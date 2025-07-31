"""Dynamic Code Traversal - Follow code connections like Cline does."""

import os
import ast
import re
import json
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

class TraversalStrategy(Enum):
    """Different strategies for code traversal."""
    FOLLOW_IMPORTS = "follow_imports"
    TRACE_FUNCTION_CALLS = "trace_function_calls"
    FOLLOW_DATA_FLOW = "follow_data_flow"
    EXPLORE_INHERITANCE = "explore_inheritance"
    MAP_DEPENDENCIES = "map_dependencies"
    TRACE_API_FLOW = "trace_api_flow"

@dataclass
class TraversalNode:
    """Represents a node in the code traversal graph."""
    file_path: str
    element_name: str  # function, class, variable name
    element_type: str  # function, class, variable, import, etc.
    line_number: int
    content_snippet: str
    connections: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TraversalPath:
    """Represents a path through the code."""
    start_node: TraversalNode
    end_node: TraversalNode
    intermediate_nodes: List[TraversalNode] = field(default_factory=list)
    path_type: str = "unknown"
    confidence: float = 0.0
    insights: List[str] = field(default_factory=list)

@dataclass
class TraversalResult:
    """Result of code traversal."""
    strategy: str
    start_point: str
    nodes_discovered: List[TraversalNode]
    paths_found: List[TraversalPath]
    connection_graph: Dict[str, List[str]]
    insights: List[str]
    recommendations: List[str]

class DynamicCodeTraversal:
    """
    Dynamic code traversal system that follows code connections intelligently.
    Like Cline, it understands the logical flow and relationships in code.
    """
    
    def __init__(self, project_path: str, exclude_dirs: Set[str] = None):
        self.project_path = Path(project_path).resolve()
        self.exclude_dirs = exclude_dirs or set()
        
        # Traversal state
        self.visited_nodes: Set[str] = set()
        self.node_cache: Dict[str, TraversalNode] = {}
        self.connection_graph: Dict[str, List[str]] = {}
        
        # Language-specific traversal patterns
        self.traversal_patterns = self._initialize_traversal_patterns()
    
    def _initialize_traversal_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize patterns for different traversal strategies."""
        return {
            'python': {
                'imports': [
                    r'from\s+([^\s]+)\s+import\s+([^\s,]+)',
                    r'import\s+([^\s,]+)(?:\s+as\s+([^\s,]+))?'
                ],
                'function_calls': [
                    r'(\w+)\s*\(',
                    r'self\.(\w+)\s*\(',
                    r'(\w+)\.(\w+)\s*\('
                ],
                'class_inheritance': [
                    r'class\s+(\w+)\s*\(\s*([^)]+)\s*\)'
                ],
                'variable_assignments': [
                    r'(\w+)\s*=\s*([^;\n]+)'
                ],
                'function_definitions': [
                    r'def\s+(\w+)\s*\([^)]*\)'
                ]
            },
            'javascript': {
                'imports': [
                    r'import\s+\{([^}]+)\}\s+from\s+[\'"]([^\'"]+)[\'"]',
                    r'import\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"]',
                    r'const\s+\{([^}]+)\}\s+=\s+require\([\'"]([^\'"]+)[\'"]\)'
                ],
                'function_calls': [
                    r'(\w+)\s*\(',
                    r'this\.(\w+)\s*\(',
                    r'(\w+)\.(\w+)\s*\('
                ],
                'function_definitions': [
                    r'function\s+(\w+)\s*\([^)]*\)',
                    r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>',
                    r'(\w+)\s*:\s*function\s*\([^)]*\)'
                ]
            }
        }
    
    async def traverse_code(self, start_point: str, strategy: TraversalStrategy, 
                          max_depth: int = 5, max_nodes: int = 50) -> TraversalResult:
        """
        Traverse code starting from a specific point using the given strategy.
        
        Args:
            start_point: Starting file path or "file:function" format
            strategy: How to traverse the code
            max_depth: Maximum traversal depth
            max_nodes: Maximum nodes to explore
        """
        # Clear previous state
        self.visited_nodes.clear()
        self.node_cache.clear()
        self.connection_graph.clear()
        
        # Parse start point
        start_file, start_element = self._parse_start_point(start_point)
        
        # Create initial node
        start_node = await self._create_traversal_node(start_file, start_element)
        if not start_node:
            return TraversalResult(
                strategy=strategy.value,
                start_point=start_point,
                nodes_discovered=[],
                paths_found=[],
                connection_graph={},
                insights=["Could not create starting node"],
                recommendations=["Check if the start point exists and is accessible"]
            )
        
        # Execute traversal strategy
        if strategy == TraversalStrategy.FOLLOW_IMPORTS:
            result = await self._traverse_imports(start_node, max_depth, max_nodes)
        elif strategy == TraversalStrategy.TRACE_FUNCTION_CALLS:
            result = await self._traverse_function_calls(start_node, max_depth, max_nodes)
        elif strategy == TraversalStrategy.FOLLOW_DATA_FLOW:
            result = await self._traverse_data_flow(start_node, max_depth, max_nodes)
        elif strategy == TraversalStrategy.EXPLORE_INHERITANCE:
            result = await self._traverse_inheritance(start_node, max_depth, max_nodes)
        elif strategy == TraversalStrategy.MAP_DEPENDENCIES:
            result = await self._traverse_dependencies(start_node, max_depth, max_nodes)
        elif strategy == TraversalStrategy.TRACE_API_FLOW:
            result = await self._traverse_api_flow(start_node, max_depth, max_nodes)
        else:
            result = await self._traverse_general(start_node, max_depth, max_nodes)
        
        return result
    
    def _parse_start_point(self, start_point: str) -> Tuple[str, Optional[str]]:
        """Parse start point into file and element."""
        if ':' in start_point:
            file_part, element_part = start_point.split(':', 1)
            return file_part, element_part
        else:
            return start_point, None
    
    async def _create_traversal_node(self, file_path: str, element_name: Optional[str] = None) -> Optional[TraversalNode]:
        """Create a traversal node from file and element."""
        try:
            # Resolve file path
            if not os.path.isabs(file_path):
                file_path = str(self.project_path / file_path)
            
            if not os.path.exists(file_path):
                return None
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # If no specific element, create node for the file
            if not element_name:
                return TraversalNode(
                    file_path=file_path,
                    element_name=os.path.basename(file_path),
                    element_type="file",
                    line_number=1,
                    content_snippet=content[:200] + "..." if len(content) > 200 else content,
                    metadata={"language": self._detect_language(file_path)}
                )
            
            # Find specific element in file
            element_info = await self._find_element_in_file(content, element_name, file_path)
            if element_info:
                return TraversalNode(
                    file_path=file_path,
                    element_name=element_name,
                    element_type=element_info["type"],
                    line_number=element_info["line"],
                    content_snippet=element_info["snippet"],
                    metadata=element_info.get("metadata", {})
                )
            
            return None
            
        except Exception as e:
            return None
    
    async def _find_element_in_file(self, content: str, element_name: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Find a specific element (function, class, etc.) in file content."""
        language = self._detect_language(file_path)
        lines = content.split('\n')
        
        # Try to find the element using language-specific patterns
        patterns = self.traversal_patterns.get(language, {})
        
        # Look for function definitions
        for pattern in patterns.get('function_definitions', []):
            for i, line in enumerate(lines):
                match = re.search(pattern, line)
                if match and match.group(1) == element_name:
                    # Get some context around the function
                    start_line = max(0, i - 1)
                    end_line = min(len(lines), i + 10)
                    snippet = '\n'.join(lines[start_line:end_line])
                    
                    return {
                        "type": "function",
                        "line": i + 1,
                        "snippet": snippet,
                        "metadata": {"language": language}
                    }
        
        # Look for class definitions
        if language == 'python':
            for i, line in enumerate(lines):
                if re.search(rf'class\s+{element_name}\s*[\(:]', line):
                    start_line = max(0, i - 1)
                    end_line = min(len(lines), i + 10)
                    snippet = '\n'.join(lines[start_line:end_line])
                    
                    return {
                        "type": "class",
                        "line": i + 1,
                        "snippet": snippet,
                        "metadata": {"language": language}
                    }
        
        # If not found as function or class, look for any mention
        for i, line in enumerate(lines):
            if element_name in line:
                return {
                    "type": "reference",
                    "line": i + 1,
                    "snippet": line.strip(),
                    "metadata": {"language": language}
                }
        
        return None
    
    async def _traverse_imports(self, start_node: TraversalNode, max_depth: int, max_nodes: int) -> TraversalResult:
        """Traverse code by following import statements."""
        nodes_discovered = [start_node]
        paths_found = []
        current_depth = 0
        nodes_to_process = [start_node]
        
        while nodes_to_process and current_depth < max_depth and len(nodes_discovered) < max_nodes:
            next_nodes = []
            
            for node in nodes_to_process:
                if node.file_path in self.visited_nodes:
                    continue
                
                self.visited_nodes.add(node.file_path)
                
                # Find imports in this file
                imports = await self._find_imports_in_file(node.file_path)
                
                for import_info in imports:
                    # Try to resolve import to actual file
                    resolved_files = await self._resolve_import(import_info, node.file_path)
                    
                    for resolved_file in resolved_files:
                        if resolved_file not in self.visited_nodes:
                            import_node = await self._create_traversal_node(resolved_file)
                            if import_node:
                                nodes_discovered.append(import_node)
                                next_nodes.append(import_node)
                                
                                # Create path
                                path = TraversalPath(
                                    start_node=node,
                                    end_node=import_node,
                                    path_type="import",
                                    confidence=0.8,
                                    insights=[f"Import relationship: {import_info['name']}"]
                                )
                                paths_found.append(path)
                                
                                # Update connection graph
                                if node.file_path not in self.connection_graph:
                                    self.connection_graph[node.file_path] = []
                                self.connection_graph[node.file_path].append(resolved_file)
            
            nodes_to_process = next_nodes
            current_depth += 1
        
        insights = self._generate_traversal_insights(nodes_discovered, paths_found, "imports")
        recommendations = self._generate_traversal_recommendations(nodes_discovered, paths_found, "imports")
        
        return TraversalResult(
            strategy="follow_imports",
            start_point=f"{start_node.file_path}:{start_node.element_name}",
            nodes_discovered=nodes_discovered,
            paths_found=paths_found,
            connection_graph=self.connection_graph,
            insights=insights,
            recommendations=recommendations
        )
    
    async def _traverse_function_calls(self, start_node: TraversalNode, max_depth: int, max_nodes: int) -> TraversalResult:
        """Traverse code by following function calls."""
        nodes_discovered = [start_node]
        paths_found = []
        
        # Find function calls in the starting file
        function_calls = await self._find_function_calls_in_file(start_node.file_path)
        
        for call_info in function_calls[:max_nodes]:
            # Try to find where this function is defined
            definition_locations = await self._find_function_definition(call_info['name'], start_node.file_path)
            
            for location in definition_locations:
                def_node = await self._create_traversal_node(location['file'], call_info['name'])
                if def_node:
                    nodes_discovered.append(def_node)
                    
                    path = TraversalPath(
                        start_node=start_node,
                        end_node=def_node,
                        path_type="function_call",
                        confidence=0.7,
                        insights=[f"Function call: {call_info['name']} at line {call_info['line']}"]
                    )
                    paths_found.append(path)
        
        insights = self._generate_traversal_insights(nodes_discovered, paths_found, "function_calls")
        recommendations = self._generate_traversal_recommendations(nodes_discovered, paths_found, "function_calls")
        
        return TraversalResult(
            strategy="trace_function_calls",
            start_point=f"{start_node.file_path}:{start_node.element_name}",
            nodes_discovered=nodes_discovered,
            paths_found=paths_found,
            connection_graph=self.connection_graph,
            insights=insights,
            recommendations=recommendations
        )
    
    async def _traverse_data_flow(self, start_node: TraversalNode, max_depth: int, max_nodes: int) -> TraversalResult:
        """Traverse code by following data flow."""
        # Simplified implementation - in a full version, this would trace variable assignments and usage
        return await self._traverse_general(start_node, max_depth, max_nodes)
    
    async def _traverse_inheritance(self, start_node: TraversalNode, max_depth: int, max_nodes: int) -> TraversalResult:
        """Traverse code by following class inheritance."""
        nodes_discovered = [start_node]
        paths_found = []
        
        if start_node.element_type == "class":
            # Find parent classes
            parent_classes = await self._find_parent_classes(start_node.file_path, start_node.element_name)
            
            for parent_info in parent_classes:
                parent_locations = await self._find_class_definition(parent_info['name'])
                
                for location in parent_locations:
                    parent_node = await self._create_traversal_node(location['file'], parent_info['name'])
                    if parent_node:
                        nodes_discovered.append(parent_node)
                        
                        path = TraversalPath(
                            start_node=start_node,
                            end_node=parent_node,
                            path_type="inheritance",
                            confidence=0.9,
                            insights=[f"Inherits from: {parent_info['name']}"]
                        )
                        paths_found.append(path)
        
        insights = self._generate_traversal_insights(nodes_discovered, paths_found, "inheritance")
        recommendations = self._generate_traversal_recommendations(nodes_discovered, paths_found, "inheritance")
        
        return TraversalResult(
            strategy="explore_inheritance",
            start_point=f"{start_node.file_path}:{start_node.element_name}",
            nodes_discovered=nodes_discovered,
            paths_found=paths_found,
            connection_graph=self.connection_graph,
            insights=insights,
            recommendations=recommendations
        )
    
    async def _traverse_dependencies(self, start_node: TraversalNode, max_depth: int, max_nodes: int) -> TraversalResult:
        """Traverse code by mapping all dependencies."""
        return await self._traverse_imports(start_node, max_depth, max_nodes)
    
    async def _traverse_api_flow(self, start_node: TraversalNode, max_depth: int, max_nodes: int) -> TraversalResult:
        """Traverse code by following API request/response flow."""
        # Simplified implementation - would trace API endpoints and their handlers
        return await self._traverse_general(start_node, max_depth, max_nodes)
    
    async def _traverse_general(self, start_node: TraversalNode, max_depth: int, max_nodes: int) -> TraversalResult:
        """General traversal strategy."""
        nodes_discovered = [start_node]
        paths_found = []
        
        insights = ["General traversal completed"]
        recommendations = ["Use more specific traversal strategies for better results"]
        
        return TraversalResult(
            strategy="general",
            start_point=f"{start_node.file_path}:{start_node.element_name}",
            nodes_discovered=nodes_discovered,
            paths_found=paths_found,
            connection_graph=self.connection_graph,
            insights=insights,
            recommendations=recommendations
        )
    
    async def _find_imports_in_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Find all import statements in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            language = self._detect_language(file_path)
            patterns = self.traversal_patterns.get(language, {}).get('imports', [])
            
            imports = []
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                for pattern in patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        if isinstance(match, tuple):
                            import_name = match[0] if match[0] else match[1]
                        else:
                            import_name = match
                        
                        imports.append({
                            'name': import_name,
                            'line': i + 1,
                            'full_line': line.strip()
                        })
            
            return imports
            
        except Exception:
            return []
    
    async def _resolve_import(self, import_info: Dict[str, Any], from_file: str) -> List[str]:
        """Resolve an import to actual file paths."""
        resolved_files = []
        import_name = import_info['name']
        from_dir = Path(from_file).parent
        
        # Handle relative imports
        if import_name.startswith('./') or import_name.startswith('../'):
            potential_path = (from_dir / import_name).resolve()
            
            # Try different extensions
            for ext in ['.py', '.js', '.ts', '.jsx', '.tsx']:
                potential_file = potential_path.with_suffix(ext)
                if potential_file.exists():
                    resolved_files.append(str(potential_file))
        
        # Handle absolute imports (simplified)
        elif '.' in import_name:
            parts = import_name.split('.')
            potential_path = self.project_path
            
            for part in parts:
                potential_path = potential_path / part
            
            # Try as file
            for ext in ['.py', '.js', '.ts']:
                potential_file = potential_path.with_suffix(ext)
                if potential_file.exists():
                    resolved_files.append(str(potential_file))
            
            # Try as package
            potential_init = potential_path / '__init__.py'
            if potential_init.exists():
                resolved_files.append(str(potential_init))
        
        return resolved_files
    
    async def _find_function_calls_in_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Find all function calls in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            language = self._detect_language(file_path)
            patterns = self.traversal_patterns.get(language, {}).get('function_calls', [])
            
            calls = []
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                for pattern in patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        if isinstance(match, tuple):
                            func_name = match[0] if match[0] else match[1]
                        else:
                            func_name = match
                        
                        calls.append({
                            'name': func_name,
                            'line': i + 1,
                            'context': line.strip()
                        })
            
            return calls
            
        except Exception:
            return []
    
    async def _find_function_definition(self, func_name: str, context_file: str) -> List[Dict[str, str]]:
        """Find where a function is defined."""
        definitions = []
        
        # First, check the same file
        try:
            with open(context_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            language = self._detect_language(context_file)
            patterns = self.traversal_patterns.get(language, {}).get('function_definitions', [])
            
            for pattern in patterns:
                if re.search(pattern.replace(r'(\w+)', func_name), content):
                    definitions.append({'file': context_file})
                    break
        
        except Exception:
            pass
        
        return definitions
    
    async def _find_parent_classes(self, file_path: str, class_name: str) -> List[Dict[str, str]]:
        """Find parent classes of a given class."""
        parents = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Look for class definition with inheritance
            pattern = rf'class\s+{class_name}\s*\(\s*([^)]+)\s*\)'
            match = re.search(pattern, content)
            
            if match:
                parent_list = match.group(1)
                parent_names = [p.strip() for p in parent_list.split(',')]
                
                for parent_name in parent_names:
                    parents.append({'name': parent_name})
        
        except Exception:
            pass
        
        return parents
    
    async def _find_class_definition(self, class_name: str) -> List[Dict[str, str]]:
        """Find where a class is defined."""
        # Simplified - would search through project files
        return []
    
    def _generate_traversal_insights(self, nodes: List[TraversalNode], paths: List[TraversalPath], 
                                   traversal_type: str) -> List[str]:
        """Generate insights from traversal results."""
        insights = []
        
        insights.append(f"Discovered {len(nodes)} nodes through {traversal_type} traversal")
        insights.append(f"Found {len(paths)} connections")
        
        # Language distribution
        languages = {}
        for node in nodes:
            lang = node.metadata.get('language', 'unknown')
            languages[lang] = languages.get(lang, 0) + 1
        
        if languages:
            main_lang = max(languages.items(), key=lambda x: x[1])
            insights.append(f"Primary language: {main_lang[0]} ({main_lang[1]} files)")
        
        # Path type distribution
        path_types = {}
        for path in paths:
            path_types[path.path_type] = path_types.get(path.path_type, 0) + 1
        
        if path_types:
            insights.append(f"Connection types: {', '.join(f'{k}({v})' for k, v in path_types.items())}")
        
        return insights
    
    def _generate_traversal_recommendations(self, nodes: List[TraversalNode], paths: List[TraversalPath], 
                                          traversal_type: str) -> List[str]:
        """Generate recommendations from traversal results."""
        recommendations = []
        
        if not nodes:
            recommendations.append("No nodes discovered - check starting point and traversal strategy")
            return recommendations
        
        if len(nodes) == 1:
            recommendations.append("Only starting node found - try different traversal strategy or increase depth")
        
        if traversal_type == "imports":
            recommendations.append("Explore function calls within discovered modules for deeper understanding")
        elif traversal_type == "function_calls":
            recommendations.append("Trace data flow through the discovered function calls")
        
        # High confidence paths
        high_confidence_paths = [p for p in paths if p.confidence > 0.8]
        if high_confidence_paths:
            recommendations.append(f"Focus on {len(high_confidence_paths)} high-confidence connections")
        
        return recommendations
    
    def _detect_language(self, file_path: str) -> str:
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