"""Exploration Planner - Plans intelligent code exploration strategies like Cline."""

import os
import re
from typing import Dict, List, Set, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

class ExplorationPhase(Enum):
    """Different phases of code exploration."""
    RECONNAISSANCE = "reconnaissance"  # Initial survey
    FOCUSED_ANALYSIS = "focused_analysis"  # Deep dive into specific areas
    CONNECTION_MAPPING = "connection_mapping"  # Map relationships
    SYNTHESIS = "synthesis"  # Combine findings

@dataclass
class ExplorationStep:
    """Represents a single step in the exploration plan."""
    phase: ExplorationPhase
    action: str
    target: str
    strategy: str
    priority: int
    estimated_effort: int  # 1-5 scale
    dependencies: List[str] = field(default_factory=list)
    expected_outcomes: List[str] = field(default_factory=list)

@dataclass
class ExplorationPlan:
    """Complete exploration plan."""
    objective: str
    context: Dict[str, Any]
    steps: List[ExplorationStep]
    estimated_duration: int  # minutes
    success_criteria: List[str]
    fallback_strategies: List[str]

class ExplorationPlanner:
    """
    Plans intelligent code exploration strategies based on objectives.
    Like Cline, it creates a strategic approach rather than random exploration.
    """
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        
        # Planning templates for different objectives
        self.planning_templates = self._initialize_planning_templates()
        
        # Context analyzers
        self.context_analyzers = {
            'project_type': self._analyze_project_type,
            'codebase_size': self._analyze_codebase_size,
            'complexity_level': self._analyze_complexity_level,
            'available_time': self._estimate_available_time
        }
    
    def _initialize_planning_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize planning templates for different exploration objectives."""
        return {
            'understand_architecture': {
                'phases': [
                    ExplorationPhase.RECONNAISSANCE,
                    ExplorationPhase.FOCUSED_ANALYSIS,
                    ExplorationPhase.CONNECTION_MAPPING,
                    ExplorationPhase.SYNTHESIS
                ],
                'key_targets': ['entry_points', 'config_files', 'main_modules', 'interfaces'],
                'strategies': ['breadth_first', 'dependency_trace', 'pattern_analysis'],
                'success_criteria': [
                    'Identified main architectural patterns',
                    'Mapped key components and their relationships',
                    'Understood data flow and control flow'
                ]
            },
            'find_security_issues': {
                'phases': [
                    ExplorationPhase.RECONNAISSANCE,
                    ExplorationPhase.FOCUSED_ANALYSIS
                ],
                'key_targets': ['auth_code', 'input_validation', 'data_handling', 'external_apis'],
                'strategies': ['security_focused', 'vulnerability_scan', 'code_review'],
                'success_criteria': [
                    'Identified potential security vulnerabilities',
                    'Analyzed authentication and authorization',
                    'Reviewed input validation and sanitization'
                ]
            },
            'trace_feature_implementation': {
                'phases': [
                    ExplorationPhase.RECONNAISSANCE,
                    ExplorationPhase.FOCUSED_ANALYSIS,
                    ExplorationPhase.CONNECTION_MAPPING
                ],
                'key_targets': ['feature_entry_points', 'related_functions', 'data_models', 'ui_components'],
                'strategies': ['feature_focused', 'trace_execution', 'dependency_analysis'],
                'success_criteria': [
                    'Traced complete feature implementation',
                    'Understood feature dependencies',
                    'Identified all related code components'
                ]
            },
            'analyze_performance': {
                'phases': [
                    ExplorationPhase.RECONNAISSANCE,
                    ExplorationPhase.FOCUSED_ANALYSIS
                ],
                'key_targets': ['hot_paths', 'database_queries', 'algorithms', 'resource_usage'],
                'strategies': ['performance_focused', 'bottleneck_analysis', 'complexity_analysis'],
                'success_criteria': [
                    'Identified performance bottlenecks',
                    'Analyzed algorithmic complexity',
                    'Found optimization opportunities'
                ]
            },
            'understand_api_design': {
                'phases': [
                    ExplorationPhase.RECONNAISSANCE,
                    ExplorationPhase.FOCUSED_ANALYSIS,
                    ExplorationPhase.CONNECTION_MAPPING
                ],
                'key_targets': ['api_endpoints', 'request_handlers', 'data_models', 'middleware'],
                'strategies': ['api_focused', 'trace_requests', 'interface_analysis'],
                'success_criteria': [
                    'Mapped all API endpoints',
                    'Understood request/response flow',
                    'Analyzed API design patterns'
                ]
            }
        }
    
    async def create_exploration_plan(self, objective: str, context: Dict[str, Any] = None) -> ExplorationPlan:
        """
        Create an intelligent exploration plan based on the objective.
        
        Args:
            objective: What we want to achieve (e.g., "understand authentication system")
            context: Additional context about the exploration
        """
        # Analyze the objective to determine the best template
        template_key = self._match_objective_to_template(objective)
        template = self.planning_templates.get(template_key, self.planning_templates['understand_architecture'])
        
        # Analyze project context
        project_context = await self._analyze_project_context(context or {})
        
        # Generate exploration steps
        steps = await self._generate_exploration_steps(objective, template, project_context)
        
        # Estimate duration
        estimated_duration = self._estimate_exploration_duration(steps)
        
        # Generate success criteria
        success_criteria = self._generate_success_criteria(objective, template)
        
        # Generate fallback strategies
        fallback_strategies = self._generate_fallback_strategies(objective, project_context)
        
        return ExplorationPlan(
            objective=objective,
            context=project_context,
            steps=steps,
            estimated_duration=estimated_duration,
            success_criteria=success_criteria,
            fallback_strategies=fallback_strategies
        )
    
    def _match_objective_to_template(self, objective: str) -> str:
        """Match the exploration objective to the best planning template."""
        objective_lower = objective.lower()
        
        # Keyword matching to determine template
        if any(keyword in objective_lower for keyword in ['architecture', 'structure', 'design', 'overview']):
            return 'understand_architecture'
        elif any(keyword in objective_lower for keyword in ['security', 'vulnerability', 'auth', 'login']):
            return 'find_security_issues'
        elif any(keyword in objective_lower for keyword in ['feature', 'implement', 'functionality']):
            return 'trace_feature_implementation'
        elif any(keyword in objective_lower for keyword in ['performance', 'speed', 'optimization', 'bottleneck']):
            return 'analyze_performance'
        elif any(keyword in objective_lower for keyword in ['api', 'endpoint', 'rest', 'graphql']):
            return 'understand_api_design'
        else:
            return 'understand_architecture'  # Default
    
    async def _analyze_project_context(self, provided_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the project to understand its context."""
        context = provided_context.copy()
        
        # Run context analyzers
        for analyzer_name, analyzer_func in self.context_analyzers.items():
            if analyzer_name not in context:
                context[analyzer_name] = await analyzer_func()
        
        return context
    
    async def _analyze_project_type(self) -> str:
        """Analyze what type of project this is."""
        # Look for common project indicators
        indicators = {
            'web_app': ['app.py', 'server.js', 'index.html', 'package.json'],
            'api_service': ['api.py', 'routes.py', 'endpoints.py', 'swagger.json'],
            'desktop_app': ['main.py', 'gui.py', 'tkinter', 'qt'],
            'library': ['setup.py', '__init__.py', 'lib/', 'src/'],
            'data_science': ['notebook.ipynb', 'data/', 'models/', 'analysis.py'],
            'mobile_app': ['android/', 'ios/', 'flutter/', 'react-native/']
        }
        
        project_files = []
        for root, dirs, files in os.walk(self.project_path):
            project_files.extend(files)
            if len(project_files) > 100:  # Limit for performance
                break
        
        project_files_lower = [f.lower() for f in project_files]
        
        # Score each project type
        scores = {}
        for project_type, type_indicators in indicators.items():
            score = 0
            for indicator in type_indicators:
                if any(indicator in pf for pf in project_files_lower):
                    score += 1
            scores[project_type] = score
        
        # Return the highest scoring type
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        else:
            return 'unknown'
    
    async def _analyze_codebase_size(self) -> str:
        """Analyze the size of the codebase."""
        file_count = 0
        total_size = 0
        
        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                if self._is_code_file(file):
                    file_count += 1
                    try:
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                    except OSError:
                        pass
        
        # Classify size
        if file_count < 10:
            return 'small'
        elif file_count < 100:
            return 'medium'
        elif file_count < 1000:
            return 'large'
        else:
            return 'very_large'
    
    async def _analyze_complexity_level(self) -> str:
        """Analyze the complexity level of the codebase."""
        # Simple heuristic based on directory depth and file patterns
        max_depth = 0
        has_tests = False
        has_config = False
        has_docs = False
        
        for root, dirs, files in os.walk(self.project_path):
            depth = len(Path(root).relative_to(self.project_path).parts)
            max_depth = max(max_depth, depth)
            
            # Check for complexity indicators
            for file in files:
                file_lower = file.lower()
                if 'test' in file_lower:
                    has_tests = True
                elif 'config' in file_lower or file_lower.endswith('.json'):
                    has_config = True
                elif file_lower.endswith('.md') or 'doc' in file_lower:
                    has_docs = True
        
        # Score complexity
        complexity_score = 0
        if max_depth > 3:
            complexity_score += 1
        if has_tests:
            complexity_score += 1
        if has_config:
            complexity_score += 1
        if has_docs:
            complexity_score += 1
        
        if complexity_score <= 1:
            return 'simple'
        elif complexity_score <= 2:
            return 'moderate'
        else:
            return 'complex'
    
    async def _estimate_available_time(self) -> int:
        """Estimate available time for exploration (in minutes)."""
        # Default estimation - in a real implementation, this could be user input
        return 30  # 30 minutes default
    
    async def _generate_exploration_steps(self, objective: str, template: Dict[str, Any], 
                                        context: Dict[str, Any]) -> List[ExplorationStep]:
        """Generate specific exploration steps based on the template and context."""
        steps = []
        phases = template['phases']
        key_targets = template['key_targets']
        strategies = template['strategies']
        
        step_priority = 1
        
        for phase in phases:
            if phase == ExplorationPhase.RECONNAISSANCE:
                # Initial survey steps
                steps.append(ExplorationStep(
                    phase=phase,
                    action="Survey project structure",
                    target="project_root",
                    strategy="breadth_first",
                    priority=step_priority,
                    estimated_effort=2,
                    expected_outcomes=["Project overview", "Key directories identified"]
                ))
                step_priority += 1
                
                steps.append(ExplorationStep(
                    phase=phase,
                    action="Identify entry points",
                    target="main_files",
                    strategy="pattern_matching",
                    priority=step_priority,
                    estimated_effort=2,
                    expected_outcomes=["Entry points located", "Execution flow understood"]
                ))
                step_priority += 1
            
            elif phase == ExplorationPhase.FOCUSED_ANALYSIS:
                # Deep dive steps based on key targets
                for target in key_targets:
                    steps.append(ExplorationStep(
                        phase=phase,
                        action=f"Analyze {target.replace('_', ' ')}",
                        target=target,
                        strategy=strategies[0] if strategies else "detailed_analysis",
                        priority=step_priority,
                        estimated_effort=3,
                        dependencies=[f"Survey project structure"],
                        expected_outcomes=[f"Detailed understanding of {target}"]
                    ))
                    step_priority += 1
            
            elif phase == ExplorationPhase.CONNECTION_MAPPING:
                # Relationship mapping steps
                steps.append(ExplorationStep(
                    phase=phase,
                    action="Map component relationships",
                    target="all_components",
                    strategy="dependency_trace",
                    priority=step_priority,
                    estimated_effort=4,
                    dependencies=[step.action for step in steps if step.phase == ExplorationPhase.FOCUSED_ANALYSIS],
                    expected_outcomes=["Component relationship map", "Dependency graph"]
                ))
                step_priority += 1
            
            elif phase == ExplorationPhase.SYNTHESIS:
                # Synthesis steps
                steps.append(ExplorationStep(
                    phase=phase,
                    action="Synthesize findings",
                    target="all_findings",
                    strategy="analysis_synthesis",
                    priority=step_priority,
                    estimated_effort=2,
                    dependencies=[step.action for step in steps],
                    expected_outcomes=["Comprehensive understanding", "Actionable insights"]
                ))
                step_priority += 1
        
        # Adjust steps based on context
        steps = self._adjust_steps_for_context(steps, context)
        
        return steps
    
    def _adjust_steps_for_context(self, steps: List[ExplorationStep], 
                                context: Dict[str, Any]) -> List[ExplorationStep]:
        """Adjust exploration steps based on project context."""
        codebase_size = context.get('codebase_size', 'medium')
        complexity_level = context.get('complexity_level', 'moderate')
        available_time = context.get('available_time', 30)
        
        # Adjust effort estimates based on codebase size
        size_multipliers = {
            'small': 0.5,
            'medium': 1.0,
            'large': 1.5,
            'very_large': 2.0
        }
        
        multiplier = size_multipliers.get(codebase_size, 1.0)
        
        for step in steps:
            step.estimated_effort = int(step.estimated_effort * multiplier)
        
        # If time is limited, prioritize high-priority steps
        if available_time < 20:  # Less than 20 minutes
            # Keep only high-priority steps
            steps = [step for step in steps if step.priority <= 3]
        
        # If complexity is high, add more detailed analysis steps
        if complexity_level == 'complex':
            for step in steps:
                if step.phase == ExplorationPhase.FOCUSED_ANALYSIS:
                    step.estimated_effort += 1
        
        return steps
    
    def _estimate_exploration_duration(self, steps: List[ExplorationStep]) -> int:
        """Estimate total duration for the exploration plan."""
        total_effort = sum(step.estimated_effort for step in steps)
        
        # Convert effort points to minutes (rough estimate)
        # Effort 1 = 3 minutes, Effort 2 = 6 minutes, etc.
        estimated_minutes = total_effort * 3
        
        return estimated_minutes
    
    def _generate_success_criteria(self, objective: str, template: Dict[str, Any]) -> List[str]:
        """Generate success criteria for the exploration."""
        base_criteria = template.get('success_criteria', [])
        
        # Add objective-specific criteria
        objective_lower = objective.lower()
        additional_criteria = []
        
        if 'understand' in objective_lower:
            additional_criteria.append("Clear understanding of the target system")
        if 'find' in objective_lower or 'identify' in objective_lower:
            additional_criteria.append("Successfully located and documented target items")
        if 'analyze' in objective_lower:
            additional_criteria.append("Comprehensive analysis completed with actionable insights")
        
        return base_criteria + additional_criteria
    
    def _generate_fallback_strategies(self, objective: str, context: Dict[str, Any]) -> List[str]:
        """Generate fallback strategies if the main plan doesn't work."""
        fallback_strategies = []
        
        # General fallback strategies
        fallback_strategies.extend([
            "Broaden search scope if initial targets are not found",
            "Use keyword search if structural analysis fails",
            "Focus on high-level overview if detailed analysis is too complex"
        ])
        
        # Context-specific fallbacks
        codebase_size = context.get('codebase_size', 'medium')
        if codebase_size in ['large', 'very_large']:
            fallback_strategies.append("Sample representative files if full analysis is too time-consuming")
        
        complexity_level = context.get('complexity_level', 'moderate')
        if complexity_level == 'complex':
            fallback_strategies.append("Focus on documentation and comments if code is too complex")
        
        return fallback_strategies
    
    def _is_code_file(self, filename: str) -> bool:
        """Check if a file is a code file."""
        code_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h', 
            '.go', '.rs', '.php', '.rb', '.cs', '.swift', '.kt'
        }
        
        return Path(filename).suffix.lower() in code_extensions