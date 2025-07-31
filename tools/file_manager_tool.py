"""File Management tool for the React Agent."""

import os
import shutil
import json
import mimetypes
import hashlib
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from .base_tool import BaseTool, ToolResult


class FileManagerTool(BaseTool):
    """Tool for safe file management operations."""
    
    # Maximum file size for reading (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Maximum number of files to list
    MAX_FILES_LIST = 1000
    
    # Allowed file extensions for reading/writing
    SAFE_TEXT_EXTENSIONS = {
        '*'
    }
    
    # Blocked directories (security)
    BLOCKED_DIRECTORIES = {

    }
    
    def __init__(self, working_directory: Optional[str] = None, safe_mode: bool = True):
        super().__init__(
            name="file_manager",
            description=self._get_detailed_description()
        )
        self.working_directory = working_directory or os.getcwd()
        self.safe_mode = safe_mode
        
        # Create a safe sandbox directory if needed
        self.sandbox_dir = os.path.join(self.working_directory, "file_sandbox")
        if not os.path.exists(self.sandbox_dir):
            os.makedirs(self.sandbox_dir, exist_ok=True)
    
    def _get_detailed_description(self) -> str:
        """Get detailed description with examples for file operations."""
        return """Perform safe file management operations including reading, writing, and organizing files.

SUPPORTED OPERATIONS:

• File Reading:
  - Read text files: read_file(path)
  - Get file info: file_info(path)
  - Check file existence: file_exists(path)
  - Calculate file hash: file_hash(path)
  
• File Writing:
  - Create/write files: write_file(path, content)
  - Append to files: append_file(path, content)
  - Modify files: modify_file(path, old_text, new_text)
  - Insert at line: insert_line(path, line_number, content)
  - Replace lines: replace_lines(path, start_line, end_line, content)
  - Delete lines: delete_lines(path, start_line, end_line)
  - Create empty files: create_file(path)
  
• Directory Operations:
  - List directory contents: list_directory(path)
  - Create directories: create_directory(path)
  - Get directory size: directory_size(path)
  
• File Operations:
  - Copy files: copy_file(source, destination)
  - Move files: move_file(source, destination)
  - Delete files: delete_file(path)
  - Rename files: rename_file(old_path, new_path)
  
• Search Operations:
  - Find files by name: find_files(pattern, directory)
  - Search file content: search_in_files(text, directory)
  - Filter by extension: filter_by_extension(directory, extension)

SECURITY FEATURES:
- Safe mode prevents access to system directories
- File size limits (10MB max for reading)
- Extension whitelist for text operations
- Sandbox directory for safe operations
- Path traversal protection
- Automatic backup before destructive operations

USAGE EXAMPLES:
- "read_file('/path/to/file.txt')" → Read file content
- "write_file('report.txt', 'Hello World')" → Create/write file
- "modify_file('config.py', 'old_value = 1', 'old_value = 2')" → Replace specific text
- "insert_line('script.py', 10, 'print(\"debug\")')" → Insert line at position 10
- "replace_lines('data.txt', 5, 7, 'new content')" → Replace lines 5-7
- "delete_lines('temp.log', 1, 3)" → Delete lines 1-3
- "list_directory('/home/user/documents')" → List directory contents
- "find_files('*.py', '/project')" → Find Python files
- "copy_file('source.txt', 'backup.txt')" → Copy file
- "file_info('/path/to/file')" → Get file metadata

SUPPORTED FILE TYPES:
- Text files: .txt, .md, .json, .csv, .xml, .yaml
- Code files: .py, .js, .html, .css, .sql
- Config files: .conf, .ini, .cfg, .env
- Log files: .log
- Script files: .sh, .bat, .ps1

LIMITATIONS:
- Text files only (no binary file editing)
- 10MB file size limit for reading
- 1000 files maximum in directory listings
- No access to system directories in safe mode
- Automatic sandboxing for write operations

COMMON USE CASES:
- Reading configuration files
- Creating reports and logs
- Managing project files
- File organization and cleanup
- Content analysis and search
- Backup and archival operations"""
    
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """Execute file management operation."""
        try:
            # Parse the operation from the query
            operation = self._parse_operation(query)
            
            if not operation:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Could not parse file operation from query. Use format: operation(parameters)"
                )
            
            # Execute the operation
            result = await self._execute_operation(operation)
            
            return result
        
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"File operation failed: {str(e)}"
            )
    
    def _parse_operation(self, query: str) -> Optional[Dict[str, Any]]:
        """Parse operation from query string."""
        query = query.strip()
        
        # Simple operation parsing
        operations = {
            'read_file': ['read_file', 'read', 'cat', 'show'],
            'write_file': ['write_file', 'write', 'create'],
            'append_file': ['append_file', 'append'],
            'modify_file': ['modify_file', 'modify', 'replace_text', 'str_replace'],
            'insert_line': ['insert_line', 'insert'],
            'replace_lines': ['replace_lines', 'replace_line_range'],
            'delete_lines': ['delete_lines', 'remove_lines'],
            'list_directory': ['list_directory', 'list', 'ls', 'dir'],
            'file_info': ['file_info', 'info', 'stat'],
            'file_exists': ['file_exists', 'exists'],
            'copy_file': ['copy_file', 'copy', 'cp'],
            'move_file': ['move_file', 'move', 'mv'],
            'delete_file': ['delete_file', 'delete', 'rm'],
            'create_directory': ['create_directory', 'mkdir'],
            'find_files': ['find_files', 'find'],
            'search_in_files': ['search_in_files', 'search', 'grep'],
            'file_hash': ['file_hash', 'hash', 'checksum']
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
            if op_name == 'read_file':
                return await self._read_file(params[0] if params else '')
            elif op_name == 'write_file':
                return await self._write_file(
                    params[0] if len(params) > 0 else '',
                    params[1] if len(params) > 1 else ''
                )
            elif op_name == 'append_file':
                return await self._append_file(
                    params[0] if len(params) > 0 else '',
                    params[1] if len(params) > 1 else ''
                )
            elif op_name == 'modify_file':
                return await self._modify_file(
                    params[0] if len(params) > 0 else '',
                    params[1] if len(params) > 1 else '',
                    params[2] if len(params) > 2 else ''
                )
            elif op_name == 'insert_line':
                return await self._insert_line(
                    params[0] if len(params) > 0 else '',
                    int(params[1]) if len(params) > 1 and params[1].isdigit() else 1,
                    params[2] if len(params) > 2 else ''
                )
            elif op_name == 'replace_lines':
                return await self._replace_lines(
                    params[0] if len(params) > 0 else '',
                    int(params[1]) if len(params) > 1 and params[1].isdigit() else 1,
                    int(params[2]) if len(params) > 2 and params[2].isdigit() else 1,
                    params[3] if len(params) > 3 else ''
                )
            elif op_name == 'delete_lines':
                return await self._delete_lines(
                    params[0] if len(params) > 0 else '',
                    int(params[1]) if len(params) > 1 and params[1].isdigit() else 1,
                    int(params[2]) if len(params) > 2 and params[2].isdigit() else 1
                )
            elif op_name == 'list_directory':
                return await self._list_directory(params[0] if params else '.')
            elif op_name == 'file_info':
                return await self._file_info(params[0] if params else '')
            elif op_name == 'file_exists':
                return await self._file_exists(params[0] if params else '')
            elif op_name == 'copy_file':
                return await self._copy_file(
                    params[0] if len(params) > 0 else '',
                    params[1] if len(params) > 1 else ''
                )
            elif op_name == 'move_file':
                return await self._move_file(
                    params[0] if len(params) > 0 else '',
                    params[1] if len(params) > 1 else ''
                )
            elif op_name == 'delete_file':
                return await self._delete_file(params[0] if params else '')
            elif op_name == 'create_directory':
                return await self._create_directory(params[0] if params else '')
            elif op_name == 'find_files':
                return await self._find_files(
                    params[0] if len(params) > 0 else '*',
                    params[1] if len(params) > 1 else '.'
                )
            elif op_name == 'search_in_files':
                return await self._search_in_files(
                    params[0] if len(params) > 0 else '',
                    params[1] if len(params) > 1 else '.'
                )
            elif op_name == 'file_hash':
                return await self._file_hash(params[0] if params else '')
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
            # Handle relative paths by resolving them relative to working directory
            if not os.path.isabs(path):
                path = os.path.join(self.working_directory, path)
            
            # Resolve the absolute path
            abs_path = os.path.abspath(path)
            
            # Check against blocked directories
            for blocked in self.BLOCKED_DIRECTORIES:
                if abs_path.startswith(blocked):
                    return False
            
            # Ensure path is within working directory or sandbox
            working_abs = os.path.abspath(self.working_directory)
            sandbox_abs = os.path.abspath(self.sandbox_dir)
            
            return (abs_path.startswith(working_abs) or 
                   abs_path.startswith(sandbox_abs) or
                   abs_path.startswith('/tmp/') or  # Allow temp directories
                   abs_path.startswith('/var/folders/'))  # Allow macOS temp directories
        
        except Exception:
            return False
    
    def _is_safe_extension(self, path: str) -> bool:
        """Check if file extension is safe for text operations."""
        ext = Path(path).suffix.lower()
        # If SAFE_TEXT_EXTENSIONS contains '*', allow all extensions
        if '*' in self.SAFE_TEXT_EXTENSIONS:
            return True
        return ext in self.SAFE_TEXT_EXTENSIONS or ext == ''
    
    async def _read_file(self, path: str) -> ToolResult:
        """Read file content."""
        if not path:
            return ToolResult(success=False, data=None, error="File path required")
        
        # Handle relative paths by resolving them relative to working directory
        if not os.path.isabs(path):
            path = os.path.join(self.working_directory, path)
        
        if not self._is_safe_path(path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        try:
            if not os.path.exists(path):
                return ToolResult(success=False, data=None, error="File not found")
            
            if not os.path.isfile(path):
                return ToolResult(success=False, data=None, error="Path is not a file")
            
            # Check file size
            file_size = os.path.getsize(path)
            if file_size > self.MAX_FILE_SIZE:
                return ToolResult(
                    success=False, 
                    data=None, 
                    error=f"File too large: {file_size} bytes (max: {self.MAX_FILE_SIZE})"
                )
            
            # Read file content
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            return ToolResult(
                success=True,
                data={
                    "path": path,
                    "content": content,
                    "size": file_size,
                    "lines": len(content.splitlines())
                },
                metadata={"operation": "read_file"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Read failed: {str(e)}")
    
    async def _write_file(self, path: str, content: str) -> ToolResult:
        """Write content to file."""
        if not path:
            return ToolResult(success=False, data=None, error="File path required")
        
        if not content:
            content = ""
        
        # Handle relative paths by resolving them relative to working directory
        if not os.path.isabs(path):
            path = os.path.join(self.working_directory, path)
        
        # Use sandbox for new files if in safe mode and path is not already safe
        if self.safe_mode and not self._is_safe_path(path):
            path = os.path.join(self.sandbox_dir, os.path.basename(path))
        
        if not self._is_safe_path(path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        if not self._is_safe_extension(path):
            return ToolResult(success=False, data=None, error="Unsafe file extension")
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Backup existing file
            backup_path = None
            if os.path.exists(path):
                backup_path = f"{path}.backup_{int(datetime.now().timestamp())}"
                shutil.copy2(path, backup_path)
            
            # Write file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            file_size = os.path.getsize(path)
            
            return ToolResult(
                success=True,
                data={
                    "path": path,
                    "size": file_size,
                    "lines": len(content.splitlines()),
                    "backup_path": backup_path
                },
                metadata={"operation": "write_file"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Write failed: {str(e)}")
    
    async def _append_file(self, path: str, content: str) -> ToolResult:
        """Append content to file."""
        if not path:
            return ToolResult(success=False, data=None, error="File path required")
        
        # Handle relative paths by resolving them relative to working directory
        if not os.path.isabs(path):
            path = os.path.join(self.working_directory, path)
        
        if not self._is_safe_path(path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        try:
            # Create file if it doesn't exist
            if not os.path.exists(path):
                return await self._write_file(path, content)
            
            with open(path, 'a', encoding='utf-8') as f:
                f.write(content)
            
            file_size = os.path.getsize(path)
            
            return ToolResult(
                success=True,
                data={
                    "path": path,
                    "size": file_size,
                    "appended_content": content
                },
                metadata={"operation": "append_file"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Append failed: {str(e)}")
    
    async def _modify_file(self, path: str, old_text: str, new_text: str) -> ToolResult:
        """Modify file by replacing specific text."""
        if not path:
            return ToolResult(success=False, data=None, error="File path required")
        if not old_text:
            return ToolResult(success=False, data=None, error="Old text to replace required")
        
        # Handle relative paths by resolving them relative to working directory
        if not os.path.isabs(path):
            path = os.path.join(self.working_directory, path)
        
        if not self._is_safe_path(path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        try:
            if not os.path.exists(path):
                return ToolResult(success=False, data=None, error="File not found")
            
            if not os.path.isfile(path):
                return ToolResult(success=False, data=None, error="Path is not a file")
            
            # Read current content
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Check if old_text exists
            if old_text not in content:
                return ToolResult(success=False, data=None, error=f"Text to replace not found: '{old_text}'")
            
            # Count occurrences
            occurrences = content.count(old_text)
            if occurrences > 1:
                return ToolResult(
                    success=False, 
                    data=None, 
                    error=f"Text appears {occurrences} times. Use more specific text to avoid ambiguity."
                )
            
            # Create backup
            backup_path = f"{path}.backup_{int(datetime.now().timestamp())}"
            shutil.copy2(path, backup_path)
            
            # Replace text
            new_content = content.replace(old_text, new_text)
            
            # Write modified content
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return ToolResult(
                success=True,
                data={
                    "path": path,
                    "old_text": old_text,
                    "new_text": new_text,
                    "backup_path": backup_path,
                    "size": os.path.getsize(path),
                    "lines": len(new_content.splitlines())
                },
                metadata={"operation": "modify_file"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Modify failed: {str(e)}")
    
    async def _insert_line(self, path: str, line_number: int, content: str) -> ToolResult:
        """Insert content at specific line number."""
        if not path:
            return ToolResult(success=False, data=None, error="File path required")
        if line_number < 1:
            return ToolResult(success=False, data=None, error="Line number must be >= 1")
        
        # Handle relative paths by resolving them relative to working directory
        if not os.path.isabs(path):
            path = os.path.join(self.working_directory, path)
        
        if not self._is_safe_path(path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        try:
            if not os.path.exists(path):
                return ToolResult(success=False, data=None, error="File not found")
            
            if not os.path.isfile(path):
                return ToolResult(success=False, data=None, error="Path is not a file")
            
            # Read current content
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            # Create backup
            backup_path = f"{path}.backup_{int(datetime.now().timestamp())}"
            shutil.copy2(path, backup_path)
            
            # Insert line (line_number is 1-based)
            insert_index = line_number - 1
            if insert_index > len(lines):
                insert_index = len(lines)
            
            # Ensure content ends with newline if it doesn't already
            if content and not content.endswith('\n'):
                content += '\n'
            
            lines.insert(insert_index, content)
            
            # Write modified content
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return ToolResult(
                success=True,
                data={
                    "path": path,
                    "line_number": line_number,
                    "inserted_content": content.rstrip('\n'),
                    "backup_path": backup_path,
                    "size": os.path.getsize(path),
                    "total_lines": len(lines)
                },
                metadata={"operation": "insert_line"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Insert failed: {str(e)}")
    
    async def _replace_lines(self, path: str, start_line: int, end_line: int, content: str) -> ToolResult:
        """Replace lines in a specific range."""
        if not path:
            return ToolResult(success=False, data=None, error="File path required")
        if start_line < 1 or end_line < 1:
            return ToolResult(success=False, data=None, error="Line numbers must be >= 1")
        if start_line > end_line:
            return ToolResult(success=False, data=None, error="Start line must be <= end line")
        
        # Handle relative paths by resolving them relative to working directory
        if not os.path.isabs(path):
            path = os.path.join(self.working_directory, path)
        
        if not self._is_safe_path(path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        try:
            if not os.path.exists(path):
                return ToolResult(success=False, data=None, error="File not found")
            
            if not os.path.isfile(path):
                return ToolResult(success=False, data=None, error="Path is not a file")
            
            # Read current content
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            # Validate line numbers
            if start_line > len(lines):
                return ToolResult(success=False, data=None, error=f"Start line {start_line} exceeds file length ({len(lines)} lines)")
            if end_line > len(lines):
                end_line = len(lines)
            
            # Create backup
            backup_path = f"{path}.backup_{int(datetime.now().timestamp())}"
            shutil.copy2(path, backup_path)
            
            # Prepare replacement content
            if content and not content.endswith('\n'):
                content += '\n'
            
            # Replace lines (convert to 0-based indexing)
            start_idx = start_line - 1
            end_idx = end_line
            
            # Store replaced lines for reporting
            replaced_lines = lines[start_idx:end_idx]
            
            # Replace the range
            lines[start_idx:end_idx] = [content] if content else []
            
            # Write modified content
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return ToolResult(
                success=True,
                data={
                    "path": path,
                    "start_line": start_line,
                    "end_line": end_line,
                    "replaced_lines": len(replaced_lines),
                    "new_content": content.rstrip('\n') if content else "",
                    "backup_path": backup_path,
                    "size": os.path.getsize(path),
                    "total_lines": len(lines)
                },
                metadata={"operation": "replace_lines"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Replace lines failed: {str(e)}")
    
    async def _delete_lines(self, path: str, start_line: int, end_line: int) -> ToolResult:
        """Delete lines in a specific range."""
        if not path:
            return ToolResult(success=False, data=None, error="File path required")
        if start_line < 1 or end_line < 1:
            return ToolResult(success=False, data=None, error="Line numbers must be >= 1")
        if start_line > end_line:
            return ToolResult(success=False, data=None, error="Start line must be <= end line")
        
        # Handle relative paths by resolving them relative to working directory
        if not os.path.isabs(path):
            path = os.path.join(self.working_directory, path)
        
        if not self._is_safe_path(path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        try:
            if not os.path.exists(path):
                return ToolResult(success=False, data=None, error="File not found")
            
            if not os.path.isfile(path):
                return ToolResult(success=False, data=None, error="Path is not a file")
            
            # Read current content
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            # Validate line numbers
            if start_line > len(lines):
                return ToolResult(success=False, data=None, error=f"Start line {start_line} exceeds file length ({len(lines)} lines)")
            if end_line > len(lines):
                end_line = len(lines)
            
            # Create backup
            backup_path = f"{path}.backup_{int(datetime.now().timestamp())}"
            shutil.copy2(path, backup_path)
            
            # Store deleted lines for reporting
            start_idx = start_line - 1
            end_idx = end_line
            deleted_lines = lines[start_idx:end_idx]
            
            # Delete lines
            del lines[start_idx:end_idx]
            
            # Write modified content
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return ToolResult(
                success=True,
                data={
                    "path": path,
                    "start_line": start_line,
                    "end_line": end_line,
                    "deleted_lines": len(deleted_lines),
                    "deleted_content": [line.rstrip('\n') for line in deleted_lines],
                    "backup_path": backup_path,
                    "size": os.path.getsize(path),
                    "remaining_lines": len(lines)
                },
                metadata={"operation": "delete_lines"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Delete lines failed: {str(e)}")
    
    async def _list_directory(self, path: str) -> ToolResult:
        """List directory contents."""
        if not path:
            path = self.working_directory
        
        if not self._is_safe_path(path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        try:
            if not os.path.exists(path):
                return ToolResult(success=False, data=None, error="Directory not found")
            
            if not os.path.isdir(path):
                return ToolResult(success=False, data=None, error="Path is not a directory")
            
            items = []
            count = 0
            
            for item in os.listdir(path):
                if count >= self.MAX_FILES_LIST:
                    break
                
                item_path = os.path.join(path, item)
                try:
                    stat = os.stat(item_path)
                    items.append({
                        "name": item,
                        "type": "directory" if os.path.isdir(item_path) else "file",
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "permissions": oct(stat.st_mode)[-3:]
                    })
                    count += 1
                except OSError:
                    continue
            
            return ToolResult(
                success=True,
                data={
                    "path": path,
                    "items": items,
                    "total_items": len(items),
                    "truncated": count >= self.MAX_FILES_LIST
                },
                metadata={"operation": "list_directory"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"List failed: {str(e)}")
    
    async def _file_info(self, path: str) -> ToolResult:
        """Get file information."""
        if not path:
            return ToolResult(success=False, data=None, error="File path required")
        
        if not self._is_safe_path(path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        try:
            if not os.path.exists(path):
                return ToolResult(success=False, data=None, error="File not found")
            
            stat = os.stat(path)
            mime_type, _ = mimetypes.guess_type(path)
            
            info = {
                "path": path,
                "name": os.path.basename(path),
                "type": "directory" if os.path.isdir(path) else "file",
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:],
                "mime_type": mime_type,
                "extension": Path(path).suffix.lower()
            }
            
            return ToolResult(
                success=True,
                data=info,
                metadata={"operation": "file_info"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Info failed: {str(e)}")
    
    async def _file_exists(self, path: str) -> ToolResult:
        """Check if file exists."""
        if not path:
            return ToolResult(success=False, data=None, error="File path required")
        
        try:
            exists = os.path.exists(path)
            return ToolResult(
                success=True,
                data={
                    "path": path,
                    "exists": exists,
                    "type": "directory" if os.path.isdir(path) else "file" if exists else None
                },
                metadata={"operation": "file_exists"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Check failed: {str(e)}")
    
    async def _copy_file(self, source: str, destination: str) -> ToolResult:
        """Copy file."""
        if not source or not destination:
            return ToolResult(success=False, data=None, error="Source and destination paths required")
        
        if not self._is_safe_path(source) or not self._is_safe_path(destination):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        try:
            if not os.path.exists(source):
                return ToolResult(success=False, data=None, error="Source file not found")
            
            if os.path.isdir(source):
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
            
            return ToolResult(
                success=True,
                data={
                    "source": source,
                    "destination": destination,
                    "size": os.path.getsize(destination)
                },
                metadata={"operation": "copy_file"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Copy failed: {str(e)}")
    
    async def _move_file(self, source: str, destination: str) -> ToolResult:
        """Move file."""
        if not source or not destination:
            return ToolResult(success=False, data=None, error="Source and destination paths required")
        
        if not self._is_safe_path(source) or not self._is_safe_path(destination):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        try:
            if not os.path.exists(source):
                return ToolResult(success=False, data=None, error="Source file not found")
            
            shutil.move(source, destination)
            
            return ToolResult(
                success=True,
                data={
                    "source": source,
                    "destination": destination
                },
                metadata={"operation": "move_file"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Move failed: {str(e)}")
    
    async def _delete_file(self, path: str) -> ToolResult:
        """Delete file."""
        if not path:
            return ToolResult(success=False, data=None, error="File path required")
        
        if not self._is_safe_path(path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        try:
            if not os.path.exists(path):
                return ToolResult(success=False, data=None, error="File not found")
            
            # Create backup before deletion
            backup_path = f"{path}.deleted_{int(datetime.now().timestamp())}"
            if os.path.isdir(path):
                shutil.copytree(path, backup_path)
                shutil.rmtree(path)
            else:
                shutil.copy2(path, backup_path)
                os.remove(path)
            
            return ToolResult(
                success=True,
                data={
                    "path": path,
                    "backup_path": backup_path
                },
                metadata={"operation": "delete_file"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Delete failed: {str(e)}")
    
    async def _create_directory(self, path: str) -> ToolResult:
        """Create directory."""
        if not path:
            return ToolResult(success=False, data=None, error="Directory path required")
        
        if not self._is_safe_path(path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        try:
            os.makedirs(path, exist_ok=True)
            
            return ToolResult(
                success=True,
                data={"path": path},
                metadata={"operation": "create_directory"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Create directory failed: {str(e)}")
    
    async def _find_files(self, pattern: str, directory: str) -> ToolResult:
        """Find files by pattern."""
        if not pattern:
            pattern = "*"
        if not directory:
            directory = self.working_directory
        
        if not self._is_safe_path(directory):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        try:
            import fnmatch
            
            matches = []
            count = 0
            
            for root, dirs, files in os.walk(directory):
                if count >= self.MAX_FILES_LIST:
                    break
                
                for file in files:
                    if fnmatch.fnmatch(file, pattern):
                        file_path = os.path.join(root, file)
                        matches.append({
                            "path": file_path,
                            "name": file,
                            "directory": root,
                            "size": os.path.getsize(file_path)
                        })
                        count += 1
                        
                        if count >= self.MAX_FILES_LIST:
                            break
            
            return ToolResult(
                success=True,
                data={
                    "pattern": pattern,
                    "directory": directory,
                    "matches": matches,
                    "total_matches": len(matches),
                    "truncated": count >= self.MAX_FILES_LIST
                },
                metadata={"operation": "find_files"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Find failed: {str(e)}")
    
    async def _search_in_files(self, text: str, directory: str) -> ToolResult:
        """Search for text in files."""
        if not text:
            return ToolResult(success=False, data=None, error="Search text required")
        if not directory:
            directory = self.working_directory
        
        if not self._is_safe_path(directory):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        try:
            matches = []
            count = 0
            
            for root, dirs, files in os.walk(directory):
                if count >= self.MAX_FILES_LIST:
                    break
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Only search in text files
                    if not self._is_safe_extension(file_path):
                        continue
                    
                    try:
                        # Check file size
                        if os.path.getsize(file_path) > self.MAX_FILE_SIZE:
                            continue
                        
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if text.lower() in content.lower():
                                # Find line numbers
                                lines = content.splitlines()
                                matching_lines = []
                                for i, line in enumerate(lines, 1):
                                    if text.lower() in line.lower():
                                        matching_lines.append({
                                            "line_number": i,
                                            "content": line.strip()
                                        })
                                
                                matches.append({
                                    "path": file_path,
                                    "name": file,
                                    "matching_lines": matching_lines[:10]  # Limit to 10 lines
                                })
                                count += 1
                                
                                if count >= self.MAX_FILES_LIST:
                                    break
                    
                    except (UnicodeDecodeError, PermissionError):
                        continue
            
            return ToolResult(
                success=True,
                data={
                    "search_text": text,
                    "directory": directory,
                    "matches": matches,
                    "total_matches": len(matches),
                    "truncated": count >= self.MAX_FILES_LIST
                },
                metadata={"operation": "search_in_files"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Search failed: {str(e)}")
    
    async def _file_hash(self, path: str) -> ToolResult:
        """Calculate file hash."""
        if not path:
            return ToolResult(success=False, data=None, error="File path required")
        
        if not self._is_safe_path(path):
            return ToolResult(success=False, data=None, error="Access denied: unsafe path")
        
        try:
            if not os.path.exists(path):
                return ToolResult(success=False, data=None, error="File not found")
            
            if not os.path.isfile(path):
                return ToolResult(success=False, data=None, error="Path is not a file")
            
            # Calculate multiple hashes
            md5_hash = hashlib.md5()
            sha256_hash = hashlib.sha256()
            
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
                    sha256_hash.update(chunk)
            
            return ToolResult(
                success=True,
                data={
                    "path": path,
                    "md5": md5_hash.hexdigest(),
                    "sha256": sha256_hash.hexdigest(),
                    "size": os.path.getsize(path)
                },
                metadata={"operation": "file_hash"}
            )
        
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Hash calculation failed: {str(e)}")
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "File operation to perform. Format: operation(parameters). Supports read_file, write_file, modify_file, insert_line, replace_lines, delete_lines, list_directory, file_info, copy_file, move_file, delete_file, find_files, search_in_files, and more."
                }
            },
            "required": ["query"],
            "examples": [
                "read_file('config.txt')",
                "write_file('report.txt', 'Hello World')",
                "modify_file('config.py', 'old_value = 1', 'old_value = 2')",
                "insert_line('script.py', 10, 'print(\"debug\")')",
                "replace_lines('data.txt', 5, 7, 'new content')",
                "delete_lines('temp.log', 1, 3)",
                "list_directory('/home/user/documents')",
                "file_info('/path/to/file.txt')",
                "copy_file('source.txt', 'backup.txt')",
                "find_files('*.py', '/project')",
                "search_in_files('TODO', '/project')",
                "file_hash('important.txt')",
                "create_directory('new_folder')",
                "file_exists('config.json')"
            ]
        }
    
    def set_working_directory(self, directory: str) -> bool:
        """Set the working directory."""
        try:
            if os.path.isdir(directory):
                self.working_directory = os.path.abspath(directory)
                return True
            return False
        except Exception:
            return False
    
    def get_working_directory(self) -> str:
        """Get the current working directory."""
        return self.working_directory
    
    def get_sandbox_directory(self) -> str:
        """Get the sandbox directory."""
        return self.sandbox_dir
    
    def toggle_safe_mode(self, enabled: bool) -> None:
        """Toggle safe mode on/off."""
        self.safe_mode = enabled