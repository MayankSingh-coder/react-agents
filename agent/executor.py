"""Execution module for the hybrid ReAct + Plan-Execute agent."""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .planner import Plan, PlanStep
from .tool_manager import ToolManager
from memory.context_manager import ContextManager, ToolContext


class ExecutionStatus(Enum):
    """Status of plan execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    """Result of executing a single step."""
    step_id: str
    status: ExecutionStatus
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ExecutionResult:
    """Result of executing a complete plan."""
    plan_id: str
    status: ExecutionStatus
    step_results: List[StepResult]
    total_time: float
    success_rate: float
    final_output: Any
    metadata: Dict[str, Any]


class PlanExecutor:
    """Executes plans created by the Planner."""
    
    def __init__(self, tool_manager: ToolManager, context_manager: ContextManager):
        self.tool_manager = tool_manager
        self.context_manager = context_manager
        self.execution_history: List[ExecutionResult] = []
    
    async def execute_plan(self, plan: Plan, max_retries: int = 2) -> ExecutionResult:
        """Execute a complete plan."""
        start_time = time.time()
        step_results = []
        completed_steps = []
        failed_steps = []
        
        # Initialize execution context
        execution_context = {
            "plan_id": plan.id,
            "query": plan.query,
            "variables": {},
            "step_outputs": {}
        }
        
        try:
            if plan.plan_type.value == "sequential":
                step_results = await self._execute_sequential(plan, execution_context, max_retries)
            elif plan.plan_type.value == "parallel":
                step_results = await self._execute_parallel(plan, execution_context, max_retries)
            elif plan.plan_type.value == "conditional":
                step_results = await self._execute_conditional(plan, execution_context, max_retries)
            elif plan.plan_type.value == "iterative":
                step_results = await self._execute_iterative(plan, execution_context, max_retries)
            else:
                # Default to sequential
                step_results = await self._execute_sequential(plan, execution_context, max_retries)
            
            # Analyze results
            completed_steps = [r.step_id for r in step_results if r.status == ExecutionStatus.COMPLETED]
            failed_steps = [r.step_id for r in step_results if r.status == ExecutionStatus.FAILED]
            
            # Determine overall status
            if len(completed_steps) == len(plan.steps):
                overall_status = ExecutionStatus.COMPLETED
            elif len(completed_steps) > 0:
                overall_status = ExecutionStatus.RUNNING  # Partial completion
            else:
                overall_status = ExecutionStatus.FAILED
            
            # Calculate success rate
            success_rate = len(completed_steps) / len(plan.steps) if plan.steps else 0.0
            
            # Determine final output
            final_output = self._determine_final_output(step_results, execution_context)
            
        except Exception as e:
            # Handle execution failure
            overall_status = ExecutionStatus.FAILED
            success_rate = 0.0
            final_output = f"Execution failed: {str(e)}"
        
        # Create execution result
        execution_result = ExecutionResult(
            plan_id=plan.id,
            status=overall_status,
            step_results=step_results,
            total_time=time.time() - start_time,
            success_rate=success_rate,
            final_output=final_output,
            metadata={
                "completed_steps": completed_steps,
                "failed_steps": failed_steps,
                "plan_type": plan.plan_type.value
            }
        )
        
        # Store in history
        self.execution_history.append(execution_result)
        
        return execution_result
    
    async def _execute_sequential(self, plan: Plan, context: Dict[str, Any], 
                                 max_retries: int) -> List[StepResult]:
        """Execute steps sequentially."""
        results = []
        
        for step in plan.steps:
            # Check dependencies
            if not self._dependencies_satisfied(step, results):
                results.append(StepResult(
                    step_id=step.id,
                    status=ExecutionStatus.SKIPPED,
                    output=None,
                    error="Dependencies not satisfied"
                ))
                continue
            
            # Execute step
            result = await self._execute_step(step, context, max_retries)
            results.append(result)
            
            # Update context with step output
            if result.status == ExecutionStatus.COMPLETED:
                context["step_outputs"][step.id] = result.output
                context["variables"][f"step_{step.id}_output"] = result.output
            
            # Stop if critical step fails
            if result.status == ExecutionStatus.FAILED and step.confidence > 0.8:
                break
        
        return results
    
    async def _execute_parallel(self, plan: Plan, context: Dict[str, Any], 
                               max_retries: int) -> List[StepResult]:
        """Execute steps in parallel where possible."""
        results = []
        remaining_steps = plan.steps.copy()
        
        while remaining_steps:
            # Find steps that can be executed (dependencies satisfied)
            executable_steps = []
            for step in remaining_steps:
                if self._dependencies_satisfied(step, results):
                    executable_steps.append(step)
            
            if not executable_steps:
                # No more executable steps - mark remaining as skipped
                for step in remaining_steps:
                    results.append(StepResult(
                        step_id=step.id,
                        status=ExecutionStatus.SKIPPED,
                        output=None,
                        error="Dependencies not satisfied"
                    ))
                break
            
            # Execute steps in parallel
            tasks = []
            for step in executable_steps:
                task = self._execute_step(step, context.copy(), max_retries)
                tasks.append(task)
            
            # Wait for completion
            step_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(step_results):
                if isinstance(result, Exception):
                    result = StepResult(
                        step_id=executable_steps[i].id,
                        status=ExecutionStatus.FAILED,
                        output=None,
                        error=str(result)
                    )
                
                results.append(result)
                
                # Update context
                if result.status == ExecutionStatus.COMPLETED:
                    context["step_outputs"][result.step_id] = result.output
                    context["variables"][f"step_{result.step_id}_output"] = result.output
            
            # Remove executed steps
            executed_ids = {step.id for step in executable_steps}
            remaining_steps = [s for s in remaining_steps if s.id not in executed_ids]
        
        return results
    
    async def _execute_conditional(self, plan: Plan, context: Dict[str, Any], 
                                  max_retries: int) -> List[StepResult]:
        """Execute steps based on conditions."""
        results = []
        
        for step in plan.steps:
            # Check if step should be executed based on conditions
            if not self._should_execute_step(step, context, results):
                results.append(StepResult(
                    step_id=step.id,
                    status=ExecutionStatus.SKIPPED,
                    output=None,
                    error="Condition not met"
                ))
                continue
            
            # Check dependencies
            if not self._dependencies_satisfied(step, results):
                results.append(StepResult(
                    step_id=step.id,
                    status=ExecutionStatus.SKIPPED,
                    output=None,
                    error="Dependencies not satisfied"
                ))
                continue
            
            # Execute step
            result = await self._execute_step(step, context, max_retries)
            results.append(result)
            
            # Update context
            if result.status == ExecutionStatus.COMPLETED:
                context["step_outputs"][step.id] = result.output
                context["variables"][f"step_{step.id}_output"] = result.output
        
        return results
    
    async def _execute_iterative(self, plan: Plan, context: Dict[str, Any], 
                                max_retries: int, max_iterations: int = 5) -> List[StepResult]:
        """Execute steps iteratively until condition is met."""
        all_results = []
        iteration = 0
        
        while iteration < max_iterations:
            iteration_results = []
            
            for step in plan.steps:
                # Check dependencies
                if not self._dependencies_satisfied(step, iteration_results):
                    continue
                
                # Execute step
                result = await self._execute_step(step, context, max_retries)
                iteration_results.append(result)
                
                # Update context
                if result.status == ExecutionStatus.COMPLETED:
                    context["step_outputs"][f"{step.id}_iter_{iteration}"] = result.output
                    context["variables"][f"step_{step.id}_output"] = result.output
            
            all_results.extend(iteration_results)
            
            # Check if we should continue iterating
            if not self._should_continue_iteration(iteration_results, context):
                break
            
            iteration += 1
        
        return all_results
    
    async def _execute_step(self, step: PlanStep, context: Dict[str, Any], 
                           max_retries: int) -> StepResult:
        """Execute a single step."""
        start_time = time.time()
        
        for attempt in range(max_retries + 1):
            try:
                # Prepare input by substituting variables
                step_input = self._substitute_variables(step.input_template, context)
                
                # Execute tool
                tool_result = await self.tool_manager.execute_tool(step.tool, step_input)
                
                # Create tool context for memory
                tool_context = ToolContext(
                    tool_name=step.tool,
                    input_data=step_input,
                    output_data=tool_result.data if tool_result.success else None,
                    success=tool_result.success,
                    error_message=tool_result.error,
                    execution_time=time.time() - start_time
                )
                
                # Add to context manager
                await self.context_manager.add_tool_context(tool_context)
                
                if tool_result.success:
                    return StepResult(
                        step_id=step.id,
                        status=ExecutionStatus.COMPLETED,
                        output=tool_result.data,
                        execution_time=time.time() - start_time,
                        metadata={"attempts": attempt + 1}
                    )
                else:
                    if attempt == max_retries:  # Last attempt
                        return StepResult(
                            step_id=step.id,
                            status=ExecutionStatus.FAILED,
                            output=None,
                            error=tool_result.error,
                            execution_time=time.time() - start_time,
                            metadata={"attempts": attempt + 1}
                        )
                    # Wait before retry
                    await asyncio.sleep(1)
            
            except Exception as e:
                if attempt == max_retries:  # Last attempt
                    return StepResult(
                        step_id=step.id,
                        status=ExecutionStatus.FAILED,
                        output=None,
                        error=str(e),
                        execution_time=time.time() - start_time,
                        metadata={"attempts": attempt + 1}
                    )
                await asyncio.sleep(1)
        
        # Should not reach here
        return StepResult(
            step_id=step.id,
            status=ExecutionStatus.FAILED,
            output=None,
            error="Unexpected execution path",
            execution_time=time.time() - start_time
        )
    
    def _dependencies_satisfied(self, step: PlanStep, completed_results: List[StepResult]) -> bool:
        """Check if step dependencies are satisfied."""
        completed_step_ids = {r.step_id for r in completed_results if r.status == ExecutionStatus.COMPLETED}
        return all(dep in completed_step_ids for dep in step.dependencies)
    
    def _should_execute_step(self, step: PlanStep, context: Dict[str, Any], 
                           results: List[StepResult]) -> bool:
        """Check if step should be executed based on conditions."""
        if not step.conditions:
            return True
        
        # Simple condition evaluation
        for condition_key, condition_value in step.conditions.items():
            if condition_key in context["variables"]:
                if context["variables"][condition_key] != condition_value:
                    return False
        
        return True
    
    def _should_continue_iteration(self, iteration_results: List[StepResult], 
                                  context: Dict[str, Any]) -> bool:
        """Check if iteration should continue."""
        # Simple heuristic: continue if any step failed
        return any(r.status == ExecutionStatus.FAILED for r in iteration_results)
    
    def _substitute_variables(self, template: str, context: Dict[str, Any]) -> str:
        """Substitute variables in input template."""
        result = template
        
        # Substitute context variables
        for key, value in context.get("variables", {}).items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        
        # Substitute step outputs
        for step_id, output in context.get("step_outputs", {}).items():
            placeholder = f"{{step_{step_id}_output}}"
            if placeholder in result:
                result = result.replace(placeholder, str(output))
        
        return result
    
    def _determine_final_output(self, step_results: List[StepResult], 
                               context: Dict[str, Any]) -> Any:
        """Determine the final output from step results."""
        # Use the output of the last successful step
        for result in reversed(step_results):
            if result.status == ExecutionStatus.COMPLETED and result.output is not None:
                return result.output
        
        # If no successful steps, return summary
        return {
            "message": "Plan execution completed with mixed results",
            "successful_steps": len([r for r in step_results if r.status == ExecutionStatus.COMPLETED]),
            "total_steps": len(step_results)
        }
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        if not self.execution_history:
            return {"total_executions": 0}
        
        total_executions = len(self.execution_history)
        successful_executions = len([e for e in self.execution_history if e.status == ExecutionStatus.COMPLETED])
        avg_success_rate = sum(e.success_rate for e in self.execution_history) / total_executions
        avg_execution_time = sum(e.total_time for e in self.execution_history) / total_executions
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions,
            "avg_step_success_rate": avg_success_rate,
            "avg_execution_time": avg_execution_time
        }