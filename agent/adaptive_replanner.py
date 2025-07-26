"""Adaptive Replanning System for Enhanced Hybrid Agent."""

import asyncio
import time
import json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .planner import Plan, PlanStep, PlanType, Planner
from .executor import ExecutionResult, ExecutionStatus, StepResult
from .tool_manager import ToolManager
from memory.context_manager import ContextManager
from llm_manager import get_llm_manager, safe_llm_invoke
from langchain.schema import HumanMessage, SystemMessage


class ReplanTrigger(Enum):
    """Reasons why replanning was triggered."""
    EXECUTION_FAILURE = "execution_failure"
    UNEXPECTED_RESULT = "unexpected_result"
    MISSING_INFORMATION = "missing_information"
    EFFICIENCY_OPTIMIZATION = "efficiency_optimization"
    GOAL_REFINEMENT = "goal_refinement"
    CONTEXT_CHANGE = "context_change"


class AdaptationStrategy(Enum):
    """Different adaptation strategies."""
    REPLAN_COMPLETE = "replan_complete"           # Start over with new plan
    REPLAN_PARTIAL = "replan_partial"             # Modify remaining steps
    SWITCH_APPROACH = "switch_approach"           # Switch from Plan-Execute to ReAct or vice versa
    ADD_VERIFICATION = "add_verification"         # Add verification steps
    PARALLEL_EXECUTION = "parallel_execution"     # Try multiple approaches in parallel
    INCREMENTAL_SEARCH = "incremental_search"     # Break down into smaller searchable chunks


@dataclass
class ReplanDecision:
    """Decision about whether and how to replan."""
    should_replan: bool
    trigger: Optional[ReplanTrigger]
    strategy: Optional[AdaptationStrategy]
    confidence: float
    reasoning: str
    estimated_improvement: float  # Expected improvement in success probability
    cost_benefit_ratio: float    # Cost of replanning vs expected benefit


@dataclass
class AdaptationContext:
    """Context for adaptive replanning decisions."""
    original_query: str
    current_plan: Plan
    execution_results: List[StepResult]
    partial_outputs: Dict[str, Any]
    failed_attempts: List[Dict[str, Any]]
    available_tools: List[str]
    time_budget_remaining: float
    success_probability: float
    context_variables: Dict[str, Any]


class AdaptiveReplanner:
    """Intelligent replanning system that adapts strategy based on execution feedback."""
    
    def __init__(self, planner: Planner, tool_manager: ToolManager, context_manager: ContextManager):
        self.planner = planner
        self.tool_manager = tool_manager
        self.context_manager = context_manager
        self.llm_manager = get_llm_manager()
        
        # Replanning history for learning
        self.replanning_history: List[Dict[str, Any]] = []
        
        # Success patterns for optimization
        self.success_patterns: Dict[str, List[Dict[str, Any]]] = {}
        
        # Performance metrics
        self.metrics = {
            "total_replans": 0,
            "successful_replans": 0,
            "efficiency_improvements": 0,
            "avg_improvement_ratio": 0.0
        }
    
    async def should_replan(self, context: AdaptationContext, session_id: str = None) -> ReplanDecision:
        """Analyze execution context and decide if replanning is beneficial."""
        
        # Quick checks for obvious replanning triggers
        obvious_triggers = self._check_obvious_triggers(context)
        if obvious_triggers:
            return ReplanDecision(
                should_replan=True,
                trigger=obvious_triggers[0],
                strategy=self._recommend_strategy(obvious_triggers[0], context),
                confidence=0.9,
                reasoning=f"Obvious trigger detected: {obvious_triggers[0].value}",
                estimated_improvement=0.7,
                cost_benefit_ratio=3.0
            )
        
        # Advanced analysis using LLM
        return await self._analyze_with_llm(context, session_id)
    
    async def execute_adaptive_replan(self, decision: ReplanDecision, context: AdaptationContext, 
                                     session_id: str = None) -> Tuple[Plan, Dict[str, Any]]:
        """Execute the replanning decision."""
        
        start_time = time.time()
        
        try:
            if decision.strategy == AdaptationStrategy.REPLAN_COMPLETE:
                new_plan = await self._replan_complete(context, session_id)
                
            elif decision.strategy == AdaptationStrategy.REPLAN_PARTIAL:
                new_plan = await self._replan_partial(context, session_id)
                
            elif decision.strategy == AdaptationStrategy.SWITCH_APPROACH:
                new_plan = await self._switch_approach(context, session_id)
                
            elif decision.strategy == AdaptationStrategy.ADD_VERIFICATION:
                new_plan = await self._add_verification_steps(context, session_id)
                
            elif decision.strategy == AdaptationStrategy.PARALLEL_EXECUTION:
                new_plan = await self._create_parallel_plan(context, session_id)
                
            elif decision.strategy == AdaptationStrategy.INCREMENTAL_SEARCH:
                new_plan = await self._create_incremental_search_plan(context, session_id)
                
            else:
                # Fallback to partial replan
                new_plan = await self._replan_partial(context, session_id)
            
            # Record replanning attempt
            replan_record = {
                "timestamp": time.time(),
                "trigger": decision.trigger.value,
                "strategy": decision.strategy.value,
                "original_plan_id": context.current_plan.id,
                "new_plan_id": new_plan.id,
                "execution_time": time.time() - start_time,
                "confidence": decision.confidence
            }
            
            self.replanning_history.append(replan_record)
            self.metrics["total_replans"] += 1
            
            return new_plan, replan_record
            
        except Exception as e:
            # If replanning fails, return original plan with modifications
            fallback_plan = await self._create_fallback_plan(context, str(e), session_id)
            return fallback_plan, {"error": str(e), "fallback": True}
    
    def _check_obvious_triggers(self, context: AdaptationContext) -> List[ReplanTrigger]:
        """Check for obvious replanning triggers."""
        triggers = []
        
        # Check execution failures
        failed_steps = [r for r in context.execution_results if r.status == ExecutionStatus.FAILED]
        if len(failed_steps) >= 2:  # Multiple failures
            triggers.append(ReplanTrigger.EXECUTION_FAILURE)
        
        # Check for missing critical information
        if any("not found" in str(r.error).lower() or "missing" in str(r.error).lower() 
               for r in failed_steps):
            triggers.append(ReplanTrigger.MISSING_INFORMATION)
        
        # Check success probability
        if context.success_probability < 0.3:
            triggers.append(ReplanTrigger.EFFICIENCY_OPTIMIZATION)
        
        # Check if too many steps without progress
        if len(context.execution_results) > len(context.current_plan.steps) * 1.5:
            triggers.append(ReplanTrigger.EFFICIENCY_OPTIMIZATION)
        
        return triggers
    
    def _recommend_strategy(self, trigger: ReplanTrigger, context: AdaptationContext) -> AdaptationStrategy:
        """Recommend adaptation strategy based on trigger."""
        
        if trigger == ReplanTrigger.EXECUTION_FAILURE:
            # If multiple tools failed, try different approach
            if len(set(r.step_id for r in context.execution_results if r.status == ExecutionStatus.FAILED)) > 1:
                return AdaptationStrategy.SWITCH_APPROACH
            else:
                return AdaptationStrategy.REPLAN_PARTIAL
        
        elif trigger == ReplanTrigger.MISSING_INFORMATION:
            return AdaptationStrategy.INCREMENTAL_SEARCH
        
        elif trigger == ReplanTrigger.EFFICIENCY_OPTIMIZATION:
            return AdaptationStrategy.PARALLEL_EXECUTION
        
        elif trigger == ReplanTrigger.UNEXPECTED_RESULT:
            return AdaptationStrategy.ADD_VERIFICATION
        
        else:
            return AdaptationStrategy.REPLAN_PARTIAL
    
    async def _analyze_with_llm(self, context: AdaptationContext, session_id: str = None) -> ReplanDecision:
        """Use LLM to analyze if replanning would be beneficial."""
        
        # Create analysis prompt
        prompt = self._create_analysis_prompt(context)
        
        messages = [
            SystemMessage(content=self._get_analysis_system_prompt()),
            HumanMessage(content=prompt)
        ]
        
        try:
            llm = self.llm_manager.get_llm_for_session(session_id)
            response = await safe_llm_invoke(llm, messages, session_id)
            analysis_text = response.content
            
            # Parse LLM decision
            return self._parse_replan_decision(analysis_text)
            
        except Exception as e:
            # Conservative fallback: don't replan unless obvious issues
            return ReplanDecision(
                should_replan=len([r for r in context.execution_results if r.status == ExecutionStatus.FAILED]) >= 2,
                trigger=ReplanTrigger.EXECUTION_FAILURE if context.execution_results else None,
                strategy=AdaptationStrategy.REPLAN_PARTIAL,
                confidence=0.5,
                reasoning=f"LLM analysis failed: {str(e)}. Using conservative approach.",
                estimated_improvement=0.3,
                cost_benefit_ratio=1.0
            )
    
    async def _replan_complete(self, context: AdaptationContext, session_id: str = None) -> Plan:
        """Create a completely new plan from scratch."""
        
        # Analyze what went wrong with the original plan
        failure_analysis = self._analyze_failures(context.execution_results)
        
        # Create new plan with lessons learned
        enhanced_context = {
            **context.context_variables,
            "previous_failures": failure_analysis,
            "avoid_tools": [r.step_id for r in context.execution_results if r.status == ExecutionStatus.FAILED],
            "successful_partial_results": context.partial_outputs
        }
        
        return await self.planner.create_plan(
            query=context.original_query,
            available_tools=context.available_tools,
            context=enhanced_context,
            session_id=session_id
        )
    
    async def _replan_partial(self, context: AdaptationContext, session_id: str = None) -> Plan:
        """Modify the remaining steps of the current plan."""
        
        # Identify completed steps
        completed_steps = [r.step_id for r in context.execution_results if r.status == ExecutionStatus.COMPLETED]
        
        # Create refined plan using the existing planner's refine_plan method
        execution_results_dict = [
            {
                "step_id": r.step_id,
                "success": r.status == ExecutionStatus.COMPLETED,
                "error": r.error or "",
                "output": r.output
            }
            for r in context.execution_results
        ]
        
        return await self.planner.refine_plan(
            plan=context.current_plan,
            execution_results=execution_results_dict,
            current_context=context.context_variables
        )
    
    async def _switch_approach(self, context: AdaptationContext, session_id: str = None) -> Plan:
        """Switch from structured planning to reactive approach or vice versa."""
        
        # Create a simple reactive-style plan that uses tools more dynamically
        steps = []
        
        # Add a dynamic search/exploration step
        steps.append(PlanStep(
            id="dynamic_search",
            description="Dynamically search for information using available tools",
            tool="wikipedia",  # Start with search
            input_template=context.original_query,
            dependencies=[],
            confidence=0.7
        ))
        
        # Add a calculation step if query seems numerical
        if any(word in context.original_query.lower() for word in ["calculate", "compute", "number", "math"]):
            steps.append(PlanStep(
                id="dynamic_calc",
                description="Perform any necessary calculations",
                tool="calculator",
                input_template="Based on previous results, calculate: {{search_result}}",
                dependencies=["dynamic_search"],
                confidence=0.6
            ))
        
        return Plan(
            id=f"switched_plan_{int(time.time())}",
            query=context.original_query,
            goal="Dynamically solve the query using reactive approach",
            plan_type=PlanType.SEQUENTIAL,
            steps=steps,
            estimated_duration=45.0,
            confidence=0.6,
            metadata={"approach": "switched", "original_plan": context.current_plan.id},
            created_at=time.time()
        )
    
    async def _add_verification_steps(self, context: AdaptationContext, session_id: str = None) -> Plan:
        """Add verification and validation steps to increase reliability."""
        
        # Clone current plan and add verification steps
        import copy
        new_plan = copy.deepcopy(context.current_plan)
        new_plan.id = f"verified_plan_{int(time.time())}"
        
        # Add verification steps after each major step
        verification_steps = []
        for step in new_plan.steps:
            if step.tool in ["calculator", "database"]:  # Add verification for critical tools
                verify_step = PlanStep(
                    id=f"verify_{step.id}",
                    description=f"Verify the result from {step.id}",
                    tool="calculator" if step.tool == "calculator" else "database",
                    input_template=f"Verify: {{output_from_{step.id}}}",
                    dependencies=[step.id],
                    confidence=0.8
                )
                verification_steps.append(verify_step)
        
        new_plan.steps.extend(verification_steps)
        new_plan.metadata["verification_added"] = True
        
        return new_plan
    
    async def _create_parallel_plan(self, context: AdaptationContext, session_id: str = None) -> Plan:
        """Create a plan that executes multiple approaches in parallel."""
        
        steps = []
        
        # Create parallel approaches for information gathering
        steps.append(PlanStep(
            id="parallel_search_1",
            description="Search approach 1: General information",
            tool="wikipedia",
            input_template=context.original_query,
            dependencies=[],
            confidence=0.7
        ))
        
        steps.append(PlanStep(
            id="parallel_search_2", 
            description="Search approach 2: Web search",
            tool="web_search",
            input_template=context.original_query,
            dependencies=[],
            confidence=0.7
        ))
        
        # Synthesis step
        steps.append(PlanStep(
            id="synthesize_results",
            description="Combine results from parallel searches",
            tool="calculator",  # Use calculator to process/combine results
            input_template="Combine: {{parallel_search_1}} and {{parallel_search_2}}",
            dependencies=["parallel_search_1", "parallel_search_2"],
            confidence=0.8
        ))
        
        return Plan(
            id=f"parallel_plan_{int(time.time())}",
            query=context.original_query,
            goal="Solve query using parallel information gathering",
            plan_type=PlanType.PARALLEL,
            steps=steps,
            estimated_duration=30.0,
            confidence=0.8,
            metadata={"parallel_execution": True},
            created_at=time.time()
        )
    
    async def _create_incremental_search_plan(self, context: AdaptationContext, session_id: str = None) -> Plan:
        """Create a plan that breaks down the query into incremental searchable parts."""
        
        # Break down the query into smaller, searchable components
        query_parts = self._decompose_query(context.original_query)
        
        steps = []
        for i, part in enumerate(query_parts):
            steps.append(PlanStep(
                id=f"incremental_search_{i+1}",
                description=f"Search for: {part}",
                tool="wikipedia",
                input_template=part,
                dependencies=[f"incremental_search_{j+1}" for j in range(i)],  # Sequential dependencies
                confidence=0.8
            ))
        
        # Final synthesis step
        steps.append(PlanStep(
            id="synthesize_incremental",
            description="Combine all incremental search results",
            tool="calculator",
            input_template="Combine all search results to answer: " + context.original_query,
            dependencies=[f"incremental_search_{i+1}" for i in range(len(query_parts))],
            confidence=0.9
        ))
        
        return Plan(
            id=f"incremental_plan_{int(time.time())}",
            query=context.original_query,
            goal="Solve query through incremental search and synthesis",
            plan_type=PlanType.SEQUENTIAL,
            steps=steps,
            estimated_duration=60.0,
            confidence=0.8,
            metadata={"incremental_search": True, "query_parts": query_parts},
            created_at=time.time()
        )
    
    def _decompose_query(self, query: str) -> List[str]:
        """Decompose complex query into searchable parts."""
        
        # Simple heuristic decomposition (could be enhanced with NLP)
        parts = []
        
        # Split on common separators
        if " and " in query.lower():
            parts.extend(query.lower().split(" and "))
        elif ", " in query:
            parts.extend(query.split(", "))
        elif "then" in query.lower():
            parts.extend(query.lower().split("then"))
        else:
            # Try to identify key concepts
            words = query.split()
            if len(words) > 6:  # Long query, break into chunks
                chunk_size = max(3, len(words) // 3)
                for i in range(0, len(words), chunk_size):
                    parts.append(" ".join(words[i:i+chunk_size]))
            else:
                parts = [query]  # Keep as single part if short
        
        return [part.strip() for part in parts if part.strip()]
    
    def _analyze_failures(self, execution_results: List[StepResult]) -> Dict[str, Any]:
        """Analyze failure patterns in execution results."""
        
        failures = [r for r in execution_results if r.status == ExecutionStatus.FAILED]
        
        analysis = {
            "total_failures": len(failures),
            "failed_tools": list(set(f.step_id for f in failures)),
            "common_errors": {},
            "failure_patterns": []
        }
        
        # Analyze error patterns
        for failure in failures:
            error_key = str(failure.error).lower()[:50]  # First 50 chars of error
            analysis["common_errors"][error_key] = analysis["common_errors"].get(error_key, 0) + 1
        
        # Identify patterns
        if len(analysis["failed_tools"]) == 1:
            analysis["failure_patterns"].append("single_tool_repeated_failure")
        elif analysis["total_failures"] > len(execution_results) / 2:
            analysis["failure_patterns"].append("high_failure_rate")
        
        return analysis
    
    def _create_analysis_prompt(self, context: AdaptationContext) -> str:
        """Create prompt for LLM analysis of replanning decision."""
        
        results_summary = []
        for result in context.execution_results:
            status = "SUCCESS" if result.status == ExecutionStatus.COMPLETED else "FAILED"
            results_summary.append(f"Step {result.step_id}: {status} - {result.error or 'OK'}")
        
        return f"""Analyze whether replanning would improve success for this execution:

Original Query: {context.original_query}

Current Plan: {context.current_plan.goal}
Plan Type: {context.current_plan.plan_type.value}
Total Steps: {len(context.current_plan.steps)}

Execution Results So Far:
{chr(10).join(results_summary)}

Success Probability: {context.success_probability:.2f}
Time Remaining: {context.time_budget_remaining:.1f}s

Should we replan? Consider:
1. Is the current approach likely to succeed?
2. Would replanning improve success probability?
3. Is there enough time/budget for replanning?
4. What strategy would work best?

Respond in JSON format:
{{
    "should_replan": true/false,
    "trigger": "execution_failure|missing_information|efficiency_optimization|unexpected_result",
    "strategy": "replan_complete|replan_partial|switch_approach|add_verification|parallel_execution|incremental_search",
    "confidence": 0.0-1.0,
    "reasoning": "explanation",
    "estimated_improvement": 0.0-1.0,
    "cost_benefit_ratio": 1.0-10.0
}}"""
    
    def _parse_replan_decision(self, analysis_text: str) -> ReplanDecision:
        """Parse LLM analysis into ReplanDecision."""
        
        try:
            import re
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                return ReplanDecision(
                    should_replan=data.get("should_replan", False),
                    trigger=ReplanTrigger(data.get("trigger", "execution_failure")) if data.get("trigger") else None,
                    strategy=AdaptationStrategy(data.get("strategy", "replan_partial")) if data.get("strategy") else None,
                    confidence=float(data.get("confidence", 0.5)),
                    reasoning=data.get("reasoning", "LLM analysis"),
                    estimated_improvement=float(data.get("estimated_improvement", 0.3)),
                    cost_benefit_ratio=float(data.get("cost_benefit_ratio", 2.0))
                )
        except Exception:
            pass
        
        # Fallback decision
        return ReplanDecision(
            should_replan=False,
            trigger=None,
            strategy=None,  
            confidence=0.3,
            reasoning="Failed to parse LLM analysis",
            estimated_improvement=0.0,
            cost_benefit_ratio=0.5
        )
    
    def _get_analysis_system_prompt(self) -> str:
        """System prompt for replanning analysis."""
        return """You are an expert at analyzing agent execution patterns and determining when replanning would be beneficial.

Your goal is to decide whether the current execution approach should be modified, and if so, how.

Consider these factors:
- Success probability of continuing current approach
- Time and resource costs of replanning
- Likelihood that alternative approaches would succeed
- Patterns in the execution failures

Be conservative about replanning - only recommend it when there's clear evidence it would help."""
    
    async def _create_fallback_plan(self, context: AdaptationContext, error: str, session_id: str = None) -> Plan:
        """Create a simple fallback plan when replanning fails."""
        
        return Plan(
            id=f"fallback_plan_{int(time.time())}",
            query=context.original_query,
            goal="Simple fallback approach",
            plan_type=PlanType.SEQUENTIAL,
            steps=[
                PlanStep(
                    id="fallback_step",
                    description="Attempt simple approach to query",
                    tool=context.available_tools[0] if context.available_tools else "calculator",
                    input_template=context.original_query,
                    dependencies=[],
                    confidence=0.4
                )
            ],
            estimated_duration=20.0,
            confidence=0.4,
            metadata={"fallback": True, "replan_error": error},
            created_at=time.time()
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get replanning performance metrics."""
        success_rate = (self.metrics["successful_replans"] / max(1, self.metrics["total_replans"]))
        
        return {
            **self.metrics,
            "success_rate": success_rate,
            "recent_replans": self.replanning_history[-10:] if self.replanning_history else []
        }