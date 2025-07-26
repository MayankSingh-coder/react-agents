"""React Agent implementation using LangGraph and LangChain with Gemini."""

# Import gRPC configuration first to suppress warnings
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import grpc_config

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .agent_state import AgentState, AgentMemory, ThoughtActionObservation, create_initial_state
from .tool_manager import ToolManager
from .planner import Planner, Plan, PlanType
from .executor import PlanExecutor, ExecutionStatus
from .adaptive_replanner import AdaptiveReplanner, AdaptationContext, ReplanDecision
from memory import MemoryStore, ContextManager, VectorMemory, EpisodicMemory
from memory.memory_store import MemoryType
from memory.context_manager import ReasoningStep, ToolContext
from memory.episodic_memory import Episode
from config import Config
from llm_manager import get_llm_manager, safe_llm_invoke
import uuid
import time


class ReactAgent:
    """React Agent that implements the Thought-Action-Observation pattern."""
    
    def __init__(self, verbose: bool = True, mode: str = "hybrid"):
        self.verbose = verbose
        self.mode = mode  # "react", "plan_execute", or "hybrid"
        self.tool_manager = ToolManager()
        
        # Initialize enhanced memory system
        self.memory_store = MemoryStore()
        self.vector_memory = VectorMemory()
        self.episodic_memory = EpisodicMemory(self.memory_store, self.vector_memory)
        self.context_manager = ContextManager(self.memory_store)
        
        # Initialize planner and executor for plan-execute mode
        self.planner = Planner(self.memory_store)
        self.executor = PlanExecutor(self.tool_manager, self.context_manager)
        
        # Initialize adaptive replanner for enhanced hybrid approach
        self.adaptive_replanner = AdaptiveReplanner(self.planner, self.tool_manager, self.context_manager)
        
        # Legacy memory for backward compatibility
        self.memory = AgentMemory()
        
        # Initialize LLM manager
        self.llm_manager = get_llm_manager()
        self.llm = None  # Will be set per session
        
        # Create the graph
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph state graph for the React Agent."""
        # Create workflow
        workflow = StateGraph(AgentState)
        
        # Add nodes based on mode
        if self.mode == "plan_execute":
            workflow.add_node("plan", self._plan_node)
            workflow.add_node("execute", self._execute_node)
            workflow.add_node("finish", self._finish_node)
            
            workflow.set_entry_point("plan")
            workflow.add_edge("plan", "execute")
            workflow.add_edge("execute", "finish")
            workflow.add_edge("finish", END)
            
        elif self.mode == "hybrid":
            # Enhanced hybrid approach with adaptive replanning
            workflow.add_node("decide_approach", self._decide_approach_node)
            workflow.add_node("plan", self._plan_node)
            workflow.add_node("execute", self._execute_node)
            workflow.add_node("evaluate_execution", self._evaluate_execution_node)  # New evaluation node
            workflow.add_node("adaptive_replan", self._adaptive_replan_node)      # New replanning node
            workflow.add_node("think", self._think_node)
            workflow.add_node("act", self._act_node)
            workflow.add_node("observe", self._observe_node)
            workflow.add_node("finish", self._finish_node)
            
            workflow.set_entry_point("decide_approach")
            
            workflow.add_conditional_edges(
                "decide_approach",
                self._route_after_decision,
                {
                    "plan": "plan",
                    "think": "think"
                }
            )
            
            # Enhanced Plan-Execute path with adaptive replanning
            workflow.add_edge("plan", "execute")
            workflow.add_edge("execute", "evaluate_execution")  # Always evaluate after execution
            workflow.add_conditional_edges(
                "evaluate_execution",
                self._should_replan_after_evaluation,
                {
                    "adaptive_replan": "adaptive_replan",  # Replan if needed
                    "think": "think",                      # Fall back to ReAct if plan completed but unsatisfactory
                    "finish": "finish"                     # Finish if successful
                }
            )
            
            # Adaptive replanning path
            workflow.add_conditional_edges(
                "adaptive_replan",
                self._route_after_replan,
                {
                    "plan": "plan",      # Execute new plan
                    "think": "think",    # Switch to ReAct approach
                    "finish": "finish"   # Give up if replanning fails
                }
            )
            
            # ReAct path
            workflow.add_conditional_edges(
                "think",
                self._should_continue_after_think,
                {
                    "act": "act",
                    "finish": "finish"
                }
            )
            
            workflow.add_edge("act", "observe")
            workflow.add_edge("observe", "think")
            workflow.add_edge("finish", END)
            
        else:  # Default ReAct mode
            workflow.add_node("think", self._think_node)
            workflow.add_node("act", self._act_node)
            workflow.add_node("observe", self._observe_node)
            workflow.add_node("finish", self._finish_node)
            
            workflow.set_entry_point("think")
            
            workflow.add_conditional_edges(
                "think",
                self._should_continue_after_think,
                {
                    "act": "act",
                    "finish": "finish"
                }
            )
            
            workflow.add_edge("act", "observe")
            workflow.add_edge("observe", "think")
            workflow.add_edge("finish", END)
        
        # Compile with memory
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    async def run(self, query: str, max_steps: int = None) -> Dict[str, Any]:
        """Run the React Agent on a query."""
        if max_steps is None:
            max_steps = Config.MAX_ITERATIONS
        
        # Start session in context manager
        session_id = str(uuid.uuid4())
        self.context_manager.start_session(session_id, query)
        
        # Get LLM instance for this session
        self.llm = self.llm_manager.get_llm_for_session(session_id)
        
        # Create initial state
        initial_state = create_initial_state(query, max_steps)
        initial_state["session_id"] = session_id
        initial_state["mode"] = self.mode
        
        # Run the graph
        config = {"configurable": {"thread_id": f"react_agent_{session_id}"}}
        
        try:
            start_time = time.time()
            final_state = await self.graph.ainvoke(initial_state, config)
            execution_time = time.time() - start_time
            
            # Debug: Print final_state type and content
            if self.verbose:
                print(f"Debug: final_state type: {type(final_state)}")
                print(f"Debug: final_state content: {final_state}")
            
            # Create response
            response = {
                "input": query,
                "output": final_state.get("output", "No output generated") if isinstance(final_state, dict) else "No output generated",
                "steps": self._format_steps(final_state),
                "success": not final_state.get("has_error", False) if isinstance(final_state, dict) else False,
                "error": final_state.get("error_message") if isinstance(final_state, dict) else f"Invalid state type: {type(final_state)}",
                "metadata": {
                    **(final_state.get("metadata", {}) if isinstance(final_state, dict) else {}),
                    "mode": self.mode,
                    "session_id": session_id,
                    "execution_time": execution_time
                }
            }
            
            # Store episode in episodic memory
            if response["success"]:
                episode = Episode(
                    id=session_id,
                    query=query,
                    response=response["output"],
                    reasoning_steps=response["steps"],
                    tools_used=list(set(step.get("action", "") for step in response["steps"] if step.get("action"))),
                    success=True,
                    duration=execution_time,
                    timestamp=time.time(),
                    importance=0.7,
                    metadata=response["metadata"]
                )
                await self.episodic_memory.store_episode(episode)
            
            # End session and cleanup
            await self.context_manager.end_session()
            self.llm_manager.cleanup_session(session_id)
            
            return response
            
        except Exception as e:
            await self.context_manager.end_session()
            self.llm_manager.cleanup_session(session_id)
            return {
                "input": query,
                "output": None,
                "steps": [],
                "success": False,
                "error": f"Agent execution failed: {str(e)}",
                "metadata": {"mode": self.mode, "session_id": session_id}
            }
    
    async def _think_node(self, state: AgentState) -> AgentState:
        """Think node - generates thoughts and decides on actions."""
        if self.verbose:
            print(f"\n🤔 Step {state['current_step'] + 1}: Thinking...")
        
        try:
            # Create thinking prompt
            prompt = await self._create_thinking_prompt(state)
            
            # if self.verbose:
            #     print(f"\n🔍 SYSTEM PROMPT:")
            #     print("=" * 80)
            #     print(self._get_system_prompt())
            #     print("=" * 80)
            #     print(f"\n🔍 USER PROMPT:")
            #     print("=" * 80)
            #     print(prompt)
            #     print("=" * 80)
            
            # Get LLM response with safe context manager
            messages = [
                SystemMessage(content=self._get_system_prompt()),
                HumanMessage(content=prompt)
            ]
            
            response = await safe_llm_invoke(self.llm, messages, state.get("session_id"))
            thought_content = response.content
            
            if self.verbose:
                print(f"\n🔍 AI MODEL RESPONSE:")
                print("=" * 80)
                print(thought_content)
                print("=" * 80)
                print(f"💭 Thought: {thought_content}")
            
            # Parse the thought to extract action if present
            # Check for multiple actions (which violates ReAct pattern)
            action_matches = re.findall(r'Action:\s*(\w+)', thought_content, re.IGNORECASE)
            if len(action_matches) > 1:
                if self.verbose:
                    print(f"⚠️ Warning: LLM generated {len(action_matches)} actions, using only the first one")
            
            # Extract the first action and its input
            action_match = re.search(r'Action:\s*(\w+)', thought_content, re.IGNORECASE)
            action_input_match = re.search(r'Action Input:\s*(.+?)(?=\n(?:Action|Observation|Thought|Final Answer)|$)', thought_content, re.IGNORECASE | re.DOTALL)
            
            # Update state
            state["thoughts"].append(thought_content)
            state["current_step"] += 1
            
            # If action is specified, prepare for action
            if action_match:
                action_name = action_match.group(1).lower()
                action_input = action_input_match.group(1).strip() if action_input_match else ""
                
                if self.verbose:
                    print(f"🔍 Parsed Action: {action_name}")
                    print(f"🔍 Parsed Action Input: '{action_input}'")
                
                state["actions"].append({
                    "name": action_name,
                    "input": action_input,
                    "step": state["current_step"]
                })
            
            return state
            
        except Exception as e:
            state["has_error"] = True
            state["error_message"] = f"Thinking failed: {str(e)}"
            return state
    
    async def _act_node(self, state: AgentState) -> AgentState:
        """Act node - executes actions using tools."""
        if not state["actions"]:
            return state
        
        current_action = state["actions"][-1]
        action_name = current_action["name"]
        action_input = current_action["input"]
        
        if self.verbose:
            print(f"🔧 Action: {action_name}")
            print(f"📝 Input: {action_input}")
        
        try:
            # Execute the tool
            if self.verbose:
                print(f"\n🔧 EXECUTING TOOL: {action_name}")
                print(f"📥 Tool Input: {action_input}")
            
            result = await self.tool_manager.execute_tool(action_name, action_input)
            
            if self.verbose:
                print(f"📤 Tool Result: {result.dict()}")
            
            # Store result
            state["tool_results"].append({
                "tool": action_name,
                "input": action_input,
                "result": result.dict(),
                "step": state["current_step"]
            })
            
            # Store important results in context memory for session persistence
            await self._store_result_in_context(action_name, action_input, result, state)
            
            return state
            
        except Exception as e:
            state["has_error"] = True
            state["error_message"] = f"Action execution failed: {str(e)}"
            return state
    
    async def _observe_node(self, state: AgentState) -> AgentState:
        """Observe node - processes tool results and creates observations."""
        if not state["tool_results"]:
            return state
        
        current_result = state["tool_results"][-1]
        tool_result = current_result["result"]
        
        # Create observation based on tool result
        if tool_result["success"]:
            observation = f"Tool '{current_result['tool']}' executed successfully. Result: {json.dumps(tool_result['data'], indent=2)}"
        else:
            observation = f"Tool '{current_result['tool']}' failed. Error: {tool_result['error']}"
        
        state["observations"].append(observation)
        
        if self.verbose:
            print(f"👁️ Observation: {observation}")
        
        return state
    
    async def _finish_node(self, state: AgentState) -> AgentState:
        """Finish node - generates final output."""
        if self.verbose:
            print(f"\n✅ Finishing...")
        
        try:
            # Check if output was already set in the thinking phase
            if state.get("output") and state.get("is_complete"):
                if self.verbose:
                    print(f"🎯 Final Answer: {state['output']}")
                return state
            
            # Create final answer prompt
            prompt = self._create_final_answer_prompt(state)
            
            messages = [
                SystemMessage(content=self._get_system_prompt()),
                HumanMessage(content=prompt)
            ]
            
            response = await safe_llm_invoke(self.llm, messages, state.get("session_id"))
            final_answer = response.content
            
            # Extract final answer if it follows the format
            answer_match = re.search(r'Final Answer:\s*(.+)', final_answer, re.IGNORECASE | re.DOTALL)
            if answer_match:
                final_answer = answer_match.group(1).strip()
            
            state["output"] = final_answer
            state["is_complete"] = True
            
            if self.verbose:
                print(f"🎯 Final Answer: {final_answer}")
            
            return state
            
        except Exception as e:
            state["has_error"] = True
            state["error_message"] = f"Final answer generation failed: {str(e)}"
            return state
    
    def _should_continue_after_think(self, state: AgentState) -> str:
        """Decide whether to continue with action or finish."""
        # Check if we've reached max steps
        if state["current_step"] >= state["max_steps"]:
            return "finish"
        
        # Check if there's an error
        if state["has_error"]:
            return "finish"
        
        # Check if the last thought indicates we should finish
        if state["thoughts"]:
            last_thought = state["thoughts"][-1]
            # Check for Final Answer pattern
            if re.search(r'Final Answer:', last_thought, re.IGNORECASE):
                # Extract the final answer and set it as output
                final_answer_match = re.search(r'Final Answer:\s*(.+)', last_thought, re.IGNORECASE | re.DOTALL)
                if final_answer_match:
                    state["output"] = final_answer_match.group(1).strip()
                    state["is_complete"] = True
                return "finish"
            
            # Check for other completion indicators
            last_thought_lower = last_thought.lower()
            if "i now know" in last_thought_lower and "final answer" in last_thought_lower:
                return "finish"
        
        # Check if there's an action to execute
        if state["actions"] and len(state["actions"]) > len(state["observations"]):
            return "act"
        
        # Default to finish if no clear action
        return "finish"
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the React Agent."""
        tools_description = self.tool_manager.format_tools_for_prompt()
        
        return f"""You are a helpful AI assistant that uses the ReAct (Reasoning and Acting) framework to solve problems.

You have access to the following tools:
{tools_description}

MEMORY CAPABILITIES:
- You have access to context from your current session, including previous calculations and tool results
- You can access similar past interactions from your episodic memory
- When users refer to "the number I just calculated" or similar references, check your memory context first
- Your memory context will be provided in the prompt when relevant

IMPORTANT: Follow the ReAct pattern strictly. In each response, provide ONLY ONE of the following:

1. A Thought (reasoning about what to do next)
2. An Action with Action Input (if you need to use a tool)
3. A Final Answer (when you're ready to conclude)

Use this exact format:

Thought: [Your reasoning about what to do next]

OR

Action: [tool_name]
Action Input: [complete_input_for_tool]

OR

Final Answer: [Your final response to the user]

Available tools: {', '.join(self.tool_manager.get_tool_names())}

Tool usage examples:
- Calculator: Action Input: 2 + 3 * 4
- Database: Action Input: set calculation_result 42
- Database: Action Input: get calculation_result
- Web Search: Action Input: information about number 42
- Wikipedia: Action Input: number 42

Critical rules:
1. Provide ONLY ONE thought, action, or final answer per response
2. Do NOT include observations in your response - they will be provided automatically
3. Do NOT simulate the entire conversation - just provide the next step
4. For database operations, always include the complete command (e.g., "set key value", not just "set")
5. Think step by step and use tools when you need external information
6. When you have enough information, provide a Final Answer
7. ALWAYS check your memory context first when users refer to previous results or calculations
8. Use your memory to avoid repeating calculations or searches you've already done

Begin!"""
    
    async def _store_result_in_context(self, action_name: str, action_input: str, result: Any, state: AgentState):
        """Store important tool results in context memory for session persistence."""
        try:
            if result.success:
                # Store calculator results
                if action_name == "calculator" and result.data:
                    calculation_result = result.data.get("result")
                    expression = result.data.get("expression")
                    if calculation_result is not None:
                        self.context_manager.set_shared_variable(
                            "last_calculation_result", 
                            calculation_result, 
                            source_tool="calculator"
                        )
                        self.context_manager.set_shared_variable(
                            "last_calculation_expression", 
                            expression, 
                            source_tool="calculator"
                        )
                        # Also store with a timestamped key for history
                        timestamp_key = f"calculation_{int(time.time())}"
                        self.context_manager.set_shared_variable(
                            timestamp_key, 
                            {"expression": expression, "result": calculation_result}, 
                            source_tool="calculator"
                        )
                
                # Store database results that might be important
                elif action_name == "database" and result.data:
                    if "get" in action_input.lower():
                        # Store retrieved data
                        key_match = re.search(r'get\s+(\w+)', action_input.lower())
                        if key_match:
                            key = key_match.group(1)
                            self.context_manager.set_shared_variable(
                                f"db_retrieved_{key}", 
                                result.data, 
                                source_tool="database"
                            )
                    elif "set" in action_input.lower():
                        # Store confirmation of data storage
                        self.context_manager.set_shared_variable(
                            "last_db_operation", 
                            {"operation": "set", "input": action_input, "result": result.data}, 
                            source_tool="database"
                        )
                
                # Store web search results summary
                elif action_name in ["web_search", "wikipedia"] and result.data:
                    search_summary = str(result.data)[:200] + "..." if len(str(result.data)) > 200 else str(result.data)
                    self.context_manager.set_shared_variable(
                        f"last_{action_name}_result", 
                        search_summary, 
                        source_tool=action_name
                    )
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Warning: Failed to store result in context: {str(e)}")

    async def _create_thinking_prompt(self, state: AgentState) -> str:
        """Create prompt for the thinking phase."""
        prompt_parts = [f"Question: {state['input']}"]
        
        # Add relevant memory context
        memory_context = await self._get_relevant_memory_context(state)
        if memory_context:
            prompt_parts.append(f"\nRelevant Context from Memory:\n{memory_context}")
        
        # Add conversation history - include all completed thought-action-observation cycles
        for i in range(len(state["thoughts"])):
            thought = state["thoughts"][i]
            action = state["actions"][i] if i < len(state["actions"]) else None
            observation = state["observations"][i] if i < len(state["observations"]) else None
            
            # Only include completed cycles (thought + action + observation)
            if action and observation:
                prompt_parts.append(f"Thought: {thought}")
                prompt_parts.append(f"Action: {action['name']}")
                prompt_parts.append(f"Action Input: {action['input']}")
                prompt_parts.append(f"Observation: {observation}")
        
        prompt_parts.append("Thought:")
        return "\n".join(prompt_parts)
    
    async def _get_relevant_memory_context(self, state: AgentState) -> str:
        """Get relevant memory context for the current query."""
        context_parts = []
        
        try:
            # Get shared variables from current session
            shared_vars = self.context_manager.get_all_shared_variables()
            if self.verbose:
                print(f"🔍 Debug: Shared variables: {shared_vars}")
            
            if shared_vars:
                relevant_vars = {}
                query_lower = state['input'].lower()
                
                # Include calculation results if query mentions calculations, numbers, or "just calculated"
                if any(keyword in query_lower for keyword in ['calculate', 'number', 'result', 'just calculated', 'computed', 'math']):
                    for key, value in shared_vars.items():
                        if isinstance(key, str) and ('calculation' in key or key in ['last_calculation_result', 'last_calculation_expression']):
                            relevant_vars[key] = value
                
                # Include database results if query mentions data or specific keys
                if any(keyword in query_lower for keyword in ['data', 'database', 'stored', 'saved', 'retrieved']):
                    for key, value in shared_vars.items():
                        if isinstance(key, str) and ('db_' in key or 'database' in key):
                            relevant_vars[key] = value
                
                # Include search results if query mentions search or information
                if any(keyword in query_lower for keyword in ['search', 'information', 'about', 'find']):
                    for key, value in shared_vars.items():
                        if isinstance(key, str) and ('search' in key or 'wikipedia' in key):
                            relevant_vars[key] = value
                
                if relevant_vars:
                    context_parts.append("Current Session Context:")
                    for key, value in relevant_vars.items():
                        context_parts.append(f"  {key}: {value}")
            
            # Search episodic memory for similar past interactions
            if hasattr(self, 'episodic_memory'):
                try:
                    similar_episodes = await self.episodic_memory.find_similar_episodes(state['input'], top_k=3)
                    if similar_episodes:
                        context_parts.append("\nSimilar Past Interactions:")
                        for episode, similarity in similar_episodes:
                            if similarity > 0.3:  # Only include reasonably similar episodes
                                context_parts.append(f"  Query: {episode.query}")
                                context_parts.append(f"  Response: {episode.response}")
                                context_parts.append(f"  Tools used: {', '.join(episode.tools_used)}")
                                context_parts.append(f"  Similarity: {similarity:.2f}")
                                context_parts.append("")
                except Exception as ep_error:
                    if self.verbose:
                        print(f"⚠️ Warning: Failed to get episodic memory: {str(ep_error)}")
            
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Warning: Failed to get memory context: {str(e)}")
                import traceback
                traceback.print_exc()
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _create_final_answer_prompt(self, state: AgentState) -> str:
        """Create prompt for generating the final answer."""
        prompt_parts = [f"Question: {state['input']}"]
        
        # Add full conversation history
        for i, (thought, action, observation) in enumerate(zip(
            state["thoughts"], 
            state["actions"] + [None] * len(state["thoughts"]), 
            state["observations"] + [None] * len(state["thoughts"])
        )):
            prompt_parts.append(f"Thought: {thought}")
            if action:
                prompt_parts.append(f"Action: {action['name']}")
                prompt_parts.append(f"Action Input: {action['input']}")
            if observation:
                prompt_parts.append(f"Observation: {observation}")
        
        prompt_parts.append("Based on the above reasoning, provide your final answer:")
        prompt_parts.append("Final Answer:")
        
        return "\n".join(prompt_parts)
    
    def _format_steps(self, state: AgentState) -> List[Dict[str, Any]]:
        """Format the reasoning steps for output."""
        steps = []
        
        # Handle case where state might not be a proper dictionary
        if not isinstance(state, dict):
            print(f"Warning: Expected dict for state, got {type(state)}: {state}")
            return []
        
        # Safely get the required fields with defaults
        thoughts = state.get("thoughts", [])
        actions = state.get("actions", [])
        observations = state.get("observations", [])
        
        for i, thought in enumerate(thoughts):
            step = {
                "step": i + 1,
                "thought": thought,
                "action": None,
                "action_input": None,
                "observation": None
            }
            
            if i < len(actions):
                action = actions[i]
                if isinstance(action, dict):
                    step["action"] = action.get("name")
                    step["action_input"] = action.get("input")
                else:
                    step["action"] = str(action)
            
            if i < len(observations):
                step["observation"] = observations[i]
            
            steps.append(step)
        
        return steps
    
    def _create_tao_steps(self, state: AgentState) -> List[ThoughtActionObservation]:
        """Create ThoughtActionObservation objects from state."""
        steps = []
        
        for i, thought in enumerate(state["thoughts"]):
            action = state["actions"][i]["name"] if i < len(state["actions"]) else None
            action_input = state["actions"][i]["input"] if i < len(state["actions"]) else None
            observation = state["observations"][i] if i < len(state["observations"]) else None
            
            steps.append(ThoughtActionObservation(
                thought=thought,
                action=action,
                action_input=action_input,
                observation=observation,
                step=i + 1
            ))
        
        return steps
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory and usage statistics."""
        return {
            "conversation_count": len(self.memory.conversation_history),
            "tool_usage": self.memory.get_tool_stats(),
            "available_tools": self.tool_manager.get_tool_names(),
            "episodic_memory_stats": await self.episodic_memory.get_episode_stats() if hasattr(self, 'episodic_memory') else {},
            "execution_stats": self.executor.get_execution_stats() if hasattr(self, 'executor') else {}
        }
    
    # New nodes for hybrid approach
    
    async def _decide_approach_node(self, state: AgentState) -> AgentState:
        """Decide whether to use ReAct or Plan-Execute approach."""
        if self.verbose:
            print(f"\n🤔 Deciding approach for: {state['input']}")
        
        try:
            # Get similar episodes to inform decision
            similar_episodes = await self.episodic_memory.find_similar_episodes(state['input'], top_k=3)
            
            # Create decision prompt
            decision_prompt = self._create_decision_prompt(state, similar_episodes)
            
            messages = [
                SystemMessage(content=self._get_decision_system_prompt()),
                HumanMessage(content=decision_prompt)
            ]
            
            response = await safe_llm_invoke(self.llm, messages, state.get("session_id"))
            decision_text = response.content.lower()
            
            # Parse decision
            if "plan" in decision_text and "execute" in decision_text:
                state["chosen_approach"] = "plan_execute"
                if self.verbose:
                    print("📋 Chosen approach: Plan-Execute")
            else:
                state["chosen_approach"] = "react"
                if self.verbose:
                    print("🔄 Chosen approach: ReAct")
            
            return state
            
        except Exception as e:
            # Default to ReAct on error
            state["chosen_approach"] = "react"
            if self.verbose:
                print(f"⚠️ Decision failed, defaulting to ReAct: {str(e)}")
            return state
    
    async def _plan_node(self, state: AgentState) -> AgentState:
        """Plan node - creates execution plan."""
        if self.verbose:
            print(f"\n📋 Planning for: {state['input']}")
        
        try:
            # Get context for planning
            context = await self.context_manager.get_relevant_context("planner", state['input'])
            
            # Create plan
            plan = await self.planner.create_plan(
                query=state['input'],
                available_tools=self.tool_manager.get_tool_names(),
                context=context
            )
            
            state["plan"] = plan
            state["metadata"]["plan_id"] = plan.id
            state["metadata"]["plan_confidence"] = plan.confidence
            
            if self.verbose:
                print(f"📝 Created plan with {len(plan.steps)} steps (confidence: {plan.confidence:.2f})")
            
            return state
            
        except Exception as e:
            state["has_error"] = True
            state["error_message"] = f"Planning failed: {str(e)}"
            return state
    
    async def _execute_node(self, state: AgentState) -> AgentState:
        """Execute node - executes the plan."""
        if self.verbose:
            print(f"\n⚡ Executing plan...")
        
        try:
            plan = state.get("plan")
            if not plan:
                state["has_error"] = True
                state["error_message"] = "No plan available for execution"
                return state
            
            # Execute the plan
            execution_result = await self.executor.execute_plan(plan)
            
            state["execution_result"] = execution_result
            state["metadata"]["execution_success_rate"] = execution_result.success_rate
            state["metadata"]["execution_time"] = execution_result.total_time
            
            # Update state based on execution result
            if execution_result.status == ExecutionStatus.COMPLETED:
                state["output"] = execution_result.final_output
                state["is_complete"] = True
                if self.verbose:
                    print(f"✅ Plan executed successfully (success rate: {execution_result.success_rate:.2f})")
            else:
                state["plan_failed"] = True
                if self.verbose:
                    print(f"⚠️ Plan execution failed (success rate: {execution_result.success_rate:.2f})")
            
            return state
            
        except Exception as e:
            state["has_error"] = True
            state["error_message"] = f"Execution failed: {str(e)}"
            return state
    
    # New routing methods
    
    def _route_after_decision(self, state: AgentState) -> str:
        """Route after approach decision."""
        chosen_approach = state.get("chosen_approach", "react")
        if chosen_approach == "plan_execute":
            return "plan"
        else:
            return "think"
    
    def _should_continue_after_execute(self, state: AgentState) -> str:
        """Decide what to do after plan execution."""
        # If execution was successful, finish
        if state.get("is_complete", False):
            return "finish"
        
        # If plan failed and we haven't exceeded max steps, fall back to ReAct
        if state.get("plan_failed", False) and state["current_step"] < state["max_steps"]:
            return "think"
        
        # Otherwise finish
        return "finish"
    
    # Helper methods for new functionality
    
    def _create_decision_prompt(self, state: AgentState, similar_episodes: List[Tuple]) -> str:
        """Create prompt for approach decision."""
        query = state['input']
        
        # Analyze query complexity
        complexity_indicators = [
            "multiple steps", "first", "then", "after that", "calculate and",
            "search and", "find and", "compare", "analyze", "complex"
        ]
        
        has_complexity = any(indicator in query.lower() for indicator in complexity_indicators)
        
        similar_episodes_text = ""
        if similar_episodes:
            similar_episodes_text = "\nSimilar past episodes:\n"
            for episode, similarity in similar_episodes[:3]:
                approach = "Plan-Execute" if len(episode.tools_used) > 2 else "ReAct"
                similar_episodes_text += f"- Query: '{episode.query}' | Approach: {approach} | Success: {episode.success} | Tools: {len(episode.tools_used)}\n"
        
        return f"""Analyze this query and decide the best approach:

Query: "{query}"

Query Analysis:
- Appears complex (multiple steps): {has_complexity}
- Word count: {len(query.split())}
{similar_episodes_text}

Available approaches:
1. **ReAct**: Good for simple queries, exploratory tasks, when you need to adapt based on intermediate results
2. **Plan-Execute**: Good for complex multi-step tasks, when you can plan ahead, structured workflows

Choose the best approach and explain why. Respond with either "ReAct" or "Plan-Execute" followed by your reasoning."""
    
    def _get_decision_system_prompt(self) -> str:
        """Get system prompt for approach decision."""
        return """You are an expert at choosing the best problem-solving approach for AI agents.

Guidelines for choosing approaches:

**Choose ReAct when:**
- Query is simple or exploratory
- You need to adapt based on intermediate results
- The path forward is unclear
- Query involves discovery or research

**Choose Plan-Execute when:**
- Query has clear multiple steps
- You can plan the entire workflow upfront
- Query involves structured data processing
- Efficiency is important (parallel execution possible)

Always explain your reasoning briefly."""
    
    async def _evaluate_execution_node(self, state: AgentState) -> AgentState:
        """Evaluate execution results and decide if replanning is needed."""
        if self.verbose:
            print(f"\n🔍 Evaluating execution results...")
        
        try:
            # Get current plan and execution results
            current_plan = state.get("current_plan")
            execution_result = state.get("execution_result")
            
            if not current_plan or not execution_result:
                # No plan or execution result, proceed to finish
                state["evaluation_result"] = "no_plan_or_result"
                return state
            
            # Create adaptation context
            adaptation_context = AdaptationContext(
                original_query=state["input"],
                current_plan=current_plan,
                execution_results=execution_result.step_results if hasattr(execution_result, 'step_results') else [],
                partial_outputs=state.get("partial_outputs", {}),
                failed_attempts=state.get("failed_attempts", []),
                available_tools=list(self.tool_manager.tools.keys()),
                time_budget_remaining=max(0, 300 - (state.get("current_step", 0) * 10)),  # Estimate remaining time
                success_probability=execution_result.success_rate if hasattr(execution_result, 'success_rate') else 0.5,
                context_variables=state.get("context_variables", {})
            )
            
            # Check if we should replan
            replan_decision = await self.adaptive_replanner.should_replan(
                adaptation_context, 
                state.get("session_id")
            )
            
            # Store evaluation results in state
            state["evaluation_result"] = "replan_needed" if replan_decision.should_replan else "continue"
            state["replan_decision"] = replan_decision
            state["adaptation_context"] = adaptation_context
            
            if self.verbose:
                print(f"📊 Evaluation: {state['evaluation_result']}")
                if replan_decision.should_replan:
                    print(f"🔄 Replanning recommended: {replan_decision.reasoning}")
                    print(f"📈 Expected improvement: {replan_decision.estimated_improvement:.2f}")
            
            return state
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Evaluation failed: {str(e)}")
            state["evaluation_result"] = "evaluation_failed"
            state["error_message"] = f"Evaluation failed: {str(e)}"
            return state
    
    async def _adaptive_replan_node(self, state: AgentState) -> AgentState:
        """Execute adaptive replanning based on evaluation."""
        if self.verbose:
            print(f"\n🔄 Executing adaptive replanning...")
        
        try:
            replan_decision = state.get("replan_decision")
            adaptation_context = state.get("adaptation_context")
            
            if not replan_decision or not adaptation_context:
                state["replan_result"] = "no_decision_or_context"
                return state
            
            # Execute the replanning
            new_plan, replan_record = await self.adaptive_replanner.execute_adaptive_replan(
                replan_decision,
                adaptation_context,
                state.get("session_id")
            )
            
            # Update state with new plan
            state["current_plan"] = new_plan
            state["replan_result"] = "success"
            state["replan_record"] = replan_record
            
            # Reset execution state for new plan attempt
            if "execution_result" in state:
                del state["execution_result"]
            
            # Track replanning attempts
            replanning_attempts = state.get("replanning_attempts", 0) + 1
            state["replanning_attempts"] = replanning_attempts
            
            if self.verbose:
                print(f"✅ Replanning successful: {replan_decision.strategy.value}")
                print(f"🎯 New plan: {new_plan.goal}")
                print(f"📝 Steps: {len(new_plan.steps)}")
                print(f"🔢 Replanning attempt: {replanning_attempts}")
            
            # Prevent infinite replanning loops
            if replanning_attempts >= 3:
                state["replan_result"] = "max_attempts_reached"
                if self.verbose:
                    print(f"⚠️ Maximum replanning attempts reached, switching to ReAct")
            
            return state
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Replanning failed: {str(e)}")
            state["replan_result"] = "failed"
            state["error_message"] = f"Replanning failed: {str(e)}"
            return state
    
    def _should_replan_after_evaluation(self, state: AgentState) -> str:
        """Determine next step after execution evaluation."""
        evaluation_result = state.get("evaluation_result", "no_result")
        execution_result = state.get("execution_result")
        
        # Check if execution was successful enough to finish
        if (evaluation_result == "continue" and execution_result and 
            hasattr(execution_result, 'success_rate') and execution_result.success_rate >= 0.7):
            return "finish"
        
        # Check if we should replan
        if evaluation_result == "replan_needed":
            return "adaptive_replan"
        
        # Fall back to ReAct if evaluation failed or plan completed but unsatisfactory
        return "think"
    
    def _route_after_replan(self, state: AgentState) -> str:
        """Route execution after replanning."""
        replan_result = state.get("replan_result", "no_result")
        replanning_attempts = state.get("replanning_attempts", 0)
        
        # If replanning failed or max attempts reached, fall back to ReAct
        if replan_result in ["failed", "max_attempts_reached", "no_decision_or_context"]:
            return "think"
        
        # If replanning was successful, try executing the new plan
        if replan_result == "success":
            replan_record = state.get("replan_record", {})
            
            # Check if the strategy suggests switching to ReAct approach
            if replan_record.get("strategy") == "switch_approach":
                return "think"
            else:
                return "plan"  # Execute the new plan
        
        # Default fallback
        return "finish"