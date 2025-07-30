"""Reflection Module for Self-Critique and Response Refinement."""

import asyncio
import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from langchain.schema import HumanMessage, SystemMessage
from llm_manager import get_llm_manager, safe_llm_invoke
from .agent_state import AgentState


class ReflectionType(Enum):
    """Types of reflection analysis."""
    ACCURACY = "accuracy"           # Is the answer factually correct?
    COMPLETENESS = "completeness"   # Does it fully address the question?
    CLARITY = "clarity"            # Is it clear and well-structured?
    RELEVANCE = "relevance"        # Is it relevant to the question?
    REASONING = "reasoning"        # Is the reasoning sound?
    EVIDENCE = "evidence"          # Is it well-supported by evidence?


class ReflectionSeverity(Enum):
    """Severity levels for reflection issues."""
    CRITICAL = "critical"      # Must be fixed
    MAJOR = "major"           # Should be fixed
    MINOR = "minor"           # Could be improved
    SUGGESTION = "suggestion" # Optional improvement


@dataclass
class ReflectionIssue:
    """Represents an issue identified during reflection."""
    type: ReflectionType
    severity: ReflectionSeverity
    description: str
    suggestion: str
    confidence: float
    evidence: Optional[str] = None


@dataclass
class CritiqueResult:
    """Result of self-critique analysis."""
    overall_quality: float  # 0.0 to 1.0
    confidence: float      # 0.0 to 1.0
    issues: List[ReflectionIssue]
    strengths: List[str]
    needs_refinement: bool
    reasoning: str
    metadata: Dict[str, Any]


@dataclass
class RefinementResult:
    """Result of response refinement."""
    refined_response: str
    improvements_made: List[str]
    quality_improvement: float
    confidence: float
    refinement_reasoning: str
    metadata: Dict[str, Any]


class ReflectionModule:
    """Module for self-critique and response refinement."""
    
    def __init__(self, 
                 quality_threshold: float = 0.7,
                 max_refinement_iterations: int = 3,
                 verbose: bool = False):
        """Initialize the reflection module.
        
        Args:
            quality_threshold: Minimum quality score to accept response
            max_refinement_iterations: Maximum number of refinement cycles
            verbose: Whether to print detailed reflection process
        """
        self.quality_threshold = quality_threshold
        self.max_refinement_iterations = max_refinement_iterations
        self.verbose = verbose
        self.llm_manager = get_llm_manager()
    
    async def reflect_and_refine(self, 
                                state: AgentState,
                                response: str,
                                reasoning_steps: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
        """Main reflection and refinement process.
        
        Args:
            state: Current agent state
            response: Initial response to reflect on
            reasoning_steps: Steps taken to reach the response
            
        Returns:
            Tuple of (refined_response, reflection_metadata)
        """
        if self.verbose:
            print(f"\n🔍 Starting reflection process...")
        
        current_response = response
        reflection_history = []
        total_improvements = []
        
        for iteration in range(self.max_refinement_iterations):
            if self.verbose:
                print(f"\n📝 Reflection iteration {iteration + 1}/{self.max_refinement_iterations}")
            
            # Perform self-critique
            critique = await self.self_critique(
                state, current_response, reasoning_steps
            )
            
            reflection_history.append({
                "iteration": iteration + 1,
                "critique": critique,
                "response_at_iteration": current_response
            })
            
            if self.verbose:
                print(f"🎯 Quality Score: {critique.overall_quality:.2f}")
                print(f"🔍 Issues Found: {len(critique.issues)}")
                print(f"✅ Strengths: {len(critique.strengths)}")
            
            # Check if quality is acceptable
            if critique.overall_quality >= self.quality_threshold and not critique.needs_refinement:
                if self.verbose:
                    print(f"✅ Quality threshold met! Stopping refinement.")
                break
            
            # If quality is too low or issues exist, refine the response
            if critique.needs_refinement:
                refinement = await self.refine_response(
                    state, current_response, critique, reasoning_steps
                )
                
                current_response = refinement.refined_response
                total_improvements.extend(refinement.improvements_made)
                
                if self.verbose:
                    print(f"🔧 Refinement completed")
                    print(f"📈 Quality improvement: +{refinement.quality_improvement:.2f}")
            else:
                if self.verbose:
                    print(f"🛑 No refinement needed despite low quality score")
                break
        
        # Prepare metadata
        metadata = {
            "reflection_iterations": len(reflection_history),
            "final_quality_score": reflection_history[-1]["critique"].overall_quality if reflection_history else 0.0,
            "total_improvements": total_improvements,
            "reflection_history": reflection_history,
            "quality_threshold": self.quality_threshold,
            "threshold_met": reflection_history[-1]["critique"].overall_quality >= self.quality_threshold if reflection_history else False
        }
        
        if self.verbose:
            print(f"\n🎉 Reflection complete!")
            print(f"📊 Final quality: {metadata['final_quality_score']:.2f}")
            print(f"🔧 Total improvements: {len(total_improvements)}")
        
        return current_response, metadata
    
    async def self_critique(self, 
                           state: AgentState,
                           response: str,
                           reasoning_steps: List[Dict[str, Any]]) -> CritiqueResult:
        """Perform self-critique on the response.
        
        Args:
            state: Current agent state
            response: Response to critique
            reasoning_steps: Reasoning steps taken
            
        Returns:
            CritiqueResult with detailed analysis
        """
        if self.verbose:
            print(f"🤔 Performing self-critique...")
        
        # Create critique prompt
        critique_prompt = self._create_critique_prompt(state, response, reasoning_steps)
        
        messages = [
            SystemMessage(content=self._get_critique_system_prompt()),
            HumanMessage(content=critique_prompt)
        ]
        
        try:
            llm = self.llm_manager.get_llm_for_session(state.get("session_id"))
            llm_response = await safe_llm_invoke(llm, messages, state.get("session_id"))
            critique_text = llm_response.content
            
            if self.verbose:
                print(f"🔍 Critique analysis completed")
            
            # Parse the critique response
            return self._parse_critique_response(critique_text)
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Critique failed: {str(e)}")
            
            # Return default critique on failure
            return CritiqueResult(
                overall_quality=0.5,
                confidence=0.3,
                issues=[ReflectionIssue(
                    type=ReflectionType.REASONING,
                    severity=ReflectionSeverity.MAJOR,
                    description="Unable to perform self-critique due to error",
                    suggestion="Manual review recommended",
                    confidence=0.3
                )],
                strengths=[],
                needs_refinement=False,
                reasoning=f"Critique failed: {str(e)}",
                metadata={"error": str(e)}
            )
    
    async def refine_response(self,
                             state: AgentState,
                             original_response: str,
                             critique: CritiqueResult,
                             reasoning_steps: List[Dict[str, Any]]) -> RefinementResult:
        """Refine the response based on critique.
        
        Args:
            state: Current agent state
            original_response: Original response to refine
            critique: Critique result with issues to address
            reasoning_steps: Original reasoning steps
            
        Returns:
            RefinementResult with improved response
        """
        if self.verbose:
            print(f"🔧 Refining response based on critique...")
        
        # Create refinement prompt
        refinement_prompt = self._create_refinement_prompt(
            state, original_response, critique, reasoning_steps
        )
        
        messages = [
            SystemMessage(content=self._get_refinement_system_prompt()),
            HumanMessage(content=refinement_prompt)
        ]
        
        try:
            llm = self.llm_manager.get_llm_for_session(state.get("session_id"))
            llm_response = await safe_llm_invoke(llm, messages, state.get("session_id"))
            refinement_text = llm_response.content
            
            if self.verbose:
                print(f"✨ Response refinement completed")
            
            # Parse the refinement response
            return self._parse_refinement_response(refinement_text, critique)
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Refinement failed: {str(e)}")
            
            # Return original response on failure
            return RefinementResult(
                refined_response=original_response,
                improvements_made=[],
                quality_improvement=0.0,
                confidence=0.3,
                refinement_reasoning=f"Refinement failed: {str(e)}",
                metadata={"error": str(e)}
            )
    
    def _create_critique_prompt(self, 
                               state: AgentState,
                               response: str,
                               reasoning_steps: List[Dict[str, Any]]) -> str:
        """Create prompt for self-critique."""
        
        # Format reasoning steps
        steps_text = ""
        for i, step in enumerate(reasoning_steps, 1):
            if step.get("thought"):
                steps_text += f"Step {i} - Thought: {step['thought']}\n"
            if step.get("action"):
                steps_text += f"Step {i} - Action: {step['action']} with input: {step.get('action_input', 'N/A')}\n"
            if step.get("observation"):
                steps_text += f"Step {i} - Observation: {step['observation']}\n"
            steps_text += "\n"
        
        return f"""Please perform a comprehensive self-critique of the following response and reasoning process.

ORIGINAL QUESTION:
{state['input']}

REASONING STEPS TAKEN:
{steps_text}

FINAL RESPONSE:
{response}

CRITIQUE INSTRUCTIONS:
Analyze the response across these dimensions:
1. ACCURACY: Is the information factually correct?
2. COMPLETENESS: Does it fully address all parts of the question?
3. CLARITY: Is it clear, well-structured, and easy to understand?
4. RELEVANCE: Is it directly relevant to the question asked?
5. REASONING: Is the logical reasoning sound and well-supported?
6. EVIDENCE: Are claims backed by appropriate evidence or tool results?

For each dimension, provide:
- A score from 0.0 to 1.0
- Specific issues identified (if any)
- Suggestions for improvement
- Your confidence in the assessment

Also provide:
- Overall quality score (0.0 to 1.0)
- List of strengths in the response
- Whether refinement is needed
- Overall reasoning for your assessment

Format your response as JSON with the following structure:
{{
    "overall_quality": 0.0-1.0,
    "confidence": 0.0-1.0,
    "dimensions": {{
        "accuracy": {{"score": 0.0-1.0, "issues": [], "suggestions": []}},
        "completeness": {{"score": 0.0-1.0, "issues": [], "suggestions": []}},
        "clarity": {{"score": 0.0-1.0, "issues": [], "suggestions": []}},
        "relevance": {{"score": 0.0-1.0, "issues": [], "suggestions": []}},
        "reasoning": {{"score": 0.0-1.0, "issues": [], "suggestions": []}},
        "evidence": {{"score": 0.0-1.0, "issues": [], "suggestions": []}}
    }},
    "strengths": [],
    "needs_refinement": true/false,
    "reasoning": "Overall assessment reasoning"
}}"""
    
    def _create_refinement_prompt(self,
                                 state: AgentState,
                                 original_response: str,
                                 critique: CritiqueResult,
                                 reasoning_steps: List[Dict[str, Any]]) -> str:
        """Create prompt for response refinement."""
        
        # Format issues for the prompt
        issues_text = ""
        for issue in critique.issues:
            issues_text += f"- {issue.type.value.upper()}: {issue.description}\n"
            issues_text += f"  Suggestion: {issue.suggestion}\n"
            issues_text += f"  Severity: {issue.severity.value}\n\n"
        
        return f"""Please refine the following response based on the self-critique analysis.

ORIGINAL QUESTION:
{state['input']}

ORIGINAL RESPONSE:
{original_response}

CRITIQUE ANALYSIS:
Overall Quality Score: {critique.overall_quality:.2f}
Needs Refinement: {critique.needs_refinement}

IDENTIFIED ISSUES:
{issues_text}

STRENGTHS TO MAINTAIN:
{chr(10).join(f'- {strength}' for strength in critique.strengths)}

REFINEMENT INSTRUCTIONS:
1. Address each identified issue while maintaining the strengths
2. Ensure the refined response is more accurate, complete, and clear
3. Keep the same core information but improve presentation and reasoning
4. If the original response was fundamentally correct, make incremental improvements
5. If there were major issues, provide a substantially improved response

Provide your refined response along with:
- List of specific improvements made
- Explanation of how each issue was addressed
- Estimated quality improvement

Format your response as JSON:
{{
    "refined_response": "Your improved response here",
    "improvements_made": ["List of specific improvements"],
    "quality_improvement": 0.0-1.0,
    "confidence": 0.0-1.0,
    "refinement_reasoning": "Explanation of refinement process"
}}"""
    
    def _get_critique_system_prompt(self) -> str:
        """Get system prompt for critique analysis."""
        return """You are an expert AI critic specializing in evaluating AI responses for quality, accuracy, and effectiveness.

Your role is to:
1. Objectively analyze responses across multiple quality dimensions
2. Identify specific issues and provide constructive suggestions
3. Recognize strengths and areas for improvement
4. Provide actionable feedback for refinement

Be thorough, fair, and constructive in your analysis. Focus on helping improve the response quality while acknowledging what works well.

Always respond in valid JSON format as specified in the prompt."""
    
    def _get_refinement_system_prompt(self) -> str:
        """Get system prompt for response refinement."""
        return """You are an expert AI response refiner specializing in improving AI-generated content based on critique analysis.

Your role is to:
1. Take constructive criticism and transform it into concrete improvements
2. Maintain the core value and accuracy of the original response
3. Enhance clarity, completeness, and overall quality
4. Address specific issues while preserving strengths

Focus on making targeted improvements that directly address the identified issues. Be precise and purposeful in your refinements.

Always respond in valid JSON format as specified in the prompt."""
    
    def _parse_critique_response(self, critique_text: str) -> CritiqueResult:
        """Parse the LLM critique response into structured format."""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', critique_text, re.DOTALL)
            if json_match:
                critique_data = json.loads(json_match.group())
            else:
                critique_data = json.loads(critique_text)
            
            # Extract issues from dimensions
            issues = []
            dimensions = critique_data.get("dimensions", {})
            
            for dim_name, dim_data in dimensions.items():
                if dim_data.get("issues"):
                    for issue_text in dim_data["issues"]:
                        issues.append(ReflectionIssue(
                            type=ReflectionType(dim_name.lower()),
                            severity=ReflectionSeverity.MAJOR,  # Default severity
                            description=issue_text,
                            suggestion=dim_data.get("suggestions", ["Review and improve"])[0],
                            confidence=critique_data.get("confidence", 0.7)
                        ))
            
            return CritiqueResult(
                overall_quality=critique_data.get("overall_quality", 0.5),
                confidence=critique_data.get("confidence", 0.7),
                issues=issues,
                strengths=critique_data.get("strengths", []),
                needs_refinement=critique_data.get("needs_refinement", True),
                reasoning=critique_data.get("reasoning", "Automated critique analysis"),
                metadata={"raw_response": critique_text}
            )
            
        except Exception as e:
            # Fallback parsing if JSON parsing fails
            return CritiqueResult(
                overall_quality=0.5,
                confidence=0.3,
                issues=[ReflectionIssue(
                    type=ReflectionType.REASONING,
                    severity=ReflectionSeverity.MAJOR,
                    description="Failed to parse critique response",
                    suggestion="Manual review recommended",
                    confidence=0.3
                )],
                strengths=[],
                needs_refinement=False,
                reasoning=f"Parse error: {str(e)}",
                metadata={"error": str(e), "raw_response": critique_text}
            )
    
    def _parse_refinement_response(self, 
                                  refinement_text: str,
                                  original_critique: CritiqueResult) -> RefinementResult:
        """Parse the LLM refinement response into structured format."""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', refinement_text, re.DOTALL)
            if json_match:
                refinement_data = json.loads(json_match.group())
            else:
                refinement_data = json.loads(refinement_text)
            
            return RefinementResult(
                refined_response=refinement_data.get("refined_response", "Refinement failed"),
                improvements_made=refinement_data.get("improvements_made", []),
                quality_improvement=refinement_data.get("quality_improvement", 0.0),
                confidence=refinement_data.get("confidence", 0.7),
                refinement_reasoning=refinement_data.get("refinement_reasoning", "Automated refinement"),
                metadata={"raw_response": refinement_text}
            )
            
        except Exception as e:
            # Fallback if JSON parsing fails
            return RefinementResult(
                refined_response=refinement_text,  # Use raw text as fallback
                improvements_made=["Attempted refinement based on critique"],
                quality_improvement=0.1,  # Assume minimal improvement
                confidence=0.3,
                refinement_reasoning=f"Parse error, using raw response: {str(e)}",
                metadata={"error": str(e), "raw_response": refinement_text}
            )