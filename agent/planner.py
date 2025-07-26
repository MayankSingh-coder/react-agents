"""Planning module for the hybrid ReAct + Plan-Execute agent."""

# Import gRPC configuration first to suppress warnings
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import grpc_config

import json
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

from memory import MemoryStore, MemoryType
from config import Config
from llm_manager import get_llm_manager, safe_llm_invoke


class PlanType(Enum):
    """Types of plans the agent can create."""
    SEQUENTIAL = "sequential"      # Execute steps one after another
    PARALLEL = "parallel"         # Execute steps in parallel where possible
    CONDITIONAL = "conditional"   # Execute steps based on conditions
    ITERATIVE = "iterative"      # Repeat steps until condition is met


@dataclass
class PlanStep:
    """A single step in a plan."""
    id: str
    description: str
    tool: str
    input_template: str
    dependencies: List[str]  # IDs of steps this depends on
    conditions: Optional[Dict[str, Any]] = None  # Conditions for execution
    expected_output: Optional[str] = None
    confidence: float = 0.5
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Plan:
    """A complete execution plan."""
    id: str
    query: str
    goal: str
    plan_type: PlanType
    steps: List[PlanStep]
    estimated_duration: float
    confidence: float
    metadata: Dict[str, Any]
    created_at: float
    
    def get_executable_steps(self, completed_steps: List[str]) -> List[PlanStep]:
        """Get steps that can be executed given completed steps."""
        executable = []
        for step in self.steps:
            if step.id not in completed_steps:
                # Check if all dependencies are completed
                if all(dep in completed_steps for dep in step.dependencies):
                    executable.append(step)
        return executable
    
    def is_complete(self, completed_steps: List[str]) -> bool:
        """Check if the plan is complete."""
        return all(step.id in completed_steps for step in self.steps)


class Planner:
    """Advanced planner that creates execution plans for complex queries."""
    
    def __init__(self, memory_store: MemoryStore):
        self.memory_store = memory_store
        self.llm_manager = get_llm_manager()
        self.llm = None  # Will be set per session
    
    async def create_plan(self, query: str, available_tools: List[str], 
                         context: Optional[Dict[str, Any]] = None, session_id: str = None) -> Plan:
        """Create an execution plan for the given query."""
        
        # Get LLM instance for this session
        if self.llm is None:
            self.llm = self.llm_manager.get_llm_for_session(session_id)
        
        # Get similar successful plans from memory
        similar_plans = await self._get_similar_plans(query)
        
        # Create planning prompt
        prompt = self._create_planning_prompt(query, available_tools, similar_plans, context)
        
        # Get plan from LLM
        messages = [
            SystemMessage(content=self._get_planning_system_prompt()),
            HumanMessage(content=prompt)
        ]
        
        response = await safe_llm_invoke(self.llm, messages, session_id)
        plan_text = response.content
        
        # Parse the plan
        plan = self._parse_plan(query, plan_text, available_tools)
        
        # Store the plan in memory
        await self._store_plan(plan)
        
        return plan
    
    async def refine_plan(self, plan: Plan, execution_results: List[Dict[str, Any]], 
                         current_context: Dict[str, Any]) -> Plan:
        """Refine a plan based on execution results."""
        
        # Analyze what went wrong or what can be improved
        refinement_prompt = self._create_refinement_prompt(plan, execution_results, current_context)
        
        messages = [
            SystemMessage(content=self._get_refinement_system_prompt()),
            HumanMessage(content=refinement_prompt)
        ]
        
        async with grpc_config.safe_llm_call():
            response = await self.llm.ainvoke(messages)
        refinement_text = response.content
        
        # Parse refinements and update plan
        refined_plan = self._apply_refinements(plan, refinement_text)
        
        # Store the refined plan
        await self._store_plan(refined_plan)
        
        return refined_plan
    
    async def _get_similar_plans(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get similar successful plans from memory."""
        similar_memories = await self.memory_store.search_memories(
            query=query,
            memory_type=MemoryType.PLAN_MEMORY,
            limit=limit
        )
        
        successful_plans = []
        for memory in similar_memories:
            if memory.metadata.get("success", False):
                successful_plans.append(memory.content)
        
        return successful_plans
    
    def _create_planning_prompt(self, query: str, available_tools: List[str], 
                               similar_plans: List[Dict[str, Any]], 
                               context: Optional[Dict[str, Any]]) -> str:
        """Create the planning prompt."""
        
        tools_description = "\n".join([f"- {tool}" for tool in available_tools])
        
        similar_plans_text = ""
        if similar_plans:
            similar_plans_text = "\n\nSimilar successful plans from past:\n"
            for i, plan in enumerate(similar_plans, 1):
                similar_plans_text += f"\nPlan {i}:\n"
                similar_plans_text += f"Query: {plan.get('query', 'N/A')}\n"
                similar_plans_text += f"Steps: {json.dumps(plan.get('steps', []), indent=2)}\n"
        
        context_text = ""
        if context:
            context_text = f"\n\nCurrent context:\n{json.dumps(context, indent=2)}"
        
        return f"""Create a detailed execution plan for the following query:

Query: {query}

Available tools:
{tools_description}
{similar_plans_text}
{context_text}

Please create a plan with the following structure:
1. Goal: Clear statement of what we want to achieve
2. Plan Type: sequential, parallel, conditional, or iterative
3. Steps: List of steps with:
   - ID: unique identifier
   - Description: what this step does
   - Tool: which tool to use
   - Input Template: template for tool input (use {{variable}} for dynamic values)
   - Dependencies: list of step IDs this depends on
   - Expected Output: what we expect to get from this step
   - Confidence: how confident you are this step will work (0.0-1.0)

Format your response as JSON with this structure:
{{
    "goal": "...",
    "plan_type": "sequential|parallel|conditional|iterative",
    "estimated_duration": 30.0,
    "confidence": 0.8,
    "steps": [
        {{
            "id": "step_1",
            "description": "...",
            "tool": "tool_name",
            "input_template": "...",
            "dependencies": [],
            "expected_output": "...",
            "confidence": 0.9
        }}
    ]
}}"""
    
    def _create_refinement_prompt(self, plan: Plan, execution_results: List[Dict[str, Any]], 
                                 current_context: Dict[str, Any]) -> str:
        """Create prompt for plan refinement."""
        
        results_summary = []
        for result in execution_results:
            step_id = result.get("step_id", "unknown")
            success = result.get("success", False)
            error = result.get("error", "")
            results_summary.append(f"Step {step_id}: {'SUCCESS' if success else 'FAILED'} - {error}")
        
        return f"""Analyze the execution results and refine the plan:

Original Plan:
Goal: {plan.goal}
Plan Type: {plan.plan_type.value}
Steps: {json.dumps([step.__dict__ for step in plan.steps], indent=2)}

Execution Results:
{chr(10).join(results_summary)}

Current Context:
{json.dumps(current_context, indent=2)}

Please provide refinements in JSON format:
{{
    "add_steps": [
        {{
            "id": "new_step_1",
            "description": "...",
            "tool": "tool_name",
            "input_template": "...",
            "dependencies": ["step_1"],
            "expected_output": "...",
            "confidence": 0.8
        }}
    ],
    "modify_steps": [
        {{
            "id": "existing_step_id",
            "changes": {{
                "input_template": "new template",
                "dependencies": ["new_deps"]
            }}
        }}
    ],
    "remove_steps": ["step_id_to_remove"],
    "change_plan_type": "sequential|parallel|conditional|iterative"
}}"""
    
    def _parse_plan(self, query: str, plan_text: str, available_tools: List[str]) -> Plan:
        """Parse the LLM response into a Plan object."""
        try:
            # Extract JSON from the response
            json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in plan response")
            
            plan_data = json.loads(json_match.group())
            
            # Create plan steps
            steps = []
            for step_data in plan_data.get("steps", []):
                step = PlanStep(
                    id=step_data.get("id", f"step_{len(steps) + 1}"),
                    description=step_data.get("description", ""),
                    tool=step_data.get("tool", ""),
                    input_template=step_data.get("input_template", ""),
                    dependencies=step_data.get("dependencies", []),
                    expected_output=step_data.get("expected_output"),
                    confidence=step_data.get("confidence", 0.5)
                )
                steps.append(step)
            
            # Create plan
            plan = Plan(
                id=f"plan_{int(time.time())}",
                query=query,
                goal=plan_data.get("goal", ""),
                plan_type=PlanType(plan_data.get("plan_type", "sequential")),
                steps=steps,
                estimated_duration=plan_data.get("estimated_duration", 60.0),
                confidence=plan_data.get("confidence", 0.5),
                metadata={},
                created_at=time.time()
            )
            
            return plan
            
        except Exception as e:
            # Fallback: create a simple sequential plan
            return self._create_fallback_plan(query, available_tools)
    
    def _create_fallback_plan(self, query: str, available_tools: List[str]) -> Plan:
        """Create a simple fallback plan when parsing fails."""
        import time
        
        # Simple heuristic: if query mentions calculation, use calculator
        # if it mentions search/find, use search tools, etc.
        steps = []
        
        if any(word in query.lower() for word in ["calculate", "compute", "math"]):
            if "calculator" in available_tools:
                steps.append(PlanStep(
                    id="calc_step",
                    description="Perform calculation",
                    tool="calculator",
                    input_template=query,
                    dependencies=[],
                    confidence=0.7
                ))
        
        if any(word in query.lower() for word in ["search", "find", "look up", "what is"]):
            if "wikipedia" in available_tools:
                steps.append(PlanStep(
                    id="wiki_step",
                    description="Search for information",
                    tool="wikipedia",
                    input_template=query,
                    dependencies=[],
                    confidence=0.6
                ))
        
        # If no specific steps identified, use the first available tool
        if not steps and available_tools:
            steps.append(PlanStep(
                id="general_step",
                description="Process query",
                tool=available_tools[0],
                input_template=query,
                dependencies=[],
                confidence=0.4
            ))
        
        return Plan(
            id=f"fallback_plan_{int(time.time())}",
            query=query,
            goal="Process the user query",
            plan_type=PlanType.SEQUENTIAL,
            steps=steps,
            estimated_duration=30.0,
            confidence=0.4,
            metadata={"fallback": True},
            created_at=time.time()
        )
    
    def _apply_refinements(self, plan: Plan, refinement_text: str) -> Plan:
        """Apply refinements to a plan."""
        try:
            json_match = re.search(r'\{.*\}', refinement_text, re.DOTALL)
            if not json_match:
                return plan  # Return original if no refinements found
            
            refinements = json.loads(json_match.group())
            
            # Create a copy of the plan
            import copy
            refined_plan = copy.deepcopy(plan)
            refined_plan.id = f"refined_{plan.id}_{int(time.time())}"
            
            # Apply refinements
            # Add new steps
            for step_data in refinements.get("add_steps", []):
                new_step = PlanStep(
                    id=step_data.get("id"),
                    description=step_data.get("description", ""),
                    tool=step_data.get("tool", ""),
                    input_template=step_data.get("input_template", ""),
                    dependencies=step_data.get("dependencies", []),
                    expected_output=step_data.get("expected_output"),
                    confidence=step_data.get("confidence", 0.5)
                )
                refined_plan.steps.append(new_step)
            
            # Modify existing steps
            for modification in refinements.get("modify_steps", []):
                step_id = modification.get("id")
                changes = modification.get("changes", {})
                
                for step in refined_plan.steps:
                    if step.id == step_id:
                        for key, value in changes.items():
                            if hasattr(step, key):
                                setattr(step, key, value)
            
            # Remove steps
            for step_id in refinements.get("remove_steps", []):
                refined_plan.steps = [s for s in refined_plan.steps if s.id != step_id]
            
            # Change plan type if specified
            if "change_plan_type" in refinements:
                refined_plan.plan_type = PlanType(refinements["change_plan_type"])
            
            return refined_plan
            
        except Exception:
            return plan  # Return original if refinement fails
    
    async def _store_plan(self, plan: Plan):
        """Store a plan in memory."""
        await self.memory_store.remember(
            content={
                "id": plan.id,
                "query": plan.query,
                "goal": plan.goal,
                "plan_type": plan.plan_type.value,
                "steps": [step.__dict__ for step in plan.steps],
                "confidence": plan.confidence
            },
            memory_type=MemoryType.PLAN_MEMORY,
            importance=plan.confidence,
            metadata={
                "plan_id": plan.id,
                "estimated_duration": plan.estimated_duration,
                "step_count": len(plan.steps)
            }
        )
    
    def _get_planning_system_prompt(self) -> str:
        """Get the system prompt for planning."""
        return """You are an expert AI planner. Your job is to create detailed, executable plans for complex queries.

Key principles:
1. Break down complex tasks into manageable steps
2. Identify dependencies between steps
3. Choose appropriate tools for each step
4. Provide clear input templates with variable placeholders
5. Estimate confidence levels realistically
6. Consider parallel execution where possible

Plan types:
- Sequential: Steps must be done in order
- Parallel: Some steps can be done simultaneously  
- Conditional: Steps depend on results of previous steps
- Iterative: Steps may need to be repeated

Always respond with valid JSON in the specified format."""
    
    def _get_refinement_system_prompt(self) -> str:
        """Get the system prompt for plan refinement."""
        return """You are an expert at analyzing execution results and refining plans.

Analyze what went wrong and suggest improvements:
1. Add steps to handle missing functionality
2. Modify steps that failed or produced poor results
3. Remove unnecessary or problematic steps
4. Change plan type if a different approach would work better

Focus on practical improvements that address the specific failures observed.
Always respond with valid JSON in the specified format."""

import time