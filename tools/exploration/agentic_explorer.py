"""Agentic File Explorer - Cline-inspired intelligent file exploration."""

import os
import ast
import re
import json
import asyncio
from typing import Dict, List, Set, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

@dataclass
class ExplorationGoal:
    """Represents a specific exploration goal."""
    purpose: str
    target_patterns: List[str]
    depth_limit: int = 5
    file_limit: int = 20
    priority: int = 1  # 1=high, 2=medium, 3=low

@dataclass
class FileExplorationResult:
    """Result of exploring a single file."""
    file_path: str
    language: str
    purpose_relevance: float  # 0.0 to 1.0
    key_findings: List[str]
    imports: List[str]
    exports: List[str]
    functions: List[str]
    classes: List[str]
    connections: List[str]  # Files this connects to
    insights: List[str]

class ExplorationStrategy(Enum):
    """Different exploration strategies like Cline uses."""
    BREADTH_FIRST = "breadth_first"
    DEPTH_FIRST = "depth_first"
    PURPOSE_DRIVEN = "purpose_driven"
    DEPENDENCY_TRACE = "dependency_trace"
    FEATURE_FOCUSED = "feature_focused"

class AgenticFileExplorer:
    """
    Agentic File Explorer that intelligently navigates codebases like Cline.
    No indexing - explores files on-demand with purpose and context.
    """
    
    def __init__(self, project_path: str, exclude_dirs: Set[str] = None, 
                 exclude_patterns: List[str] = None, max_file_size: int = 10*1024*1024):
        self.project_path = Path(project_path).resolve()
        self.exclude_dirs = exclude_dirs or set()
        self.exclude_patterns = exclude_patterns or []
        self.max_file_size = max_file_size
        
        # Exploration state
        self.explored_files: Dict[str, FileExplorationResult] = {}
        self.exploration_queue: List[Tuple[str, ExplorationGoal]] = []
        self.connection_graph: Dict[str, List[str]] = {}
        self.purpose_cache: Dict[str, List[str]] = {}
        
        # Language-specific patterns
        self.language_patterns = self._initialize_language_patterns()
    
    def _initialize_language_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize patterns for different programming languages."""
        return {
            'python': {
                'imports': [
                    r'from\s+([^\s]+)\s+import',
                    r'import\s+([^\s,]+)',
                ],
                'functions': [r'def\s+(\w+)\s*\('],
                'classes': [r'class\s+(\w+)'],
                'exports': [r'__all__\s*=\s*\[(.*?)\]'],
                'entry_points': ['if __name__ == "__main__":', 'def main()', 'app.run()', 'uvicorn.run(']
            },
            'javascript': {
                'imports': [
                    r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
                    r'import\s+[\'"]([^\'"]+)[\'"]',
                    r'require\([\'"]([^\'"]+)[\'"]\)'
                ],
                'functions': [r'function\s+(\w+)', r'const\s+(\w+)\s*=\s*\(', r'(\w+)\s*:\s*function'],
                'classes': [r'class\s+(\w+)'],
                'exports': [r'export\s+.*?(\w+)', r'module\.exports\s*='],
                'entry_points': ['app.listen(', 'server.listen(', 'process.argv']
            }
        }
    
    async def explore_with_purpose(self, purpose: str, strategy: ExplorationStrategy = ExplorationStrategy.PURPOSE_DRIVEN,
                                 entry_points: List[str] = None, max_files: int = 50) -> Dict[str, Any]:
        """
        Explore the codebase with a specific purpose, like Cline would.
        """
        exploration_goal = ExplorationGoal(
            purpose=purpose,
            target_patterns=self._extract_purpose_patterns(purpose),
            file_limit=max_files
        )
        
        # Clear previous exploration state
        self.explored_files.clear()
        self.exploration_queue.clear()
        self.connection_graph.clear()
        
        # Determine starting points
        start_files = await self._determine_starting_points(purpose, entry_points)
        
        # Add starting files to exploration queue
        for file_path in start_files:
            self.exploration_queue.append((file_path, exploration_goal))
        
        # Execute exploration strategy
        results = await self._execute_exploration_strategy(strategy, exploration_goal)
        
        return {
            'purpose': purpose,
            'strategy': strategy.value,
            'files_explored': len(self.explored_files),
            'exploration_results': results,
            'connection_graph': self.connection_graph,
            'key_insights': self._generate_exploration_insights(purpose),
            'recommended_next_steps': self._recommend_next_exploration_steps(purpose, results)
        }
    
    def _extract_purpose_patterns(self, purpose: str) -> List[str]:
        """Extract search patterns from the exploration purpose."""
        purpose_lower = purpose.lower()
        patterns = []
        
        # Common purpose patterns
        if 'auth' in purpose_lower or 'login' in purpose_lower:
            patterns.extend(['auth', 'login', 'password', 'token', 'session', 'jwt'])
        elif 'api' in purpose_lower or 'endpoint' in purpose_lower:
            patterns.extend(['api', 'route', 'endpoint', 'handler', 'controller'])
        elif 'database' in purpose_lower or 'db' in purpose_lower:
            patterns.extend(['database', 'db', 'model', 'schema', 'query', 'orm'])
        else:
            # Extract keywords from purpose
            words = re.findall(r'\b\w+\b', purpose_lower)
            patterns.extend([word for word in words if len(word) > 3])
        
        return patterns
    
    async def _determine_starting_points(self, purpose: str, entry_points: List[str] = None) -> List[str]:
        """Determine the best starting points for exploration."""
        if entry_points:
            return [str(self.project_path / ep) for ep in entry_points if (self.project_path / ep).exists()]
        
        start_files = []
        purpose_patterns = self._extract_purpose_patterns(purpose)
        
        # Look for files that match the purpose
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                if self._should_include_file(file):
                    file_path = os.path.join(root, file)
                    file_lower = file.lower()
                    path_lower = file_path.lower()
                    
                    # Calculate relevance score
                    relevance_score = 0
                    for pattern in purpose_patterns:
                        if pattern in file_lower:
                            relevance_score += 3
                        elif pattern in path_lower:
                            relevance_score += 1
                    
                    if relevance_score > 0:
                        start_files.append((file_path, relevance_score))
        
        # Sort by relevance and return top candidates
        start_files.sort(key=lambda x: x[1], reverse=True)
        return [fp for fp, _ in start_files[:10]]  # Top 10 starting points
    
    async def _execute_exploration_strategy(self, strategy: ExplorationStrategy, 
                                          goal: ExplorationGoal) -> Dict[str, Any]:
        """Execute the chosen exploration strategy."""
        return await self._purpose_driven_exploration(goal)
    
    async def _purpose_driven_exploration(self, goal: ExplorationGoal) -> Dict[str, Any]:
        """Explore files based on their relevance to the purpose."""
        results = {
            'strategy': 'purpose_driven',
            'files_analyzed': [],
            'key_findings': [],
            'connections_discovered': [],
            'insights': []
        }
        
        files_processed = 0
        while self.exploration_queue and files_processed < goal.file_limit:
            file_path, exploration_goal = self.exploration_queue.pop(0)
            
            if file_path in self.explored_files:
                continue
            
            # Explore the file
            file_result = await self._explore_single_file(file_path, exploration_goal)
            if file_result:
                self.explored_files[file_path] = file_result
                results['files_analyzed'].append(file_result)
                
                # Add connected files to queue if they're relevant
                for connection in file_result.connections:
                    if connection not in self.explored_files and self._is_file_relevant(connection, goal):
                        self.exploration_queue.append((connection, goal))
                
                files_processed += 1
        
        # Generate insights
        results['insights'] = self._generate_purpose_insights(goal.purpose, results['files_analyzed'])
        
        return results
    
    async def _explore_single_file(self, file_path: str, goal: ExplorationGoal) -> Optional[FileExplorationResult]:
        """Explore a single file with the given goal."""
        try:
            if not self._is_valid_file(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            language = self._detect_file_language(file_path)
            
            # Extract file information
            imports = self._extract_imports(content, language)
            functions = self._extract_functions(content, language)
            classes = self._extract_classes(content, language)
            exports = self._extract_exports(content, language)
            
            # Calculate purpose relevance
            relevance = self._calculate_purpose_relevance(content, file_path, goal)
            
            # Find connections to other files
            connections = await self._find_file_connections(file_path, imports, content)
            
            # Generate insights
            insights = self._generate_file_insights(content, file_path, language, goal.purpose)
            
            # Extract key findings
            key_findings = self._extract_key_findings(content, language, goal.target_patterns)
            
            return FileExplorationResult(
                file_path=file_path,
                language=language,
                purpose_relevance=relevance,
                key_findings=key_findings,
                imports=imports,
                exports=exports,
                functions=functions,
                classes=classes,
                connections=connections,
                insights=insights
            )
            
        except Exception as e:
            return None
    
    def _calculate_purpose_relevance(self, content: str, file_path: str, goal: ExplorationGoal) -> float:
        """Calculate how relevant a file is to the exploration purpose."""
        relevance_score = 0.0
        content_lower = content.lower()
        file_lower = file_path.lower()
        
        # Check for target patterns
        for pattern in goal.target_patterns:
            pattern_lower = pattern.lower()
            
            # File name/path matches
            if pattern_lower in file_lower:
                relevance_score += 0.3
            
            # Content matches
            content_matches = len(re.findall(re.escape(pattern_lower), content_lower))
            if content_matches > 0:
                relevance_score += min(0.5, content_matches * 0.1)
        
        # Normalize to 0-1 range
        return min(1.0, relevance_score)
    
    def _extract_imports(self, content: str, language: str) -> List[str]:
        """Extract import statements from file content."""
        imports = []
        patterns = self.language_patterns.get(language, {}).get('imports', [])
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            imports.extend(matches)
        
        return list(set(imports))
    
    def _extract_functions(self, content: str, language: str) -> List[str]:
        """Extract function names from file content."""
        functions = []
        patterns = self.language_patterns.get(language, {}).get('functions', [])
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            functions.extend(matches)
        
        return list(set(functions))
    
    def _extract_classes(self, content: str, language: str) -> List[str]:
        """Extract class names from file content."""
        classes = []
        patterns = self.language_patterns.get(language, {}).get('classes', [])
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            classes.extend(matches)
        
        return list(set(classes))
    
    def _extract_exports(self, content: str, language: str) -> List[str]:
        """Extract export statements from file content."""
        exports = []
        patterns = self.language_patterns.get(language, {}).get('exports', [])
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            exports.extend(matches)
        
        return list(set(exports))
    
    async def _find_file_connections(self, file_path: str, imports: List[str], content: str) -> List[str]:
        """Find files that this file connects to."""
        connections = []
        file_dir = Path(file_path).parent
        
        for import_name in imports:
            # Try to resolve import to actual file
            resolved_files = await self._resolve_import_to_files(import_name, file_dir)
            connections.extend(resolved_files)
        
        # Update connection graph
        if file_path not in self.connection_graph:
            self.connection_graph[file_path] = []
        self.connection_graph[file_path].extend(connections)
        
        return connections
    
    async def _resolve_import_to_files(self, import_name: str, from_dir: Path) -> List[str]:
        """Resolve an import statement to actual file paths."""
        resolved_files = []
        
        # Handle relative imports
        if import_name.startswith('./') or import_name.startswith('../'):
            potential_path = (from_dir / import_name).resolve()
            
            # Try different extensions
            for ext in ['.py', '.js', '.ts', '.jsx', '.tsx']:
                potential_file = potential_path.with_suffix(ext)
                if potential_file.exists() and potential_file.is_file():
                    resolved_files.append(str(potential_file))
        
        return resolved_files
    
    def _extract_key_findings(self, content: str, language: str, target_patterns: List[str]) -> List[str]:
        """Extract key findings relevant to the exploration purpose."""
        findings = []
        
        for pattern in target_patterns:
            pattern_lower = pattern.lower()
            
            # Find lines containing the pattern
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if pattern_lower in line.lower():
                    findings.append(f"Found '{pattern}' at line {i+1}: {line.strip()}")
        
        return findings[:5]  # Limit to top 5 findings
    
    def _generate_file_insights(self, content: str, file_path: str, language: str, purpose: str) -> List[str]:
        """Generate insights about the file in context of the purpose."""
        insights = []
        
        # Basic file info
        lines = len(content.split('\n'))
        insights.append(f"File has {lines} lines of {language} code")
        
        return insights
    
    def _generate_exploration_insights(self, purpose: str) -> List[str]:
        """Generate overall insights from the exploration."""
        insights = []
        
        if not self.explored_files:
            return ["No files were explored"]
        
        total_files = len(self.explored_files)
        insights.append(f"Explored {total_files} files related to '{purpose}'")
        
        return insights
    
    def _generate_purpose_insights(self, purpose: str, files_analyzed: List[FileExplorationResult]) -> List[str]:
        """Generate insights specific to the exploration purpose."""
        insights = []
        
        if not files_analyzed:
            return ["No files analyzed for this purpose"]
        
        insights.append(f"Analyzed {len(files_analyzed)} files for '{purpose}'")
        
        return insights
    
    def _recommend_next_exploration_steps(self, purpose: str, results: Dict[str, Any]) -> List[str]:
        """Recommend next steps for exploration."""
        recommendations = []
        
        files_analyzed = results.get('files_analyzed', [])
        
        if not files_analyzed:
            recommendations.append("Try broadening the search criteria or checking different entry points")
        else:
            recommendations.append("Continue exploring connected files for deeper understanding")
        
        return recommendations
    
    def _is_file_relevant(self, file_path: str, goal: ExplorationGoal) -> bool:
        """Check if a file is relevant to the exploration goal."""
        file_lower = file_path.lower()
        
        for pattern in goal.target_patterns:
            if pattern.lower() in file_lower:
                return True
        
        return False
    
    def _should_include_file(self, file_name: str) -> bool:
        """Check if a file should be included in exploration."""
        for pattern in self.exclude_patterns:
            if re.match(pattern.replace('*', '.*'), file_name):
                return False
        return True
    
    def _is_valid_file(self, file_path: str) -> bool:
        """Check if a file is valid for exploration."""
        if not os.path.exists(file_path):
            return False
        
        try:
            if os.path.getsize(file_path) > self.max_file_size:
                return False
        except OSError:
            return False
        
        return self._should_include_file(os.path.basename(file_path))
    
    def _detect_file_language(self, file_path: str) -> str:
        """Detect the programming language of a file."""
        extension = Path(file_path).suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust'
        }
        
        return language_map.get(extension, 'unknown')