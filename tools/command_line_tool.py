"""Command Line tool for the React Agent."""

import subprocess
import asyncio
import os
import shlex
import platform
import tempfile
from typing import Any, Dict, List, Optional
from .base_tool import BaseTool, ToolResult


class CommandLineTool(BaseTool):
    """Tool for executing command line operations safely."""
    
    # Allowed commands for security (whitelist approach)
    SAFE_COMMANDS = {
        # File operations
        'ls', 'dir', 'pwd', 'cd', 'find', 'locate', 'which', 'whereis',
        'cat', 'head', 'tail', 'less', 'more', 'wc', 'grep', 'awk', 'sed',
        'sort', 'uniq', 'cut', 'tr', 'diff', 'cmp',
        
        # System information
        'ps', 'top', 'htop', 'df', 'du', 'free', 'uptime', 'whoami', 'id',
        'uname', 'hostname', 'date', 'cal', 'env', 'printenv',
        
        # Network utilities
        'ping', 'curl', 'wget', 'nslookup', 'dig', 'netstat', 'ss',
        
        # Text processing
        'echo', 'printf', 'basename', 'dirname',
        
        # Archive operations
        'tar', 'zip', 'unzip', 'gzip', 'gunzip',
        
        # Development tools
        'git', 'python', 'python3', 'pip', 'pip3', 'node', 'npm', 'yarn',
        'java', 'javac', 'gcc', 'g++', 'make', 'cmake',
        
        # Package managers
        'apt', 'yum', 'brew', 'pacman', 'dnf',
        
        # Docker (if needed)
        'docker', 'docker-compose',
        
        # Kubernetes (if needed)
        'kubectl', 'helm',

        # Miscellaneous
        'help','history'
    }
    
    # Dangerous commands to block
    BLOCKED_COMMANDS = {
        'rm', 'rmdir', 'del', 'format', 'fdisk', 'mkfs', 'dd',
        'shutdown', 'reboot', 'halt', 'poweroff', 'init',
        'su', 'sudo', 'passwd', 'chown', 'chmod', 'chgrp',
        'mount', 'umount', 'fsck', 'crontab',
        'kill', 'killall', 'pkill', 'xkill',
        'nc', 'netcat', 'telnet', 'ssh', 'scp', 'rsync',
        'iptables', 'ufw', 'firewall-cmd',
    }
    
    # Default prohibited directories (can be overridden)
    DEFAULT_PROHIBITED_DIRECTORIES = {
        # System directories
        '/etc', '/bin', '/sbin', '/usr/bin', '/usr/sbin', '/boot',
        '/sys', '/proc', '/dev', '/root',
        
        # macOS system directories
        '/System', '/Library', '/Applications', '/private/etc', '/private/var/log', '/private/var/run',
        
        # Windows system directories
        'C:\\Windows', 'C:\\Program Files', 'C:\\Program Files (x86)',
        'C:\\System32', 'C:\\SysWOW64',
        
        # Other sensitive directories
        '/var/log', '/var/run', '/var/lib', '/opt/local',
        '/usr/local/bin', '/usr/local/sbin'
    }
    
    def __init__(self, working_directory: Optional[str] = None, timeout: int = 30, 
                 safe_mode: bool = True, prohibited_directories: Optional[set] = None,
                 use_dynamic_cwd: bool = True):
        super().__init__(
            name="command_line",
            description=self._get_detailed_description()
        )
        self.working_directory = working_directory
        self.use_dynamic_cwd = use_dynamic_cwd
        self.timeout = timeout
        self.system = platform.system().lower()
        self.safe_mode = safe_mode
        
        # Set prohibited directories
        if prohibited_directories is not None:
            self.prohibited_directories = prohibited_directories
        else:
            self.prohibited_directories = self.DEFAULT_PROHIBITED_DIRECTORIES.copy()
        
        # If not using dynamic cwd and working directory is specified, ensure it's safe
        if not self.use_dynamic_cwd and self.working_directory:
            if self.safe_mode and not self._is_safe_working_directory():
                # Fall back to a safe directory
                safe_dir = self._get_safe_fallback_directory()
                print(f"⚠️  Working directory {self.working_directory} is not safe, using {safe_dir}")
                self.working_directory = safe_dir
    
    def _get_detailed_description(self) -> str:
        """Get detailed description with examples for command line operations."""
        return """Execute command line operations safely with security restrictions.

SUPPORTED OPERATIONS:
• File Operations:
  - List files: ls, dir (Windows)
  - View files: cat, head, tail, less
  - Search: find, grep, locate
  - Text processing: wc, sort, uniq, cut, awk, sed
  
• System Information:
  - Process info: ps, top, htop
  - Disk usage: df, du
  - Memory: free
  - System: uname, hostname, whoami, date
  
• Network Utilities:
  - Connectivity: ping, curl, wget
  - DNS: nslookup, dig
  - Network status: netstat, ss
  
• Development Tools:
  - Version control: git status, git log, git diff
  - Python: python --version, pip list, pip show
  - Node.js: node --version, npm list
  - Compilers: gcc --version, java -version
  
• Package Management:
  - Linux: apt list, yum info
  - macOS: brew list, brew info
  - Python: pip list, pip show package_name

SECURITY FEATURES:
- Whitelist of safe commands only
- Blocked dangerous operations (rm, sudo, etc.)
- Timeout protection (30 seconds default)
- Dynamic working directory detection (uses current directory by default)
- Working directory isolation and validation
- Prohibited directory path protection
- Output size limits
- Safe mode with automatic fallback directories

USAGE EXAMPLES:
- "ls -la" → List files with details
- "ps aux | grep python" → Find Python processes  
- "curl -I https://google.com" → Check website headers
- "git status" → Check git repository status
- "python --version" → Check Python version
- "df -h" → Check disk space
- "ping -c 3 google.com" → Test connectivity

LIMITATIONS:
- No destructive operations (rm, format, etc.)
- No privilege escalation (sudo, su)
- No system modification commands
- Timeout after 30 seconds
- Output limited to prevent memory issues

COMMON USE CASES:
- Check system status and resources
- Inspect files and directories
- Test network connectivity
- View process information
- Check software versions
- Basic development operations"""
    
    def _get_current_working_directory(self) -> str:
        """Get the current working directory, either dynamic or fixed."""
        if self.use_dynamic_cwd:
            return os.getcwd()
        elif self.working_directory:
            return self.working_directory
        else:
            return os.getcwd()
    
    def _is_safe_working_directory(self, working_dir: Optional[str] = None) -> bool:
        """Check if the specified working directory is safe."""
        if not self.safe_mode:
            return True
        
        try:
            if working_dir is None:
                working_dir = self._get_current_working_directory()
            
            abs_working_dir = os.path.abspath(working_dir)
            
            # Check against prohibited directories
            for prohibited in self.prohibited_directories:
                if abs_working_dir.startswith(prohibited):
                    return False
            
            return True
        except Exception:
            return False
    
    def _get_safe_fallback_directory(self) -> str:
        """Get a safe fallback directory."""
        safe_options = [
            os.path.expanduser("~"),  # User home directory
            "/tmp",  # Temp directory (Unix)
            "/var/tmp",  # Alternative temp (Unix)
            os.path.join(os.path.expanduser("~"), "Documents"),  # User documents
            os.getcwd()  # Current directory as last resort
        ]
        
        for option in safe_options:
            if os.path.exists(option) and os.path.isdir(option):
                abs_option = os.path.abspath(option)
                # Check if this directory is safe
                is_safe = True
                for prohibited in self.prohibited_directories:
                    if abs_option.startswith(prohibited):
                        is_safe = False
                        break
                
                if is_safe:
                    return abs_option
        
        # If all else fails, use temp directory
        return tempfile.gettempdir()
    
    def _is_command_path_safe(self, command: str) -> bool:
        """Check if command involves safe paths only."""
        if not self.safe_mode:
            return True
        
        # Extract potential paths from command
        import shlex
        try:
            parts = shlex.split(command)
        except ValueError:
            # If we can't parse it safely, be conservative
            return False
        
        for part in parts:
            # Skip flags and options
            if part.startswith('-'):
                continue
            
            # Check if this looks like a path
            if '/' in part or '\\' in part:
                # Resolve relative paths
                if not os.path.isabs(part):
                    current_wd = self._get_current_working_directory()
                    part = os.path.join(current_wd, part)
                
                abs_path = os.path.abspath(part)
                
                # Check against prohibited directories
                for prohibited in self.prohibited_directories:
                    if abs_path.startswith(prohibited):
                        return False
        
        return True
    
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """Execute command line operation safely."""
        try:
            # Clean and parse the command
            command = query.strip()
            if not command:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Empty command provided"
                )
            
            # Get current working directory
            current_wd = self._get_current_working_directory()
            
            # Check if current working directory is safe
            if not self._is_safe_working_directory(current_wd):
                # Fall back to a safe directory
                safe_dir = self._get_safe_fallback_directory()
                print(f"⚠️  Current working directory {current_wd} is not safe, using {safe_dir}")
                current_wd = safe_dir
            
            # Security check
            security_check = self._security_check(command)
            if not security_check["allowed"]:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Command blocked for security: {security_check['reason']}"
                )
            
            # Path safety check
            if not self._is_command_path_safe(command):
                return ToolResult(
                    success=False,
                    data=None,
                    error="Command blocked: involves prohibited directory paths"
                )
            
            # Execute the command
            result = await self._execute_command(command, working_directory=current_wd)
            
            return ToolResult(
                success=result["success"],
                data={
                    "command": command,
                    "stdout": result["stdout"],
                    "stderr": result["stderr"],
                    "return_code": result["return_code"],
                    "execution_time": result["execution_time"],
                    "working_directory": current_wd
                },
                error=result.get("error"),
                metadata={
                    "type": "command_execution",
                    "system": self.system,
                    "timeout": self.timeout
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Command execution failed: {str(e)}"
            )
    
    def _security_check(self, command: str) -> Dict[str, Any]:
        """Perform security checks on the command."""
        try:
            # Parse command to get the base command
            parts = shlex.split(command)
            if not parts:
                return {"allowed": False, "reason": "Empty command"}
            
            base_command = parts[0].lower()
            
            # Remove path if present (e.g., /usr/bin/ls -> ls)
            base_command = os.path.basename(base_command)
            
            # Check against blocked commands first
            if base_command in self.BLOCKED_COMMANDS:
                return {"allowed": False, "reason": f"Command '{base_command}' is blocked for security"}
            
            # Check against allowed commands
            if base_command not in self.SAFE_COMMANDS:
                return {"allowed": False, "reason": f"Command '{base_command}' is not in the allowed list"}
            
            # Additional security checks
            dangerous_patterns = [
                '&&', '||', ';', '|', '>', '>>', '<', '`', '$(',
                'eval', 'exec', 'system', 'shell',
            ]
            
            # Allow some safe pipe operations
            safe_pipes = ['grep', 'awk', 'sed', 'sort', 'uniq', 'head', 'tail', 'wc', 'cut']
            if '|' in command:
                # Check if it's a safe pipe operation
                pipe_parts = [part.strip().split()[0] for part in command.split('|')]
                if not all(os.path.basename(part.lower()) in self.SAFE_COMMANDS for part in pipe_parts):
                    return {"allowed": False, "reason": "Unsafe pipe operation detected"}
            
            # Check for other dangerous patterns (excluding safe pipes)
            for pattern in dangerous_patterns:
                if pattern in command and pattern != '|':
                    return {"allowed": False, "reason": f"Dangerous pattern '{pattern}' detected"}
            
            # Check command length (prevent extremely long commands)
            if len(command) > 1000:
                return {"allowed": False, "reason": "Command too long"}
            
            return {"allowed": True, "reason": "Command passed security checks"}
        
        except Exception as e:
            return {"allowed": False, "reason": f"Security check failed: {str(e)}"}
    
    async def _execute_command(self, command: str, working_directory: Optional[str] = None) -> Dict[str, Any]:
        """Execute the command asynchronously with timeout."""
        import time
        start_time = time.time()
        
        # Use provided working directory or fall back to instance working directory
        cwd = working_directory or self._get_current_working_directory()
        
        try:
            # Create subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=os.environ.copy()
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "",
                    "return_code": -1,
                    "execution_time": self.timeout,
                    "error": f"Command timed out after {self.timeout} seconds"
                }
            
            execution_time = time.time() - start_time
            
            # Decode output
            stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            # Limit output size to prevent memory issues
            max_output_size = 10000  # 10KB
            if len(stdout_text) > max_output_size:
                stdout_text = stdout_text[:max_output_size] + "\n... (output truncated)"
            if len(stderr_text) > max_output_size:
                stderr_text = stderr_text[:max_output_size] + "\n... (output truncated)"
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "return_code": process.returncode,
                "execution_time": execution_time,
                "error": stderr_text if process.returncode != 0 and stderr_text else None
            }
        
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "return_code": -1,
                "execution_time": execution_time,
                "error": f"Execution error: {str(e)}"
            }
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Command line command to execute. Must be from the allowed list of safe commands. Supports file operations, system info, network utilities, and development tools."
                }
            },
            "required": ["query"],
            "examples": [
                "ls -la",
                "ps aux",
                "df -h",
                "ping -c 3 google.com",
                "git status",
                "python --version",
                "curl -I https://httpbin.org/get",
                "find . -name '*.py'",
                "cat /etc/os-release",
                "ps aux | grep python"
            ]
        }
    
    def set_working_directory(self, directory: str) -> bool:
        """Set the working directory for command execution."""
        try:
            if os.path.isdir(directory):
                abs_directory = os.path.abspath(directory)
                
                # Check if directory is safe in safe mode
                if self.safe_mode:
                    for prohibited in self.prohibited_directories:
                        if abs_directory.startswith(prohibited):
                            return False
                
                self.working_directory = abs_directory
                return True
            return False
        except Exception:
            return False
    
    def get_working_directory(self) -> str:
        """Get the current working directory."""
        return self.working_directory
    
    def get_allowed_commands(self) -> List[str]:
        """Get list of allowed commands."""
        return sorted(list(self.SAFE_COMMANDS))
    
    def get_blocked_commands(self) -> List[str]:
        """Get list of blocked commands."""
        return sorted(list(self.BLOCKED_COMMANDS))
    
    def get_prohibited_directories(self) -> List[str]:
        """Get list of prohibited directories."""
        return sorted(list(self.prohibited_directories))
    
    def add_prohibited_directory(self, directory: str) -> bool:
        """Add a directory to the prohibited list."""
        try:
            abs_dir = os.path.abspath(directory)
            self.prohibited_directories.add(abs_dir)
            
            # If current working directory becomes prohibited, change it
            if self.safe_mode and not self._is_safe_working_directory():
                safe_dir = self._get_safe_fallback_directory()
                self.working_directory = safe_dir
                print(f"⚠️  Working directory changed to {safe_dir} due to new prohibition")
            
            return True
        except Exception:
            return False
    
    def remove_prohibited_directory(self, directory: str) -> bool:
        """Remove a directory from the prohibited list."""
        try:
            abs_dir = os.path.abspath(directory)
            if abs_dir in self.prohibited_directories:
                self.prohibited_directories.remove(abs_dir)
                return True
            return False
        except Exception:
            return False
    
    def set_prohibited_directories(self, directories: set) -> bool:
        """Set the entire prohibited directories list."""
        try:
            self.prohibited_directories = {os.path.abspath(d) for d in directories}
            
            # Check if current working directory is still safe
            if self.safe_mode and not self._is_safe_working_directory():
                safe_dir = self._get_safe_fallback_directory()
                self.working_directory = safe_dir
                print(f"⚠️  Working directory changed to {safe_dir} due to new prohibitions")
            
            return True
        except Exception:
            return False
    
    def reset_prohibited_directories(self) -> None:
        """Reset prohibited directories to default."""
        self.prohibited_directories = self.DEFAULT_PROHIBITED_DIRECTORIES.copy()
        
        # Check if current working directory is still safe
        if self.safe_mode and not self._is_safe_working_directory():
            safe_dir = self._get_safe_fallback_directory()
            self.working_directory = safe_dir
            print(f"⚠️  Working directory changed to {safe_dir} after reset")
    
    def toggle_safe_mode(self, enabled: bool) -> None:
        """Toggle safe mode on/off."""
        self.safe_mode = enabled
        
        if enabled and not self._is_safe_working_directory():
            safe_dir = self._get_safe_fallback_directory()
            self.working_directory = safe_dir
            print(f"⚠️  Safe mode enabled, working directory changed to {safe_dir}")
    
    def is_safe_mode_enabled(self) -> bool:
        """Check if safe mode is enabled."""
        return self.safe_mode