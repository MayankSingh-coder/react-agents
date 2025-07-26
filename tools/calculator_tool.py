"""Calculator tool for the React Agent."""

import ast
import operator
import math
from typing import Any, Dict
from .base_tool import BaseTool, ToolResult


class CalculatorTool(BaseTool):
    """Tool for performing mathematical calculations."""
    
    # Supported operators
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.BitXor: operator.xor,
        ast.USub: operator.neg,
    }
    
    # Supported functions
    FUNCTIONS = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'log': math.log,
        'log10': math.log10,
        'exp': math.exp,
        'pi': math.pi,
        'e': math.e,
    }
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Perform mathematical calculations including basic arithmetic, trigonometry, and common math functions"
        )
    
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """Execute mathematical calculation."""
        try:
            # Clean the query
            expression = query.strip()
            
            # Handle special cases
            if expression.lower() in ['pi', 'π']:
                return ToolResult(
                    success=True,
                    data={"expression": expression, "result": math.pi},
                    metadata={"type": "constant"}
                )
            elif expression.lower() == 'e':
                return ToolResult(
                    success=True,
                    data={"expression": expression, "result": math.e},
                    metadata={"type": "constant"}
                )
            
            # Evaluate the expression
            result = self._safe_eval(expression)
            
            return ToolResult(
                success=True,
                data={
                    "expression": expression,
                    "result": result
                },
                metadata={"type": "calculation"}
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Calculation failed: {str(e)}"
            )
    
    def _safe_eval(self, expression: str) -> float:
        """Safely evaluate a mathematical expression."""
        try:
            # Parse the expression into an AST
            node = ast.parse(expression, mode='eval')
            return self._eval_node(node.body)
        except Exception as e:
            raise ValueError(f"Invalid expression: {expression}") from e
    
    def _eval_node(self, node) -> float:
        """Recursively evaluate AST nodes."""
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op = self.OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op = self.OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return op(operand)
        elif isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else None
            if func_name not in self.FUNCTIONS:
                raise ValueError(f"Unsupported function: {func_name}")
            
            func = self.FUNCTIONS[func_name]
            args = [self._eval_node(arg) for arg in node.args]
            
            return func(*args)
        elif isinstance(node, ast.Name):
            # Handle constants
            if node.id in self.FUNCTIONS:
                return self.FUNCTIONS[node.id]
            else:
                raise ValueError(f"Unsupported variable: {node.id}")
        else:
            raise ValueError(f"Unsupported node type: {type(node).__name__}")
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's input schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Mathematical expression to calculate. Supports +, -, *, /, **, (), and functions like sqrt, sin, cos, tan, log, exp, abs, round, min, max, sum. Constants: pi, e"
                }
            },
            "required": ["query"],
            "examples": [
                "2 + 3 * 4",
                "sqrt(16)",
                "sin(pi/2)",
                "log(e)",
                "2**3 + 5",
                "abs(-10)",
                "round(3.14159, 2)"
            ]
        }