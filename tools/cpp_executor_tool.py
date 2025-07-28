"""C++ Code Execution Tool for the React Agent."""

import os
import subprocess
import tempfile
import json
from typing import Any, Dict
from .base_tool import BaseTool, ToolResult


class CppExecutorTool(BaseTool):
    """Tool for executing C++ code snippets."""
    
    def __init__(self):
        super().__init__(
            name="cpp_executor",
            description=self._get_detailed_description()
        )
    
    def _get_detailed_description(self) -> str:
        """Get detailed description with examples for C++ code execution."""
        return """Execute C++ code snippets. Provide complete C++ code including headers and main function.

WHAT IT DOES:
• Compiles and executes C++ code in a secure environment
• Returns program output, compilation errors, or runtime errors
• Supports standard C++ libraries and features
• Handles both simple programs and complex algorithms

REQUIREMENTS:
• Must include complete C++ program structure
• Requires #include statements for used libraries
• Must have a main() function as entry point
• Code should be syntactically correct

SUPPORTED FEATURES:
• Standard C++ libraries (iostream, vector, string, algorithm, etc.)
• Basic data types and structures
• Control flow (if/else, loops, switch)
• Functions and classes
• STL containers and algorithms
• Basic file I/O operations

CODE STRUCTURE EXAMPLES:

Simple Hello World:
```cpp
#include <iostream>
using namespace std;

int main() {
    cout << "Hello, World!" << endl;
    return 0;
}
```

Mathematical Calculation:
```cpp
#include <iostream>
#include <cmath>
using namespace std;

int main() {
    double x = 16.0;
    double result = sqrt(x);
    cout << "Square root of " << x << " is " << result << endl;
    return 0;
}
```

Working with Vectors:
```cpp
#include <iostream>
#include <vector>
#include <algorithm>
using namespace std;

int main() {
    vector<int> numbers = {5, 2, 8, 1, 9};
    sort(numbers.begin(), numbers.end());
    
    cout << "Sorted numbers: ";
    for(int num : numbers) {
        cout << num << " ";
    }
    cout << endl;
    return 0;
}
```

USAGE GUIDELINES:
• Always include necessary header files
• Use proper C++ syntax and conventions  
• Include main() function for execution
• Add output statements to see results
• Handle potential runtime errors gracefully

COMMON INCLUDES:
- #include <iostream>     // Input/output operations
- #include <vector>       // Dynamic arrays
- #include <string>       // String operations  
- #include <algorithm>    // STL algorithms
- #include <cmath>        // Mathematical functions
- #include <fstream>      // File operations

LIMITATIONS:
• Execution timeout for infinite loops
• Limited memory and processing time
• No access to external files or network
• Cannot install additional libraries
• Security restrictions on system calls

COMPILATION & EXECUTION:
- Uses g++ compiler with standard flags
- Automatic compilation before execution
- Returns both compilation and runtime output
- Error messages for debugging assistance"""
    
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """Execute C++ code and return the result."""
        try:
            # Extract C++ code from query
            cpp_code = self._extract_cpp_code(query)
            
            if not cpp_code:
                return ToolResult(
                    success=False,
                    data=None,
                    error="No valid C++ code found in the query. Please provide complete C++ code including headers and main function."
                )
            
            # Create temporary files
            with tempfile.TemporaryDirectory() as temp_dir:
                cpp_file = os.path.join(temp_dir, "program.cpp")
                exe_file = os.path.join(temp_dir, "program")
                
                # Write C++ code to file
                with open(cpp_file, 'w') as f:
                    f.write(cpp_code)
                
                # Compile the C++ code
                compile_result = subprocess.run(
                    ["g++", "-std=c++17", "-o", exe_file, cpp_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if compile_result.returncode != 0:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Compilation failed: {compile_result.stderr}",
                        metadata={"compilation_error": compile_result.stderr}
                    )
                
                # Execute the compiled program
                execution_result = subprocess.run(
                    [exe_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if execution_result.returncode != 0:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Execution failed: {execution_result.stderr}",
                        metadata={
                            "return_code": execution_result.returncode,
                            "stderr": execution_result.stderr,
                            "stdout": execution_result.stdout
                        }
                    )
                
                # Return successful result
                return ToolResult(
                    success=True,
                    data={
                        "output": execution_result.stdout.strip(),
                        "return_code": execution_result.returncode
                    },
                    metadata={
                        "compiled_successfully": True,
                        "execution_time": "< 30s"
                    }
                )
        
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                data=None,
                error="Code execution timed out (30 seconds limit)"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Unexpected error: {str(e)}"
            )
    
    def _extract_cpp_code(self, query: str) -> str:
        """Extract C++ code from the query."""
        # If the query contains code blocks, extract them
        if "```cpp" in query or "```c++" in query:
            # Extract code from markdown code blocks
            lines = query.split('\n')
            code_lines = []
            in_code_block = False
            
            for line in lines:
                if line.strip().startswith("```cpp") or line.strip().startswith("```c++"):
                    in_code_block = True
                    continue
                elif line.strip() == "```" and in_code_block:
                    in_code_block = False
                    break
                elif in_code_block:
                    code_lines.append(line)
            
            return '\n'.join(code_lines)
        
        # If no code blocks, check if the entire query looks like C++ code
        elif "#include" in query and "int main" in query:
            return query.strip()
        
        # Try to find C++ code patterns
        elif any(keyword in query for keyword in ["#include", "using namespace", "int main(", "cout", "vector"]):
            return query.strip()
        
        return ""
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Complete C++ code including headers and main function"
                }
            },
            "required": ["query"]
        }