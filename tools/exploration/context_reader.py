"""Context-Aware Code Reader - Reads code with specific purposes like Cline."""

import os
import ast
import re
import json
from typing import Dict, List, Set, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

class ReadingPurpose(Enum):
    """Different purposes for reading code."""
    UNDERSTAND_FUNCTION = "understand_function"
    TRACE_DATA_FLOW = "trace_data_flow"
    FIND_SECURITY_ISSUES = "find_security_issues"
    ANALYZE_ARCHITECTURE = "analyze_architecture"
    EXTRACT_API_ENDPOINTS = "extract_api_endpoints"
    UNDERSTAND_ERROR_HANDLING = "understand_error_handling"
    FIND_DEPENDENCIES = "find_dependencies"
    ANALYZE_PERFORMANCE = "analyze_performance"

@dataclass
class CodeSection:
    """Represents a section of code with context."""
    content: str
    start_line: int
    end_line: int
    purpose_relevance: float
    context_type: str  # function, class, module, etc.
    key_elements: List[str]
    insights: List[str]

@dataclass
class ReadingResult:
    """Result of context-aware code reading."""
    file_path: str
    purpose: str
    relevant_sections: List[CodeSection]
    summary: str
    key_insights: List[str]
    recommendations: List[str]
    confidence_score: float

class ContextAwareCodeReader:
    """
    Context-aware code reader that understands code with specific purposes.
    Like Cline, it doesn't just read code - it understands what it's looking for.
    """
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        
        # Purpose-specific patterns
        self.purpose_patterns = self._initialize_purpose_patterns()
        
        # Language-specific analyzers
        self.language_analyzers = {
            'python': self._analyze_python_code,
            'javascript': self._analyze_javascript_code,
            'typescript': self._analyze_typescript_code,
            'java': self._analyze_java_code
        }
    
    def _initialize_purpose_patterns(self) -> Dict[ReadingPurpose, Dict[str, List[str]]]:
        """Initialize patterns for different reading purposes."""
        return {
            ReadingPurpose.UNDERSTAND_FUNCTION: {
                'keywords': ['def ', 'function ', 'async ', 'return', 'yield'],
                'patterns': [r'def\s+(\w+)', r'function\s+(\w+)', r'const\s+(\w+)\s*='],
                'context_clues': ['parameters', 'arguments', 'docstring', 'comments']
            },
            ReadingPurpose.TRACE_DATA_FLOW: {
                'keywords': ['=', 'return', 'yield', 'input', 'output', 'transform'],
                'patterns': [r'(\w+)\s*=', r'return\s+(\w+)', r'yield\s+(\w+)'],
                'context_clues': ['variable assignments', 'function calls', 'data transformations']
            },
            ReadingPurpose.FIND_SECURITY_ISSUES: {
                'keywords': ['password', 'token', 'secret', 'auth', 'sql', 'exec', 'eval'],
                'patterns': [
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r'token\s*=\s*["\'][^"\']+["\']',
                    r'exec\s*\(',
                    r'eval\s*\(',
                    r'sql.*\+.*'
                ],
                'context_clues': ['hardcoded credentials', 'SQL injection', 'code execution']
            },
            ReadingPurpose.EXTRACT_API_ENDPOINTS: {
                'keywords': ['route', 'endpoint', 'api', 'get', 'post', 'put', 'delete'],
                'patterns': [
                    r'@app\.route\(["\']([^"\']+)["\']',
                    r'@router\.(get|post|put|delete)\(["\']([^"\']+)["\']',
                    r'app\.(get|post|put|delete)\(["\']([^"\']+)["\']'
                ],
                'context_clues': ['HTTP methods', 'URL patterns', 'request handlers']
            },
            ReadingPurpose.UNDERSTAND_ERROR_HANDLING: {
                'keywords': ['try', 'except', 'catch', 'throw', 'raise', 'error', 'exception'],
                'patterns': [
                    r'try\s*:',
                    r'except\s+(\w+)',
                    r'catch\s*\(',
                    r'throw\s+new\s+(\w+)',
                    r'raise\s+(\w+)'
                ],
                'context_clues': ['exception types', 'error messages', 'recovery strategies']
            },
            ReadingPurpose.FIND_DEPENDENCIES: {
                'keywords': ['import', 'require', 'include', 'from'],
                'patterns': [
                    r'import\s+([^\s]+)',
                    r'from\s+([^\s]+)\s+import',
                    r'require\(["\']([^"\']+)["\']\)',
                    r'#include\s*<([^>]+)>'
                ],
                'context_clues': ['module names', 'package imports', 'external dependencies']
            }
        }
    
    async def read_with_purpose(self, file_path: str, purpose: ReadingPurpose, 
                              context: Dict[str, Any] = None) -> ReadingResult:
        """
        Read a file with a specific purpose, like Cline would.
        
        Args:
            file_path: Path to the file to read
            purpose: What we're trying to understand
            context: Additional context for the reading
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Detect language
            language = self._detect_language(file_path)
            
            # Get purpose-specific patterns
            purpose_config = self.purpose_patterns.get(purpose, {})
            
            # Find relevant sections
            relevant_sections = await self._find_relevant_sections(
                content, purpose, purpose_config, language
            )
            
            # Analyze with language-specific analyzer
            if language in self.language_analyzers:
                enhanced_sections = await self.language_analyzers[language](
                    content, relevant_sections, purpose
                )
            else:
                enhanced_sections = relevant_sections
            
            # Generate summary and insights
            summary = self._generate_summary(enhanced_sections, purpose)
            key_insights = self._extract_key_insights(enhanced_sections, purpose)
            recommendations = self._generate_recommendations(enhanced_sections, purpose)
            confidence_score = self._calculate_confidence_score(enhanced_sections)
            
            return ReadingResult(
                file_path=file_path,
                purpose=purpose.value,
                relevant_sections=enhanced_sections,
                summary=summary,
                key_insights=key_insights,
                recommendations=recommendations,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            return ReadingResult(
                file_path=file_path,
                purpose=purpose.value,
                relevant_sections=[],
                summary=f"Error reading file: {str(e)}",
                key_insights=[],
                recommendations=[],
                confidence_score=0.0
            )
    
    async def _find_relevant_sections(self, content: str, purpose: ReadingPurpose, 
                                    purpose_config: Dict[str, List[str]], 
                                    language: str) -> List[CodeSection]:
        """Find sections of code relevant to the reading purpose."""
        relevant_sections = []
        lines = content.split('\n')
        
        keywords = purpose_config.get('keywords', [])
        patterns = purpose_config.get('patterns', [])
        
        # Find lines that match our purpose
        relevant_line_indices = set()
        
        # Keyword matching
        for i, line in enumerate(lines):
            line_lower = line.lower()
            for keyword in keywords:
                if keyword.lower() in line_lower:
                    relevant_line_indices.add(i)
        
        # Pattern matching
        for pattern in patterns:
            for i, line in enumerate(lines):
                if re.search(pattern, line, re.IGNORECASE):
                    relevant_line_indices.add(i)
        
        # Group consecutive relevant lines into sections
        if relevant_line_indices:
            sections = self._group_lines_into_sections(
                list(sorted(relevant_line_indices)), lines, purpose
            )
            relevant_sections.extend(sections)
        
        return relevant_sections
    
    def _group_lines_into_sections(self, relevant_indices: List[int], 
                                 lines: List[str], purpose: ReadingPurpose) -> List[CodeSection]:
        """Group relevant lines into meaningful code sections."""
        sections = []
        
        if not relevant_indices:
            return sections
        
        # Group consecutive lines with some context
        current_group = [relevant_indices[0]]
        
        for i in range(1, len(relevant_indices)):
            if relevant_indices[i] - relevant_indices[i-1] <= 5:  # Within 5 lines
                current_group.append(relevant_indices[i])
            else:
                # Create section from current group
                section = self._create_code_section(current_group, lines, purpose)
                if section:
                    sections.append(section)
                current_group = [relevant_indices[i]]
        
        # Handle last group
        if current_group:
            section = self._create_code_section(current_group, lines, purpose)
            if section:
                sections.append(section)
        
        return sections
    
    def _create_code_section(self, line_indices: List[int], lines: List[str], 
                           purpose: ReadingPurpose) -> Optional[CodeSection]:
        """Create a code section from line indices."""
        if not line_indices:
            return None
        
        # Add context around the relevant lines
        start_line = max(0, min(line_indices) - 2)
        end_line = min(len(lines), max(line_indices) + 3)
        
        section_lines = lines[start_line:end_line]
        content = '\n'.join(section_lines)
        
        # Determine context type
        context_type = self._determine_context_type(content, purpose)
        
        # Extract key elements
        key_elements = self._extract_key_elements(content, purpose)
        
        # Generate insights
        insights = self._generate_section_insights(content, purpose, context_type)
        
        # Calculate relevance
        relevance = self._calculate_section_relevance(content, purpose)
        
        return CodeSection(
            content=content,
            start_line=start_line + 1,  # 1-based line numbers
            end_line=end_line,
            purpose_relevance=relevance,
            context_type=context_type,
            key_elements=key_elements,
            insights=insights
        )
    
    def _determine_context_type(self, content: str, purpose: ReadingPurpose) -> str:
        """Determine the type of code context."""
        content_lower = content.lower()
        
        if 'def ' in content or 'function ' in content:
            return 'function'
        elif 'class ' in content:
            return 'class'
        elif any(keyword in content_lower for keyword in ['import', 'require', 'include']):
            return 'imports'
        elif any(keyword in content_lower for keyword in ['route', 'endpoint', 'api']):
            return 'api_endpoint'
        elif any(keyword in content_lower for keyword in ['try', 'except', 'catch']):
            return 'error_handling'
        else:
            return 'code_block'
    
    def _extract_key_elements(self, content: str, purpose: ReadingPurpose) -> List[str]:
        """Extract key elements from the code section."""
        elements = []
        
        if purpose == ReadingPurpose.UNDERSTAND_FUNCTION:
            # Extract function names, parameters, return values
            func_matches = re.findall(r'def\s+(\w+)\s*\([^)]*\)', content)
            elements.extend([f"Function: {func}" for func in func_matches])
            
            return_matches = re.findall(r'return\s+([^;\n]+)', content)
            elements.extend([f"Returns: {ret.strip()}" for ret in return_matches])
        
        elif purpose == ReadingPurpose.EXTRACT_API_ENDPOINTS:
            # Extract API routes and methods
            route_matches = re.findall(r'@\w+\.(get|post|put|delete)\(["\']([^"\']+)["\']', content)
            elements.extend([f"{method.upper()} {route}" for method, route in route_matches])
        
        elif purpose == ReadingPurpose.FIND_SECURITY_ISSUES:
            # Extract potential security issues
            if 'password' in content.lower():
                elements.append("Contains password-related code")
            if 'token' in content.lower():
                elements.append("Contains token-related code")
            if re.search(r'exec\s*\(|eval\s*\(', content):
                elements.append("Contains code execution functions")
        
        return elements
    
    def _generate_section_insights(self, content: str, purpose: ReadingPurpose, 
                                 context_type: str) -> List[str]:
        """Generate insights about the code section."""
        insights = []
        
        # Basic insights
        lines_count = len(content.split('\n'))
        insights.append(f"Code section with {lines_count} lines ({context_type})")
        
        # Purpose-specific insights
        if purpose == ReadingPurpose.UNDERSTAND_FUNCTION:
            if 'async' in content:
                insights.append("Asynchronous function")
            if 'yield' in content:
                insights.append("Generator function")
        
        elif purpose == ReadingPurpose.FIND_SECURITY_ISSUES:
            if re.search(r'password\s*=\s*["\'][^"\']+["\']', content):
                insights.append("⚠️ Potential hardcoded password")
            if re.search(r'sql.*\+', content, re.IGNORECASE):
                insights.append("⚠️ Potential SQL injection vulnerability")
        
        elif purpose == ReadingPurpose.UNDERSTAND_ERROR_HANDLING:
            try_count = len(re.findall(r'try\s*:', content))
            except_count = len(re.findall(r'except\s+', content))
            if try_count > 0:
                insights.append(f"Contains {try_count} try blocks and {except_count} exception handlers")
        
        return insights
    
    def _calculate_section_relevance(self, content: str, purpose: ReadingPurpose) -> float:
        """Calculate how relevant a section is to the reading purpose."""
        purpose_config = self.purpose_patterns.get(purpose, {})
        keywords = purpose_config.get('keywords', [])
        patterns = purpose_config.get('patterns', [])
        
        relevance_score = 0.0
        content_lower = content.lower()
        
        # Keyword matching
        for keyword in keywords:
            if keyword.lower() in content_lower:
                relevance_score += 0.1
        
        # Pattern matching
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                relevance_score += 0.2
        
        return min(1.0, relevance_score)
    
    async def _analyze_python_code(self, content: str, sections: List[CodeSection], 
                                 purpose: ReadingPurpose) -> List[CodeSection]:
        """Analyze Python code with AST for deeper understanding."""
        try:
            tree = ast.parse(content)
            
            # Enhance sections with AST analysis
            for section in sections:
                try:
                    section_tree = ast.parse(section.content)
                    
                    # Extract additional information using AST
                    if purpose == ReadingPurpose.UNDERSTAND_FUNCTION:
                        functions = [node.name for node in ast.walk(section_tree) 
                                   if isinstance(node, ast.FunctionDef)]
                        section.key_elements.extend([f"AST Function: {func}" for func in functions])
                    
                    elif purpose == ReadingPurpose.TRACE_DATA_FLOW:
                        assignments = [node.targets[0].id for node in ast.walk(section_tree) 
                                     if isinstance(node, ast.Assign) and 
                                     isinstance(node.targets[0], ast.Name)]
                        section.key_elements.extend([f"Variable: {var}" for var in assignments])
                
                except SyntaxError:
                    # If section can't be parsed, skip AST analysis
                    pass
            
            return sections
            
        except SyntaxError:
            # If full file can't be parsed, return sections as-is
            return sections
    
    async def _analyze_javascript_code(self, content: str, sections: List[CodeSection], 
                                     purpose: ReadingPurpose) -> List[CodeSection]:
        """Analyze JavaScript code for deeper understanding."""
        # For now, return sections as-is
        # In a full implementation, we'd use a JavaScript parser
        return sections
    
    async def _analyze_typescript_code(self, content: str, sections: List[CodeSection], 
                                     purpose: ReadingPurpose) -> List[CodeSection]:
        """Analyze TypeScript code for deeper understanding."""
        return sections
    
    async def _analyze_java_code(self, content: str, sections: List[CodeSection], 
                                purpose: ReadingPurpose) -> List[CodeSection]:
        """Analyze Java code for deeper understanding."""
        return sections
    
    def _generate_summary(self, sections: List[CodeSection], purpose: ReadingPurpose) -> str:
        """Generate a summary of the reading results."""
        if not sections:
            return f"No relevant code found for {purpose.value}"
        
        total_lines = sum(len(section.content.split('\n')) for section in sections)
        avg_relevance = sum(section.purpose_relevance for section in sections) / len(sections)
        
        context_types = [section.context_type for section in sections]
        unique_contexts = list(set(context_types))
        
        summary = f"Found {len(sections)} relevant code sections ({total_lines} lines total) "
        summary += f"with average relevance of {avg_relevance:.2f}. "
        summary += f"Context types: {', '.join(unique_contexts)}."
        
        return summary
    
    def _extract_key_insights(self, sections: List[CodeSection], purpose: ReadingPurpose) -> List[str]:
        """Extract key insights from all sections."""
        all_insights = []
        
        for section in sections:
            all_insights.extend(section.insights)
        
        # Remove duplicates while preserving order
        unique_insights = []
        seen = set()
        for insight in all_insights:
            if insight not in seen:
                unique_insights.append(insight)
                seen.add(insight)
        
        return unique_insights[:10]  # Return top 10 insights
    
    def _generate_recommendations(self, sections: List[CodeSection], purpose: ReadingPurpose) -> List[str]:
        """Generate recommendations based on the analysis."""
        recommendations = []
        
        if not sections:
            recommendations.append("Consider broadening the search criteria or checking related files")
            return recommendations
        
        # Purpose-specific recommendations
        if purpose == ReadingPurpose.FIND_SECURITY_ISSUES:
            security_issues = [s for s in sections if any('⚠️' in insight for insight in s.insights)]
            if security_issues:
                recommendations.append("Review identified security concerns and implement proper safeguards")
            else:
                recommendations.append("No obvious security issues found, but consider a deeper security audit")
        
        elif purpose == ReadingPurpose.UNDERSTAND_FUNCTION:
            complex_functions = [s for s in sections if len(s.content.split('\n')) > 20]
            if complex_functions:
                recommendations.append("Consider breaking down complex functions for better maintainability")
        
        elif purpose == ReadingPurpose.EXTRACT_API_ENDPOINTS:
            if sections:
                recommendations.append("Document the identified API endpoints and their expected inputs/outputs")
        
        # General recommendations
        high_relevance_sections = [s for s in sections if s.purpose_relevance > 0.7]
        if high_relevance_sections:
            recommendations.append(f"Focus on {len(high_relevance_sections)} highly relevant sections for deeper analysis")
        
        return recommendations
    
    def _calculate_confidence_score(self, sections: List[CodeSection]) -> float:
        """Calculate confidence score for the reading results."""
        if not sections:
            return 0.0
        
        # Base confidence on relevance scores and number of sections
        avg_relevance = sum(section.purpose_relevance for section in sections) / len(sections)
        section_count_factor = min(1.0, len(sections) / 5)  # Normalize to max 5 sections
        
        confidence = (avg_relevance * 0.7) + (section_count_factor * 0.3)
        
        return min(1.0, confidence)
    
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