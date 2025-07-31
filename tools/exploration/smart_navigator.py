"""Smart Code Navigator - Intelligent code discovery and navigation like Cline."""

import os
import re
import json
from typing import Dict, List, Set, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

class NavigationIntent(Enum):
    """Different intents for code navigation."""
    FIND_IMPLEMENTATION = "find_implementation"
    LOCATE_USAGE = "locate_usage"
    DISCOVER_RELATED = "discover_related"
    FIND_ENTRY_POINTS = "find_entry_points"
    EXPLORE_FEATURE = "explore_feature"
    UNDERSTAND_FLOW = "understand_flow"

@dataclass
class NavigationTarget:
    """Represents a navigation target."""
    name: str
    type: str  # function, class, variable, file, etc.
    context: str = ""
    priority: int = 1

@dataclass
class NavigationResult:
    """Result of smart navigation."""
    target: NavigationTarget
    found_locations: List[Dict[str, Any]]
    related_items: List[Dict[str, Any]]
    navigation_path: List[str]
    confidence: float
    insights: List[str]
    next_suggestions: List[str]

class SmartCodeNavigator:
    """
    Smart code navigator that finds code elements intelligently.
    Like Cline, it understands context and can navigate to relevant code.
    """
    
    def __init__(self, project_path: str, exclude_dirs: Set[str] = None):
        self.project_path = Path(project_path).resolve()
        self.exclude_dirs = exclude_dirs or set()
        
        # Navigation cache
        self.location_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.usage_cache: Dict[str, List[Dict[str, Any]]] = {}
        
        # Smart patterns for different navigation intents
        self.navigation_patterns = self._initialize_navigation_patterns()
    
    def _initialize_navigation_patterns(self) -> Dict[NavigationIntent, Dict[str, Any]]:
        """Initialize patterns for different navigation intents."""
        return {
            NavigationIntent.FIND_IMPLEMENTATION: {
                'python': {
                    'function': [r'def\s+{name}\s*\(', r'async\s+def\s+{name}\s*\('],
                    'class': [r'class\s+{name}\s*[\(:]'],
                    'variable': [r'{name}\s*=', r'self\.{name}\s*=']
                },
                'javascript': {
                    'function': [
                        r'function\s+{name}\s*\(',
                        r'const\s+{name}\s*=\s*\(',
                        r'{name}\s*:\s*function',
                        r'{name}\s*=>\s*'
                    ],
                    'class': [r'class\s+{name}\s*\{{'],
                    'variable': [r'const\s+{name}\s*=', r'let\s+{name}\s*=', r'var\s+{name}\s*=']
                }
            },
            NavigationIntent.LOCATE_USAGE: {
                'patterns': [
                    r'{name}\s*\(',  # Function calls
                    r'{name}\.',     # Method calls
                    r'\.{name}\s*\(',  # Method calls
                    r'{name}\s*=',   # Assignments
                    r'=\s*{name}',   # Assignments
                    r'{name}\s*\[',  # Array/dict access
                    r'import.*{name}',  # Imports
                    r'from.*import.*{name}'  # Imports
                ]
            },
            NavigationIntent.FIND_ENTRY_POINTS: {
                'patterns': [
                    r'if\s+__name__\s*==\s*["\']__main__["\']',
                    r'def\s+main\s*\(',
                    r'app\.run\s*\(',
                    r'app\.listen\s*\(',
                    r'server\.listen\s*\(',
                    r'uvicorn\.run\s*\(',
                    r'process\.argv'
                ],
                'files': [
                    'main.py', 'app.py', 'server.py', 'index.js', 'index.ts',
                    'main.js', 'main.ts', 'run.py', 'start.py'
                ]
            }
        }
    
    async def navigate_to(self, target: NavigationTarget, intent: NavigationIntent, 
                         context_files: List[str] = None) -> NavigationResult:
        """
        Navigate to a specific target with given intent.
        
        Args:
            target: What we're looking for
            intent: Why we're looking for it
            context_files: Files to search in (if None, searches all)
        """
        # Check cache first
        cache_key = f"{target.name}:{target.type}:{intent.value}"
        if cache_key in self.location_cache:
            cached_locations = self.location_cache[cache_key]
        else:
            # Find locations
            cached_locations = await self._find_target_locations(target, intent, context_files)
            self.location_cache[cache_key] = cached_locations
        
        # Find related items
        related_items = await self._find_related_items(target, cached_locations)
        
        # Build navigation path
        navigation_path = self._build_navigation_path(target, cached_locations)
        
        # Calculate confidence
        confidence = self._calculate_navigation_confidence(cached_locations, target, intent)
        
        # Generate insights
        insights = self._generate_navigation_insights(target, cached_locations, related_items, intent)
        
        # Generate next suggestions
        next_suggestions = self._generate_next_suggestions(target, cached_locations, intent)
        
        return NavigationResult(
            target=target,
            found_locations=cached_locations,
            related_items=related_items,
            navigation_path=navigation_path,
            confidence=confidence,
            insights=insights,
            next_suggestions=next_suggestions
        )
    
    async def _find_target_locations(self, target: NavigationTarget, intent: NavigationIntent, 
                                   context_files: List[str] = None) -> List[Dict[str, Any]]:
        """Find all locations where the target exists."""
        locations = []
        
        # Determine files to search
        if context_files:
            search_files = [f for f in context_files if os.path.exists(f)]
        else:
            search_files = await self._get_relevant_files(target, intent)
        
        # Search for target in files
        for file_path in search_files:
            file_locations = await self._search_in_file(file_path, target, intent)
            locations.extend(file_locations)
        
        # Sort by relevance
        locations.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return locations
    
    async def _get_relevant_files(self, target: NavigationTarget, intent: NavigationIntent) -> List[str]:
        """Get files that are likely to contain the target."""
        relevant_files = []
        
        # If looking for entry points, prioritize certain files
        if intent == NavigationIntent.FIND_ENTRY_POINTS:
            entry_files = self.navigation_patterns[intent].get('files', [])
            for root, dirs, files in os.walk(self.project_path):
                dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
                for file in files:
                    if file.lower() in [ef.lower() for ef in entry_files]:
                        relevant_files.append(os.path.join(root, file))
        
        # For other intents, search files that might contain the target
        else:
            target_name_lower = target.name.lower()
            
            for root, dirs, files in os.walk(self.project_path):
                dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
                
                for file in files:
                    if self._should_include_file(file):
                        file_path = os.path.join(root, file)
                        file_lower = file.lower()
                        
                        # Prioritize files with target name in filename
                        if target_name_lower in file_lower:
                            relevant_files.insert(0, file_path)  # High priority
                        else:
                            relevant_files.append(file_path)  # Normal priority
        
        return relevant_files[:100]  # Limit to prevent excessive searching
    
    async def _search_in_file(self, file_path: str, target: NavigationTarget, 
                            intent: NavigationIntent) -> List[Dict[str, Any]]:
        """Search for target in a specific file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            locations = []
            language = self._detect_language(file_path)
            lines = content.split('\n')
            
            # Get patterns for this intent and language
            patterns = self._get_search_patterns(target, intent, language)
            
            for pattern in patterns:
                # Replace {name} placeholder with actual target name
                search_pattern = pattern.format(name=re.escape(target.name))
                
                for i, line in enumerate(lines):
                    matches = re.finditer(search_pattern, line, re.IGNORECASE)
                    for match in matches:
                        # Get context around the match
                        context_start = max(0, i - 2)
                        context_end = min(len(lines), i + 3)
                        context_lines = lines[context_start:context_end]
                        
                        location = {
                            'file_path': file_path,
                            'line_number': i + 1,
                            'column': match.start(),
                            'match_text': match.group(),
                            'line_content': line.strip(),
                            'context': '\n'.join(context_lines),
                            'language': language,
                            'match_type': self._classify_match(line, target, intent),
                            'relevance_score': self._calculate_match_relevance(line, target, intent)
                        }
                        locations.append(location)
            
            return locations
            
        except Exception:
            return []
    
    def _get_search_patterns(self, target: NavigationTarget, intent: NavigationIntent, 
                           language: str) -> List[str]:
        """Get search patterns for the given target, intent, and language."""
        patterns = []
        
        if intent == NavigationIntent.FIND_IMPLEMENTATION:
            impl_patterns = self.navigation_patterns[intent].get(language, {})
            target_patterns = impl_patterns.get(target.type, [])
            patterns.extend(target_patterns)
        
        elif intent == NavigationIntent.LOCATE_USAGE:
            usage_patterns = self.navigation_patterns[intent].get('patterns', [])
            patterns.extend(usage_patterns)
        
        elif intent == NavigationIntent.FIND_ENTRY_POINTS:
            entry_patterns = self.navigation_patterns[intent].get('patterns', [])
            patterns.extend(entry_patterns)
        
        else:
            # Generic patterns
            patterns.extend([
                r'{name}',  # Simple name match
                r'\b{name}\b',  # Word boundary match
            ])
        
        return patterns
    
    def _classify_match(self, line: str, target: NavigationTarget, intent: NavigationIntent) -> str:
        """Classify the type of match found."""
        line_lower = line.lower().strip()
        
        if intent == NavigationIntent.FIND_IMPLEMENTATION:
            if line_lower.startswith('def ') or line_lower.startswith('async def '):
                return 'function_definition'
            elif line_lower.startswith('class '):
                return 'class_definition'
            elif '=' in line and not line_lower.startswith('if '):
                return 'variable_assignment'
        
        elif intent == NavigationIntent.LOCATE_USAGE:
            if f'{target.name}(' in line:
                return 'function_call'
            elif f'.{target.name}' in line:
                return 'method_call'
            elif 'import' in line_lower:
                return 'import_statement'
        
        elif intent == NavigationIntent.FIND_ENTRY_POINTS:
            if '__main__' in line:
                return 'main_guard'
            elif 'def main(' in line:
                return 'main_function'
            elif any(keyword in line_lower for keyword in ['run(', 'listen(', 'start(']):
                return 'application_start'
        
        return 'reference'
    
    def _calculate_match_relevance(self, line: str, target: NavigationTarget, 
                                 intent: NavigationIntent) -> float:
        """Calculate relevance score for a match."""
        score = 0.5  # Base score
        
        line_lower = line.lower().strip()
        
        # Boost score for exact matches
        if target.name in line:
            score += 0.3
        
        # Intent-specific scoring
        if intent == NavigationIntent.FIND_IMPLEMENTATION:
            if line_lower.startswith('def ') or line_lower.startswith('class '):
                score += 0.4  # Definitions are highly relevant
            elif '=' in line and not line_lower.startswith('if '):
                score += 0.2  # Assignments are moderately relevant
        
        elif intent == NavigationIntent.LOCATE_USAGE:
            if f'{target.name}(' in line:
                score += 0.3  # Function calls are relevant
            elif 'import' in line_lower:
                score += 0.2  # Imports are moderately relevant
        
        # Context boost
        if target.context and target.context.lower() in line_lower:
            score += 0.2
        
        return min(1.0, score)
    
    async def _find_related_items(self, target: NavigationTarget, 
                                locations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find items related to the target."""
        related_items = []
        
        # Find items in the same files as the target
        target_files = set(loc['file_path'] for loc in locations)
        
        for file_path in target_files:
            # Find other functions/classes in the same file
            file_items = await self._extract_file_items(file_path)
            
            for item in file_items:
                if item['name'] != target.name:  # Exclude the target itself
                    item['relation_type'] = 'same_file'
                    item['file_path'] = file_path
                    related_items.append(item)
        
        # Limit related items
        return related_items[:20]
    
    async def _extract_file_items(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract functions, classes, etc. from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            items = []
            language = self._detect_language(file_path)
            lines = content.split('\n')
            
            # Extract functions
            if language == 'python':
                for i, line in enumerate(lines):
                    # Function definitions
                    func_match = re.search(r'def\s+(\w+)\s*\(', line)
                    if func_match:
                        items.append({
                            'name': func_match.group(1),
                            'type': 'function',
                            'line': i + 1
                        })
                    
                    # Class definitions
                    class_match = re.search(r'class\s+(\w+)\s*[\(:]', line)
                    if class_match:
                        items.append({
                            'name': class_match.group(1),
                            'type': 'class',
                            'line': i + 1
                        })
            
            elif language in ['javascript', 'typescript']:
                for i, line in enumerate(lines):
                    # Function definitions
                    func_patterns = [
                        r'function\s+(\w+)\s*\(',
                        r'const\s+(\w+)\s*=\s*\(',
                        r'(\w+)\s*:\s*function'
                    ]
                    
                    for pattern in func_patterns:
                        func_match = re.search(pattern, line)
                        if func_match:
                            items.append({
                                'name': func_match.group(1),
                                'type': 'function',
                                'line': i + 1
                            })
                            break
                    
                    # Class definitions
                    class_match = re.search(r'class\s+(\w+)\s*\{', line)
                    if class_match:
                        items.append({
                            'name': class_match.group(1),
                            'type': 'class',
                            'line': i + 1
                        })
            
            return items
            
        except Exception:
            return []
    
    def _build_navigation_path(self, target: NavigationTarget, 
                             locations: List[Dict[str, Any]]) -> List[str]:
        """Build a navigation path to the target."""
        if not locations:
            return []
        
        # Use the most relevant location
        best_location = locations[0]
        
        path = [
            f"File: {best_location['file_path']}",
            f"Line: {best_location['line_number']}",
            f"Type: {best_location.get('match_type', 'unknown')}"
        ]
        
        return path
    
    def _calculate_navigation_confidence(self, locations: List[Dict[str, Any]], 
                                       target: NavigationTarget, intent: NavigationIntent) -> float:
        """Calculate confidence in the navigation results."""
        if not locations:
            return 0.0
        
        # Base confidence on number of locations and their relevance
        avg_relevance = sum(loc.get('relevance_score', 0) for loc in locations) / len(locations)
        location_count_factor = min(1.0, len(locations) / 5)  # Normalize to max 5 locations
        
        confidence = (avg_relevance * 0.7) + (location_count_factor * 0.3)
        
        # Boost confidence for exact matches
        exact_matches = [loc for loc in locations if loc.get('match_type') in 
                        ['function_definition', 'class_definition', 'main_function']]
        if exact_matches:
            confidence += 0.2
        
        return min(1.0, confidence)
    
    def _generate_navigation_insights(self, target: NavigationTarget, locations: List[Dict[str, Any]], 
                                    related_items: List[Dict[str, Any]], intent: NavigationIntent) -> List[str]:
        """Generate insights from navigation results."""
        insights = []
        
        if not locations:
            insights.append(f"No locations found for {target.name}")
            return insights
        
        insights.append(f"Found {len(locations)} locations for {target.name}")
        
        # File distribution
        files = set(loc['file_path'] for loc in locations)
        if len(files) == 1:
            insights.append(f"All occurrences in single file: {list(files)[0]}")
        else:
            insights.append(f"Distributed across {len(files)} files")
        
        # Match type distribution
        match_types = {}
        for loc in locations:
            match_type = loc.get('match_type', 'unknown')
            match_types[match_type] = match_types.get(match_type, 0) + 1
        
        if match_types:
            insights.append(f"Match types: {', '.join(f'{k}({v})' for k, v in match_types.items())}")
        
        # Related items insight
        if related_items:
            insights.append(f"Found {len(related_items)} related items in the same context")
        
        return insights
    
    def _generate_next_suggestions(self, target: NavigationTarget, locations: List[Dict[str, Any]], 
                                 intent: NavigationIntent) -> List[str]:
        """Generate suggestions for next navigation steps."""
        suggestions = []
        
        if not locations:
            suggestions.append("Try searching with different target type or broader context")
            return suggestions
        
        # Intent-specific suggestions
        if intent == NavigationIntent.FIND_IMPLEMENTATION:
            suggestions.append("Explore usage patterns of this implementation")
            suggestions.append("Check for related functions in the same module")
        
        elif intent == NavigationIntent.LOCATE_USAGE:
            suggestions.append("Navigate to the implementation to understand the interface")
            suggestions.append("Trace data flow through the usage points")
        
        elif intent == NavigationIntent.FIND_ENTRY_POINTS:
            suggestions.append("Trace execution flow from the entry points")
            suggestions.append("Explore configuration and initialization code")
        
        # General suggestions based on results
        if len(locations) > 5:
            suggestions.append("Focus on the most relevant matches to avoid information overload")
        
        files_with_matches = set(loc['file_path'] for loc in locations)
        if len(files_with_matches) > 1:
            suggestions.append("Compare implementations across different files")
        
        return suggestions
    
    def _should_include_file(self, file_name: str) -> bool:
        """Check if a file should be included in navigation."""
        # Skip binary files, logs, etc.
        exclude_extensions = {'.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib', 
                            '.log', '.tmp', '.cache', '.min.js', '.min.css'}
        
        file_ext = Path(file_name).suffix.lower()
        return file_ext not in exclude_extensions
    
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
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'cpp',
            '.h': 'cpp'
        }
        
        return language_map.get(extension, 'unknown')