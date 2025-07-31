"""File Explorer tool for recursive directory traversal and project exploration."""

import os
import json
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from datetime import datetime
from .base_tool import BaseTool, ToolResult


class FileExplorerTool(BaseTool):
    """Tool for recursive file system exploration and project analysis."""
    
    # Maximum depth for recursive traversal
    MAX_DEPTH = 20
    
    # Maximum number of items to return
    MAX_ITEMS = 5000
    
    # Common directories to ignore by default
    DEFAULT_IGNORE_DIRS = {
        '.git', '.svn', '.hg', '.bzr',  # Version control
        'node_modules', '__pycache__', '.pytest_cache',  # Dependencies/cache
        '.venv', 'venv', 'env', '.env',  # Virtual environments
        'build', 'dist', 'target', 'out',  # Build outputs
        '.idea', '.vscode', '.vs',  # IDE files
        'coverage', '.coverage', '.nyc_output',  # Coverage reports
        'logs', 'log', 'tmp', 'temp',  # Temporary files
        '.DS_Store', 'Thumbs.db'  # System files
    }
    
    # Common file patterns to ignore
    DEFAULT_IGNORE_FILES = {
        '*.pyc', '*.pyo', '*.pyd', '__pycache__',
        '*.class', '*.jar', '*.war',
        '*.o', '*.so', '*.dll', '*.dylib',
        '*.log', '*.tmp', '*.temp',
        '.DS_Store', 'Thumbs.db', 'desktop.ini',
        '*.min.js', '*.min.css',  # Minified files
        '*.map'  # Source maps
    }
    
    def __init__(self, working_directory: Optional[str] = None, safe_mode: bool = True, 
                 custom_ignore_dirs: Optional[Set[str]] = None, 
                 custom_ignore_files: Optional[Set[str]] = None,
                 blacklisted_paths: Optional[List[str]] = None):
        super().__init__(
            name="file_explorer",
            description=self._get_detailed_description()
        )
        self.working_directory = working_directory or os.getcwd()
        self.safe_mode = safe_mode
        
        # Custom ignore patterns
        self.custom_ignore_dirs = custom_ignore_dirs
        self.custom_ignore_files = custom_ignore_files
        
        # Blacklisted paths
        self.blacklisted_paths = set()
        if blacklisted_paths:
            for path in blacklisted_paths:
                self.blacklisted_paths.add(os.path.abspath(path))
    
    def _get_detailed_description(self) -> str:
        """Get detailed description with examples for file exploration operations."""
        return """Recursively explore file systems and analyze project structures.

SUPPORTED OPERATIONS:

• Directory Exploration:
  - Recursive tree view: explore_tree(path, max_depth=10)
  - Project structure: project_structure(path)
  - Directory summary: directory_summary(path)
  - Find directories: find_directories(pattern, root_path)
  
• File Discovery:
  - Find files by pattern: find_files_recursive(pattern, root_path)
  - Find by extension: find_by_extension(extension, root_path)
  - Find large files: find_large_files(min_size_mb, root_path)
  - Find recent files: find_recent_files(days, root_path)
  
• Project Analysis:
  - Code statistics: code_stats(project_path)
  - File type analysis: analyze_file_types(path)
  - Project dependencies: detect_dependencies(project_path)
  - Git repository info: git_info(repo_path)
  
• Advanced Search:
  - Search by content: search_content_recursive(text, root_path)
  - Find duplicates: find_duplicate_files(root_path)
  - Empty directories: find_empty_directories(root_path)
  - Broken symlinks: find_broken_symlinks(root_path)

FILTERING OPTIONS:
- Ignore patterns: Set custom ignore patterns for directories and files
- Depth control: Limit recursion depth to avoid deep traversals
- Size filters: Filter by file size (min/max)
- Date filters: Filter by modification/creation date
- Extension filters: Include/exclude specific file types

USAGE EXAMPLES:
- "explore_tree('/project')" → Show recursive directory tree
- "project_structure('/my-app')" → Analyze project structure
- "find_files_recursive('*.py', '/src')" → Find all Python files
- "code_stats('/project')" → Get code statistics
- "find_large_files(10, '/data')" → Find files larger than 10MB
- "search_content_recursive('TODO', '/src')" → Find files containing 'TODO'

SUPPORTED PROJECT TYPES:
- Python projects (requirements.txt, setup.py, pyproject.toml)
- Node.js projects (package.json, yarn.lock)
- Java projects (pom.xml, build.gradle)
- .NET projects (*.csproj, *.sln)
- Go projects (go.mod, go.sum)
- Rust projects (Cargo.toml)
- Docker projects (Dockerfile, docker-compose.yml)

FEATURES:
- Smart ignore patterns (node_modules, .git, etc.)
- File type detection and categorization
- Size and date analysis
- Symlink handling
- Git repository detection
- Dependency file recognition
- Code metrics calculation
- Duplicate file detection

LIMITATIONS:
- Maximum depth: 20 levels
- Maximum items: 5000 files/directories
- Text files only for content search
- Respects system permissions
- Safe mode prevents access to system directories"""
    
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """Execute file exploration operation."""
        try:
            # Parse the operation from the query
            operation = self._parse_operation(query)
            
            if not operation:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Could not parse exploration operation from query. Use format: operation(parameters)"
                )
            
            # Execute the operation
            result = await self._execute_operation(operation)
            
            return result
        
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"File exploration failed: {str(e)}"
            )
    
    def _parse_operation(self, query: str) -> Optional[Dict[str, Any]]:
        """Parse operation from query string."""
        query = query.strip()
        
        # Operation mapping
        operations = {
            'explore_tree': ['explore_tree', 'tree', 'show_tree'],
            'project_structure': ['project_structure', 'structure', 'analyze_project'],
            'directory_summary': ['directory_summary', 'summary', 'dir_summary'],
            'find_files_recursive': ['find_files_recursive', 'find_files', 'search_files'],
            'find_directories': ['find_directories', 'find_dirs'],
            'find_by_extension': ['find_by_extension', 'find_ext'],
            'find_large_files': ['find_large_files', 'large_files'],
            'find_recent_files': ['find_recent_files', 'recent_files'],
            'code_stats': ['code_stats', 'stats', 'code_statistics'],
            'analyze_file_types': ['analyze_file_types', 'file_types'],
            'detect_dependencies': ['detect_dependencies', 'dependencies', 'deps'],
            'git_info': ['git_info', 'git_status'],
            'search_content_recursive': ['search_content_recursive', 'search_content', 'grep_recursive'],
            'find_duplicate_files': ['find_duplicate_files', 'duplicates'],
            'find_empty_directories': ['find_empty_directories', 'empty_dirs'],
            'find_broken_symlinks': ['find_broken_symlinks', 'broken_links']
        }
        
        # Try to match operation
        for op_name, keywords in operations.items():
            for keyword in keywords:
                if query.lower().startswith(keyword.lower()):
                    # Extract parameters
                    params = self._extract_parameters(query, keyword)
                    return {
                        'operation': op_name,
                        'parameters': params
                    }
        
        return None
    
    def _extract_parameters(self, query: str, keyword: str) -> List[str]:
        """Extract parameters from query."""
        # Remove the keyword and clean up
        remaining = query[len(keyword):].strip()
        
        # Handle different parameter formats
        if remaining.startswith('(') and remaining.endswith(')'):
            # Function call format: operation(param1, param2)
            params_str = remaining[1:-1]
            params = [p.strip().strip('"\'') for p in params_str.split(',')]
        else:
            # Space-separated format: operation param1 param2
            params = [p.strip().strip('"\'') for p in remaining.split()]
        
        return [p for p in params if p]  # Remove empty parameters
    
    async def _execute_operation(self, operation: Dict[str, Any]) -> ToolResult:
        """Execute the parsed operation."""
        op_name = operation['operation']
        params = operation['parameters']
        
        try:
            if op_name == 'explore_tree':
                return await self._explore_tree(
                    params[0] if len(params) > 0 else self.working_directory,
                    int(params[1]) if len(params) > 1 and params[1].isdigit() else 10
                )
            elif op_name == 'project_structure':
                return await self._project_structure(params[0] if params else self.working_directory)
            elif op_name == 'directory_summary':
                return await self._directory_summary(params[0] if params else self.working_directory)
            elif op_name == 'find_files_recursive':
                return await self._find_files_recursive(
                    params[0] if len(params) > 0 else '*',
                    params[1] if len(params) > 1 else self.working_directory
                )
            elif op_name == 'find_directories':
                return await self._find_directories(
                    params[0] if len(params) > 0 else '*',
                    params[1] if len(params) > 1 else self.working_directory
                )
            elif op_name == 'find_by_extension':
                return await self._find_by_extension(
                    params[0] if len(params) > 0 else 'py',
                    params[1] if len(params) > 1 else self.working_directory
                )
            elif op_name == 'find_large_files':
                return await self._find_large_files(
                    float(params[0]) if len(params) > 0 and params[0].replace('.', '').isdigit() else 10.0,
                    params[1] if len(params) > 1 else self.working_directory
                )
            elif op_name == 'find_recent_files':
                return await self._find_recent_files(
                    int(params[0]) if len(params) > 0 and params[0].isdigit() else 7,
                    params[1] if len(params) > 1 else self.working_directory
                )
            elif op_name == 'code_stats':
                return await self._code_stats(params[0] if params else self.working_directory)
            elif op_name == 'analyze_file_types':
                return await self._analyze_file_types(params[0] if params else self.working_directory)
            elif op_name == 'detect_dependencies':
                return await self._detect_dependencies(params[0] if params else self.working_directory)
            elif op_name == 'git_info':
                return await self._git_info(params[0] if params else self.working_directory)
            elif op_name == 'search_content_recursive':
                return await self._search_content_recursive(
                    params[0] if len(params) > 0 else '',
                    params[1] if len(params) > 1 else self.working_directory
                )
            elif op_name == 'find_duplicate_files':
                return await self._find_duplicate_files(params[0] if params else self.working_directory)
            elif op_name == 'find_empty_directories':
                return await self._find_empty_directories(params[0] if params else self.working_directory)
            elif op_name == 'find_broken_symlinks':
                return await self._find_broken_symlinks(params[0] if params else self.working_directory)
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown operation: {op_name}"
                )
        
        except IndexError:
            return ToolResult(
                success=False,
                data=None,
                error=f"Insufficient parameters for operation: {op_name}"
            )
    
    def _is_safe_path(self, path: str) -> bool:
        """Check if path is safe to access."""
        if not self.safe_mode:
            return True
        
        try:
            # Handle relative paths
            if not os.path.isabs(path):
                if self.working_directory != '*':
                    path = os.path.join(self.working_directory, path)
                else:
                    path = os.path.abspath(path)
            
            abs_path = os.path.abspath(path)
            
            # Check blacklisted paths first
            if hasattr(self, 'blacklisted_paths'):
                for blacklisted in self.blacklisted_paths:
                    if abs_path.startswith(blacklisted):
                        return False
            
            # Allow access to any path if working_directory is '*'
            if self.working_directory == '*':
                # Allow access to most paths except system critical ones
                system_critical = ['/etc', '/boot', '/sys', '/proc', '/dev']
                for critical in system_critical:
                    if abs_path.startswith(critical):
                        return False
                return True
            
            working_abs = os.path.abspath(self.working_directory)
            
            # Allow access within working directory and common safe locations
            return (abs_path.startswith(working_abs) or
                   abs_path.startswith('/tmp/') or
                   abs_path.startswith('/var/folders/') or  # macOS temp
                   abs_path.startswith(os.path.expanduser('~/Documents/')) or
                   abs_path.startswith(os.path.expanduser('~/Desktop/')) or
                   abs_path.startswith(os.path.expanduser('~/Projects/')) or
                   abs_path.startswith(os.path.expanduser('~/Downloads/')))
        
        except Exception:
            return False
    
    def _should_ignore_dir(self, dir_name: str, custom_ignore: Optional[Set[str]] = None) -> bool:
        """Check if directory should be ignored."""
        ignore_set = custom_ignore or self.custom_ignore_dirs or self.DEFAULT_IGNORE_DIRS
        return dir_name in ignore_set or dir_name.startswith('.')
    
    def _should_ignore_file(self, file_name: str, custom_ignore: Optional[Set[str]] = None) -> bool:
        """Check if file should be ignored."""
        ignore_set = custom_ignore or self.custom_ignore_files or self.DEFAULT_IGNORE_FILES
        
        # Check exact matches
        if file_name in ignore_set:
            return True
        
        # Check pattern matches (simple glob patterns)
        import fnmatch
        for pattern in ignore_set:
            if fnmatch.fnmatch(file_name, pattern):
                return True
        
        return False
    
    async def _explore_tree(self, root_path: str, max_depth: int = 10) -> ToolResult:
        """Create a recursive tree view of the directory structure."""
        if not self._is_safe_path(root_path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        if not os.path.exists(root_path):
            return ToolResult(success=False, data=None, error="Path not found")
        
        if not os.path.isdir(root_path):
            return ToolResult(success=False, data=None, error="Path is not a directory")
        
        try:
            tree_data = []
            total_files = 0
            total_dirs = 0
            
            def build_tree(path: str, depth: int = 0, prefix: str = "") -> None:
                nonlocal total_files, total_dirs
                
                if depth > max_depth or total_files + total_dirs > self.MAX_ITEMS:
                    return
                
                try:
                    items = sorted(os.listdir(path))
                    dirs = []
                    files = []
                    
                    # Separate directories and files
                    for item in items:
                        item_path = os.path.join(path, item)
                        if os.path.isdir(item_path):
                            if not self._should_ignore_dir(item):
                                dirs.append(item)
                        else:
                            if not self._should_ignore_file(item):
                                files.append(item)
                    
                    # Process directories first
                    for i, dir_name in enumerate(dirs):
                        is_last_dir = (i == len(dirs) - 1) and len(files) == 0
                        connector = "└── " if is_last_dir else "├── "
                        tree_data.append(f"{prefix}{connector}{dir_name}/")
                        total_dirs += 1
                        
                        # Recurse into subdirectory
                        new_prefix = prefix + ("    " if is_last_dir else "│   ")
                        build_tree(os.path.join(path, dir_name), depth + 1, new_prefix)
                    
                    # Process files
                    for i, file_name in enumerate(files):
                        is_last = i == len(files) - 1
                        connector = "└── " if is_last else "├── "
                        
                        # Add file size info
                        try:
                            file_path = os.path.join(path, file_name)
                            size = os.path.getsize(file_path)
                            size_str = self._format_size(size)
                            tree_data.append(f"{prefix}{connector}{file_name} ({size_str})")
                        except:
                            tree_data.append(f"{prefix}{connector}{file_name}")
                        
                        total_files += 1
                
                except PermissionError:
                    tree_data.append(f"{prefix}├── [Permission Denied]")
                except Exception as e:
                    tree_data.append(f"{prefix}├── [Error: {str(e)}]")
            
            # Start building tree
            tree_data.append(f"{os.path.basename(root_path) or root_path}/")
            build_tree(root_path)
            
            return ToolResult(
                success=True,
                data={
                    "root_path": root_path,
                    "tree": tree_data,
                    "total_directories": total_dirs,
                    "total_files": total_files,
                    "max_depth": max_depth,
                    "truncated": total_files + total_dirs >= self.MAX_ITEMS
                },
                metadata={"operation": "explore_tree"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Tree exploration failed: {str(e)}")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"
    
    async def _project_structure(self, project_path: str) -> ToolResult:
        """Analyze and return project structure with categorization."""
        if not self._is_safe_path(project_path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        if not os.path.exists(project_path):
            return ToolResult(success=False, data=None, error="Project path not found")
        
        try:
            structure = {
                "root": project_path,
                "project_type": "unknown",
                "config_files": [],
                "source_directories": [],
                "documentation": [],
                "tests": [],
                "build_files": [],
                "dependencies": [],
                "assets": [],
                "other": []
            }
            
            # Detect project type and categorize files
            for root, dirs, files in os.walk(project_path):
                # Skip ignored directories
                dirs[:] = [d for d in dirs if not self._should_ignore_dir(d)]
                
                rel_root = os.path.relpath(root, project_path)
                
                for file in files:
                    if self._should_ignore_file(file):
                        continue
                    
                    file_path = os.path.join(rel_root, file) if rel_root != '.' else file
                    file_lower = file.lower()
                    
                    # Categorize files
                    if file in ['package.json', 'yarn.lock', 'package-lock.json']:
                        structure["project_type"] = "node.js"
                        structure["config_files"].append(file_path)
                    elif file in ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile']:
                        structure["project_type"] = "python"
                        structure["config_files"].append(file_path)
                    elif file in ['pom.xml', 'build.gradle', 'build.xml']:
                        structure["project_type"] = "java"
                        structure["config_files"].append(file_path)
                    elif file.endswith(('.csproj', '.sln', '.vbproj')):
                        structure["project_type"] = ".net"
                        structure["config_files"].append(file_path)
                    elif file in ['go.mod', 'go.sum']:
                        structure["project_type"] = "go"
                        structure["config_files"].append(file_path)
                    elif file in ['Cargo.toml', 'Cargo.lock']:
                        structure["project_type"] = "rust"
                        structure["config_files"].append(file_path)
                    elif file in ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml']:
                        structure["config_files"].append(file_path)
                    elif file_lower in ['readme.md', 'readme.txt', 'readme.rst', 'changelog.md', 'license']:
                        structure["documentation"].append(file_path)
                    elif 'test' in file_lower or 'spec' in file_lower:
                        structure["tests"].append(file_path)
                    elif file_lower in ['makefile', 'cmake', 'build.sh'] or file.endswith('.mk'):
                        structure["build_files"].append(file_path)
                    elif file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.css', '.scss', '.less')):
                        structure["assets"].append(file_path)
                    elif any(src_dir in rel_root.lower() for src_dir in ['src', 'source', 'lib', 'app']):
                        structure["source_directories"].append(file_path)
                    else:
                        structure["other"].append(file_path)
            
            # Identify source directories
            for root, dirs, files in os.walk(project_path):
                dirs[:] = [d for d in dirs if not self._should_ignore_dir(d)]
                rel_root = os.path.relpath(root, project_path)
                
                if any(src_name in rel_root.lower() for src_name in ['src', 'source', 'lib', 'app', 'components']):
                    if rel_root not in structure["source_directories"] and rel_root != '.':
                        structure["source_directories"].append(rel_root + '/')
            
            return ToolResult(
                success=True,
                data=structure,
                metadata={"operation": "project_structure"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Project structure analysis failed: {str(e)}")
    
    async def _find_files_recursive(self, pattern: str, root_path: str) -> ToolResult:
        """Find files recursively matching a pattern."""
        if not self._is_safe_path(root_path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        if not os.path.exists(root_path):
            return ToolResult(success=False, data=None, error="Root path not found")
        
        try:
            import fnmatch
            matches = []
            
            for root, dirs, files in os.walk(root_path):
                # Skip ignored directories
                dirs[:] = [d for d in dirs if not self._should_ignore_dir(d)]
                
                for file in files:
                    if self._should_ignore_file(file):
                        continue
                    
                    if fnmatch.fnmatch(file, pattern):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, root_path)
                        
                        try:
                            stat = os.stat(file_path)
                            matches.append({
                                "path": rel_path,
                                "full_path": file_path,
                                "size": stat.st_size,
                                "size_formatted": self._format_size(stat.st_size),
                                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                "extension": Path(file).suffix.lower()
                            })
                        except:
                            matches.append({
                                "path": rel_path,
                                "full_path": file_path,
                                "size": 0,
                                "size_formatted": "0B",
                                "modified": None,
                                "extension": Path(file).suffix.lower()
                            })
                        
                        if len(matches) >= self.MAX_ITEMS:
                            break
                
                if len(matches) >= self.MAX_ITEMS:
                    break
            
            return ToolResult(
                success=True,
                data={
                    "pattern": pattern,
                    "root_path": root_path,
                    "matches": matches,
                    "total_matches": len(matches),
                    "truncated": len(matches) >= self.MAX_ITEMS
                },
                metadata={"operation": "find_files_recursive"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Recursive file search failed: {str(e)}")
    
    async def _directory_summary(self, dir_path: str) -> ToolResult:
        """Get a summary of directory contents."""
        if not self._is_safe_path(dir_path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        if not os.path.exists(dir_path):
            return ToolResult(success=False, data=None, error="Directory not found")
        
        try:
            summary = {
                "path": dir_path,
                "total_files": 0,
                "total_directories": 0,
                "total_size": 0,
                "file_types": {},
                "largest_files": [],
                "recent_files": []
            }
            
            all_files = []
            
            for root, dirs, files in os.walk(dir_path):
                dirs[:] = [d for d in dirs if not self._should_ignore_dir(d)]
                summary["total_directories"] += len(dirs)
                
                for file in files:
                    if self._should_ignore_file(file):
                        continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        size = stat.st_size
                        ext = Path(file).suffix.lower() or 'no extension'
                        
                        summary["total_files"] += 1
                        summary["total_size"] += size
                        summary["file_types"][ext] = summary["file_types"].get(ext, 0) + 1
                        
                        all_files.append({
                            "path": os.path.relpath(file_path, dir_path),
                            "size": size,
                            "modified": stat.st_mtime
                        })
                    except:
                        continue
            
            # Get largest files (top 10)
            summary["largest_files"] = sorted(all_files, key=lambda x: x["size"], reverse=True)[:10]
            
            # Get most recent files (top 10)
            summary["recent_files"] = sorted(all_files, key=lambda x: x["modified"], reverse=True)[:10]
            
            # Format sizes
            summary["total_size_formatted"] = self._format_size(summary["total_size"])
            
            for file_info in summary["largest_files"]:
                file_info["size_formatted"] = self._format_size(file_info["size"])
                file_info["modified_formatted"] = datetime.fromtimestamp(file_info["modified"]).isoformat()
            
            for file_info in summary["recent_files"]:
                file_info["size_formatted"] = self._format_size(file_info["size"])
                file_info["modified_formatted"] = datetime.fromtimestamp(file_info["modified"]).isoformat()
            
            return ToolResult(
                success=True,
                data=summary,
                metadata={"operation": "directory_summary"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Directory summary failed: {str(e)}")
    
    async def _code_stats(self, project_path: str) -> ToolResult:
        """Generate code statistics for a project."""
        if not self._is_safe_path(project_path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        if not os.path.exists(project_path):
            return ToolResult(success=False, data=None, error="Project path not found")
        
        try:
            # Define code file extensions
            code_extensions = {
                '.py': 'Python',
                '.js': 'JavaScript',
                '.ts': 'TypeScript',
                '.java': 'Java',
                '.c': 'C',
                '.cpp': 'C++',
                '.h': 'C/C++ Header',
                '.cs': 'C#',
                '.go': 'Go',
                '.rs': 'Rust',
                '.php': 'PHP',
                '.rb': 'Ruby',
                '.swift': 'Swift',
                '.kt': 'Kotlin',
                '.scala': 'Scala',
                '.html': 'HTML',
                '.css': 'CSS',
                '.scss': 'SCSS',
                '.less': 'LESS',
                '.sql': 'SQL',
                '.sh': 'Shell',
                '.bat': 'Batch',
                '.ps1': 'PowerShell'
            }
            
            stats = {
                "project_path": project_path,
                "languages": {},
                "total_files": 0,
                "total_lines": 0,
                "total_size": 0,
                "largest_files": [],
                "file_distribution": {}
            }
            
            all_code_files = []
            
            for root, dirs, files in os.walk(project_path):
                dirs[:] = [d for d in dirs if not self._should_ignore_dir(d)]
                
                for file in files:
                    if self._should_ignore_file(file):
                        continue
                    
                    ext = Path(file).suffix.lower()
                    if ext not in code_extensions:
                        continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            line_count = len(lines)
                            size = os.path.getsize(file_path)
                        
                        language = code_extensions[ext]
                        if language not in stats["languages"]:
                            stats["languages"][language] = {
                                "files": 0,
                                "lines": 0,
                                "size": 0
                            }
                        
                        stats["languages"][language]["files"] += 1
                        stats["languages"][language]["lines"] += line_count
                        stats["languages"][language]["size"] += size
                        
                        stats["total_files"] += 1
                        stats["total_lines"] += line_count
                        stats["total_size"] += size
                        
                        all_code_files.append({
                            "path": os.path.relpath(file_path, project_path),
                            "language": language,
                            "lines": line_count,
                            "size": size
                        })
                    
                    except:
                        continue
            
            # Get largest files by lines
            stats["largest_files"] = sorted(all_code_files, key=lambda x: x["lines"], reverse=True)[:10]
            
            # Format sizes
            stats["total_size_formatted"] = self._format_size(stats["total_size"])
            for lang_stats in stats["languages"].values():
                lang_stats["size_formatted"] = self._format_size(lang_stats["size"])
            
            for file_info in stats["largest_files"]:
                file_info["size_formatted"] = self._format_size(file_info["size"])
            
            return ToolResult(
                success=True,
                data=stats,
                metadata={"operation": "code_stats"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Code statistics failed: {str(e)}")
    
    async def _find_large_files(self, min_size_mb: float, root_path: str) -> ToolResult:
        """Find files larger than specified size."""
        if not self._is_safe_path(root_path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        if not os.path.exists(root_path):
            return ToolResult(success=False, data=None, error="Root path not found")
        
        try:
            min_size_bytes = int(min_size_mb * 1024 * 1024)
            large_files = []
            
            for root, dirs, files in os.walk(root_path):
                dirs[:] = [d for d in dirs if not self._should_ignore_dir(d)]
                
                for file in files:
                    if self._should_ignore_file(file):
                        continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(file_path)
                        if size >= min_size_bytes:
                            stat = os.stat(file_path)
                            large_files.append({
                                "path": os.path.relpath(file_path, root_path),
                                "full_path": file_path,
                                "size": size,
                                "size_formatted": self._format_size(size),
                                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                            })
                    except:
                        continue
                    
                    if len(large_files) >= self.MAX_ITEMS:
                        break
                
                if len(large_files) >= self.MAX_ITEMS:
                    break
            
            # Sort by size (largest first)
            large_files.sort(key=lambda x: x["size"], reverse=True)
            
            return ToolResult(
                success=True,
                data={
                    "min_size_mb": min_size_mb,
                    "min_size_bytes": min_size_bytes,
                    "root_path": root_path,
                    "large_files": large_files,
                    "total_found": len(large_files),
                    "truncated": len(large_files) >= self.MAX_ITEMS
                },
                metadata={"operation": "find_large_files"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Large files search failed: {str(e)}")
    
    async def _search_content_recursive(self, search_text: str, root_path: str) -> ToolResult:
        """Search for text content recursively in files."""
        if not search_text:
            return ToolResult(success=False, data=None, error="Search text required")
        
        if not self._is_safe_path(root_path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        if not os.path.exists(root_path):
            return ToolResult(success=False, data=None, error="Root path not found")
        
        try:
            matches = []
            
            # Text file extensions to search
            text_extensions = {'.txt', '.md', '.py', '.js', '.ts', '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.log', '.sql', '.sh', '.bat', '.ps1', '.c', '.cpp', '.h', '.java', '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.scala'}
            
            for root, dirs, files in os.walk(root_path):
                dirs[:] = [d for d in dirs if not self._should_ignore_dir(d)]
                
                for file in files:
                    if self._should_ignore_file(file):
                        continue
                    
                    ext = Path(file).suffix.lower()
                    if ext not in text_extensions:
                        continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            matching_lines = []
                            
                            for i, line in enumerate(lines, 1):
                                if search_text.lower() in line.lower():
                                    matching_lines.append({
                                        "line_number": i,
                                        "content": line.strip()
                                    })
                            
                            if matching_lines:
                                matches.append({
                                    "path": os.path.relpath(file_path, root_path),
                                    "full_path": file_path,
                                    "matching_lines": matching_lines[:20],  # Limit to 20 lines per file
                                    "total_matches": len(matching_lines)
                                })
                    
                    except:
                        continue
                    
                    if len(matches) >= self.MAX_ITEMS:
                        break
                
                if len(matches) >= self.MAX_ITEMS:
                    break
            
            return ToolResult(
                success=True,
                data={
                    "search_text": search_text,
                    "root_path": root_path,
                    "matches": matches,
                    "total_files": len(matches),
                    "truncated": len(matches) >= self.MAX_ITEMS
                },
                metadata={"operation": "search_content_recursive"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Content search failed: {str(e)}")
    
    async def _find_directories(self, pattern: str, root_path: str) -> ToolResult:
        """Find directories recursively matching a pattern."""
        if not self._is_safe_path(root_path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        if not os.path.exists(root_path):
            return ToolResult(success=False, data=None, error="Root path not found")
        
        try:
            import fnmatch
            matches = []
            
            for root, dirs, files in os.walk(root_path):
                # Filter out ignored directories from traversal
                dirs[:] = [d for d in dirs if not self._should_ignore_dir(d)]
                
                for dir_name in dirs:
                    if fnmatch.fnmatch(dir_name, pattern):
                        dir_path = os.path.join(root, dir_name)
                        rel_path = os.path.relpath(dir_path, root_path)
                        
                        try:
                            stat = os.stat(dir_path)
                            # Count items in directory
                            try:
                                item_count = len(os.listdir(dir_path))
                            except:
                                item_count = 0
                            
                            matches.append({
                                "path": rel_path,
                                "full_path": dir_path,
                                "item_count": item_count,
                                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                            })
                        except:
                            matches.append({
                                "path": rel_path,
                                "full_path": dir_path,
                                "item_count": 0,
                                "modified": None
                            })
                        
                        if len(matches) >= self.MAX_ITEMS:
                            break
                
                if len(matches) >= self.MAX_ITEMS:
                    break
            
            return ToolResult(
                success=True,
                data={
                    "pattern": pattern,
                    "root_path": root_path,
                    "matches": matches,
                    "total_matches": len(matches),
                    "truncated": len(matches) >= self.MAX_ITEMS
                },
                metadata={"operation": "find_directories"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Directory search failed: {str(e)}")
    
    async def _find_by_extension(self, extension: str, root_path: str) -> ToolResult:
        """Find files by extension recursively."""
        if not extension.startswith('.'):
            extension = '.' + extension
        
        pattern = f"*{extension}"
        return await self._find_files_recursive(pattern, root_path)
    
    async def _find_recent_files(self, days: int, root_path: str) -> ToolResult:
        """Find files modified within the specified number of days."""
        if not self._is_safe_path(root_path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        if not os.path.exists(root_path):
            return ToolResult(success=False, data=None, error="Root path not found")
        
        try:
            import time
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            recent_files = []
            
            for root, dirs, files in os.walk(root_path):
                dirs[:] = [d for d in dirs if not self._should_ignore_dir(d)]
                
                for file in files:
                    if self._should_ignore_file(file):
                        continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        if stat.st_mtime >= cutoff_time:
                            recent_files.append({
                                "path": os.path.relpath(file_path, root_path),
                                "full_path": file_path,
                                "size": stat.st_size,
                                "size_formatted": self._format_size(stat.st_size),
                                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                "extension": Path(file).suffix.lower()
                            })
                    except:
                        continue
                    
                    if len(recent_files) >= self.MAX_ITEMS:
                        break
                
                if len(recent_files) >= self.MAX_ITEMS:
                    break
            
            # Sort by modification time (most recent first)
            recent_files.sort(key=lambda x: x["modified"], reverse=True)
            
            return ToolResult(
                success=True,
                data={
                    "days": days,
                    "cutoff_time": datetime.fromtimestamp(cutoff_time).isoformat(),
                    "root_path": root_path,
                    "recent_files": recent_files,
                    "total_found": len(recent_files),
                    "truncated": len(recent_files) >= self.MAX_ITEMS
                },
                metadata={"operation": "find_recent_files"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Recent files search failed: {str(e)}")
    
    async def _analyze_file_types(self, path: str) -> ToolResult:
        """Analyze file types in a directory."""
        if not self._is_safe_path(path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        if not os.path.exists(path):
            return ToolResult(success=False, data=None, error="Path not found")
        
        try:
            file_types = {}
            total_files = 0
            total_size = 0
            
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if not self._should_ignore_dir(d)]
                
                for file in files:
                    if self._should_ignore_file(file):
                        continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(file_path)
                        ext = Path(file).suffix.lower() or 'no extension'
                        
                        if ext not in file_types:
                            file_types[ext] = {
                                "count": 0,
                                "total_size": 0,
                                "avg_size": 0,
                                "largest_file": None,
                                "largest_size": 0
                            }
                        
                        file_types[ext]["count"] += 1
                        file_types[ext]["total_size"] += size
                        
                        if size > file_types[ext]["largest_size"]:
                            file_types[ext]["largest_size"] = size
                            file_types[ext]["largest_file"] = os.path.relpath(file_path, path)
                        
                        total_files += 1
                        total_size += size
                    except:
                        continue
            
            # Calculate averages and format sizes
            for ext_info in file_types.values():
                ext_info["avg_size"] = ext_info["total_size"] // ext_info["count"] if ext_info["count"] > 0 else 0
                ext_info["total_size_formatted"] = self._format_size(ext_info["total_size"])
                ext_info["avg_size_formatted"] = self._format_size(ext_info["avg_size"])
                ext_info["largest_size_formatted"] = self._format_size(ext_info["largest_size"])
            
            return ToolResult(
                success=True,
                data={
                    "path": path,
                    "file_types": file_types,
                    "total_files": total_files,
                    "total_size": total_size,
                    "total_size_formatted": self._format_size(total_size),
                    "unique_extensions": len(file_types)
                },
                metadata={"operation": "analyze_file_types"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"File type analysis failed: {str(e)}")
    
    async def _detect_dependencies(self, project_path: str) -> ToolResult:
        """Detect project dependencies and configuration files."""
        if not self._is_safe_path(project_path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        if not os.path.exists(project_path):
            return ToolResult(success=False, data=None, error="Project path not found")
        
        try:
            dependencies = {
                "project_type": "unknown",
                "dependency_files": [],
                "config_files": [],
                "build_files": [],
                "dependencies": {}
            }
            
            # Define dependency file patterns
            dependency_patterns = {
                "python": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile", "poetry.lock"],
                "node.js": ["package.json", "yarn.lock", "package-lock.json", "npm-shrinkwrap.json"],
                "java": ["pom.xml", "build.gradle", "gradle.properties", "build.xml"],
                ".net": ["*.csproj", "*.sln", "*.vbproj", "packages.config", "project.json"],
                "go": ["go.mod", "go.sum", "Gopkg.toml", "Gopkg.lock"],
                "rust": ["Cargo.toml", "Cargo.lock"],
                "php": ["composer.json", "composer.lock"],
                "ruby": ["Gemfile", "Gemfile.lock", "*.gemspec"]
            }
            
            # Search for dependency files
            for root, dirs, files in os.walk(project_path):
                dirs[:] = [d for d in dirs if not self._should_ignore_dir(d)]
                
                for file in files:
                    file_lower = file.lower()
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, project_path)
                    
                    # Check for dependency files
                    for project_type, patterns in dependency_patterns.items():
                        for pattern in patterns:
                            import fnmatch
                            if fnmatch.fnmatch(file_lower, pattern.lower()):
                                dependencies["project_type"] = project_type
                                dependencies["dependency_files"].append({
                                    "file": rel_path,
                                    "type": project_type,
                                    "pattern": pattern
                                })
                    
                    # Check for config files
                    config_patterns = ["*.config", "*.conf", "*.ini", "*.yaml", "*.yml", "*.json", "Dockerfile", "docker-compose.*"]
                    for pattern in config_patterns:
                        import fnmatch
                        if fnmatch.fnmatch(file_lower, pattern.lower()):
                            dependencies["config_files"].append(rel_path)
                    
                    # Check for build files
                    build_patterns = ["Makefile", "makefile", "build.sh", "*.mk", "CMakeLists.txt"]
                    for pattern in build_patterns:
                        import fnmatch
                        if fnmatch.fnmatch(file_lower, pattern.lower()):
                            dependencies["build_files"].append(rel_path)
            
            # Try to parse some dependency files for actual dependencies
            for dep_file in dependencies["dependency_files"]:
                file_path = os.path.join(project_path, dep_file["file"])
                try:
                    if dep_file["file"].endswith("package.json"):
                        import json
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            deps = {}
                            if "dependencies" in data:
                                deps.update(data["dependencies"])
                            if "devDependencies" in data:
                                deps.update(data["devDependencies"])
                            dependencies["dependencies"]["npm"] = deps
                    elif dep_file["file"].endswith("requirements.txt"):
                        with open(file_path, 'r') as f:
                            deps = {}
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#'):
                                    if '==' in line:
                                        name, version = line.split('==', 1)
                                        deps[name.strip()] = version.strip()
                                    else:
                                        deps[line] = "latest"
                            dependencies["dependencies"]["pip"] = deps
                except:
                    continue
            
            return ToolResult(
                success=True,
                data=dependencies,
                metadata={"operation": "detect_dependencies"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Dependency detection failed: {str(e)}")
    
    async def _git_info(self, repo_path: str) -> ToolResult:
        """Get Git repository information."""
        if not self._is_safe_path(repo_path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        if not os.path.exists(repo_path):
            return ToolResult(success=False, data=None, error="Repository path not found")
        
        try:
            git_dir = os.path.join(repo_path, '.git')
            if not os.path.exists(git_dir):
                return ToolResult(success=False, data=None, error="Not a Git repository")
            
            git_info = {
                "is_git_repo": True,
                "git_dir": git_dir,
                "repo_path": repo_path
            }
            
            # Try to read basic Git info
            try:
                # Read current branch
                head_file = os.path.join(git_dir, 'HEAD')
                if os.path.exists(head_file):
                    with open(head_file, 'r') as f:
                        head_content = f.read().strip()
                        if head_content.startswith('ref: refs/heads/'):
                            git_info["current_branch"] = head_content.replace('ref: refs/heads/', '')
                        else:
                            git_info["current_branch"] = "detached HEAD"
                
                # Check for common Git files
                git_files = ['.gitignore', '.gitmodules', 'README.md', 'LICENSE']
                git_info["git_files"] = []
                for git_file in git_files:
                    if os.path.exists(os.path.join(repo_path, git_file)):
                        git_info["git_files"].append(git_file)
                
                # Count refs (branches and tags)
                refs_dir = os.path.join(git_dir, 'refs')
                if os.path.exists(refs_dir):
                    branches_dir = os.path.join(refs_dir, 'heads')
                    tags_dir = os.path.join(refs_dir, 'tags')
                    
                    git_info["branch_count"] = len(os.listdir(branches_dir)) if os.path.exists(branches_dir) else 0
                    git_info["tag_count"] = len(os.listdir(tags_dir)) if os.path.exists(tags_dir) else 0
            
            except Exception as e:
                git_info["error"] = f"Could not read Git details: {str(e)}"
            
            return ToolResult(
                success=True,
                data=git_info,
                metadata={"operation": "git_info"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Git info failed: {str(e)}")
    
    async def _find_duplicate_files(self, root_path: str) -> ToolResult:
        """Find duplicate files based on size and content hash."""
        if not self._is_safe_path(root_path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        if not os.path.exists(root_path):
            return ToolResult(success=False, data=None, error="Root path not found")
        
        try:
            import hashlib
            file_hashes = {}
            duplicates = []
            
            for root, dirs, files in os.walk(root_path):
                dirs[:] = [d for d in dirs if not self._should_ignore_dir(d)]
                
                for file in files:
                    if self._should_ignore_file(file):
                        continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        # First check by size
                        size = os.path.getsize(file_path)
                        if size == 0:  # Skip empty files
                            continue
                        
                        # Calculate hash for files with same size
                        with open(file_path, 'rb') as f:
                            file_hash = hashlib.md5(f.read()).hexdigest()
                        
                        key = (size, file_hash)
                        if key not in file_hashes:
                            file_hashes[key] = []
                        
                        file_hashes[key].append({
                            "path": os.path.relpath(file_path, root_path),
                            "full_path": file_path,
                            "size": size,
                            "size_formatted": self._format_size(size)
                        })
                    except:
                        continue
            
            # Find duplicates
            for (size, file_hash), files in file_hashes.items():
                if len(files) > 1:
                    duplicates.append({
                        "size": size,
                        "size_formatted": self._format_size(size),
                        "hash": file_hash,
                        "files": files,
                        "duplicate_count": len(files)
                    })
            
            # Sort by size (largest first)
            duplicates.sort(key=lambda x: x["size"], reverse=True)
            
            return ToolResult(
                success=True,
                data={
                    "root_path": root_path,
                    "duplicates": duplicates,
                    "total_duplicate_groups": len(duplicates),
                    "total_duplicate_files": sum(d["duplicate_count"] for d in duplicates)
                },
                metadata={"operation": "find_duplicate_files"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Duplicate files search failed: {str(e)}")
    
    async def _find_empty_directories(self, root_path: str) -> ToolResult:
        """Find empty directories."""
        if not self._is_safe_path(root_path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        if not os.path.exists(root_path):
            return ToolResult(success=False, data=None, error="Root path not found")
        
        try:
            empty_dirs = []
            
            for root, dirs, files in os.walk(root_path, topdown=False):
                dirs[:] = [d for d in dirs if not self._should_ignore_dir(d)]
                
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if not os.listdir(dir_path):  # Directory is empty
                            empty_dirs.append({
                                "path": os.path.relpath(dir_path, root_path),
                                "full_path": dir_path,
                                "modified": datetime.fromtimestamp(os.path.getmtime(dir_path)).isoformat()
                            })
                    except:
                        continue
                    
                    if len(empty_dirs) >= self.MAX_ITEMS:
                        break
                
                if len(empty_dirs) >= self.MAX_ITEMS:
                    break
            
            return ToolResult(
                success=True,
                data={
                    "root_path": root_path,
                    "empty_directories": empty_dirs,
                    "total_found": len(empty_dirs),
                    "truncated": len(empty_dirs) >= self.MAX_ITEMS
                },
                metadata={"operation": "find_empty_directories"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Empty directories search failed: {str(e)}")
    
    async def _find_broken_symlinks(self, root_path: str) -> ToolResult:
        """Find broken symbolic links."""
        if not self._is_safe_path(root_path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        if not os.path.exists(root_path):
            return ToolResult(success=False, data=None, error="Root path not found")
        
        try:
            broken_links = []
            
            for root, dirs, files in os.walk(root_path):
                dirs[:] = [d for d in dirs if not self._should_ignore_dir(d)]
                
                # Check files for symlinks
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.islink(file_path):
                        try:
                            # This will raise an exception if the link is broken
                            os.stat(file_path)
                        except (OSError, FileNotFoundError):
                            target = os.readlink(file_path)
                            broken_links.append({
                                "path": os.path.relpath(file_path, root_path),
                                "full_path": file_path,
                                "target": target,
                                "type": "file"
                            })
                
                # Check directories for symlinks
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    if os.path.islink(dir_path):
                        try:
                            os.stat(dir_path)
                        except (OSError, FileNotFoundError):
                            target = os.readlink(dir_path)
                            broken_links.append({
                                "path": os.path.relpath(dir_path, root_path),
                                "full_path": dir_path,
                                "target": target,
                                "type": "directory"
                            })
                
                if len(broken_links) >= self.MAX_ITEMS:
                    break
            
            return ToolResult(
                success=True,
                data={
                    "root_path": root_path,
                    "broken_symlinks": broken_links,
                    "total_found": len(broken_links),
                    "truncated": len(broken_links) >= self.MAX_ITEMS
                },
                metadata={"operation": "find_broken_symlinks"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Broken symlinks search failed: {str(e)}")
    
    def set_custom_ignore_patterns(self, ignore_dirs: Optional[Set[str]] = None, ignore_files: Optional[Set[str]] = None):
        """Set custom ignore patterns for directories and files."""
        if ignore_dirs is not None:
            self.custom_ignore_dirs = ignore_dirs
        if ignore_files is not None:
            self.custom_ignore_files = ignore_files
    
    def add_to_blacklist(self, paths: List[str]):
        """Add paths to the blacklist."""
        if not hasattr(self, 'blacklisted_paths'):
            self.blacklisted_paths = set()
        
        for path in paths:
            abs_path = os.path.abspath(path)
            self.blacklisted_paths.add(abs_path)
    
    def remove_from_blacklist(self, paths: List[str]):
        """Remove paths from the blacklist."""
        if not hasattr(self, 'blacklisted_paths'):
            return
        
        for path in paths:
            abs_path = os.path.abspath(path)
            self.blacklisted_paths.discard(abs_path)
    
    def get_blacklisted_paths(self) -> Set[str]:
        """Get current blacklisted paths."""
        return getattr(self, 'blacklisted_paths', set())
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "File exploration operation to perform. Format: operation(parameters). Supports explore_tree, project_structure, find_files_recursive, code_stats, and more."
                }
            },
            "required": ["query"],
            "examples": [
                "explore_tree('/project', 5)",
                "project_structure('/my-app')",
                "find_files_recursive('*.py', '/src')",
                "code_stats('/project')",
                "find_large_files(10, '/data')",
                "search_content_recursive('TODO', '/src')",
                "analyze_file_types('/project')",
                "detect_dependencies('/project')"
            ]
        }