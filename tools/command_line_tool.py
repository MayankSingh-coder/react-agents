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
    
    def __init__(self, working_directory: Optional[str] = None, timeout: int = 30):
        super().__init__(
            name="command_line",
            description=self._get_detailed_description()
        )
        self.working_directory = working_directory or os.getcwd()
        self.timeout = timeout
        self.system = platform.system().lower()
    
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
- Working directory isolation
- Output size limits

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
            
            # Security check
            security_check = self._security_check(command)
            if not security_check["allowed"]:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Command blocked for security: {security_check['reason']}"
                )
            
            # Execute the command
            result = await self._execute_command(command)
            
            return ToolResult(
                success=result["success"],
                data={
                    "command": command,
                    "stdout": result["stdout"],
                    "stderr": result["stderr"],
                    "return_code": result["return_code"],
                    "execution_time": result["execution_time"],
                    "working_directory": self.working_directory
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
    
    async def _execute_command(self, command: str) -> Dict[str, Any]:
        """Execute the command asynchronously with timeout."""
        import time
        start_time = time.time()
        
        try:
            # Create subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_directory,
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
                self.working_directory = os.path.abspath(directory)
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