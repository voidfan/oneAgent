"""Calculator tool for mathematical expressions."""
import ast
import math
import operator
from typing import Any

from app.tools.base import BaseTool, ToolResult


# Safe operators for expression evaluation
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

SAFE_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
}


def safe_eval(expr: str) -> Any:
    """Safely evaluate a mathematical expression."""
    tree = ast.parse(expr, mode="eval")

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Unsupported constant: {node.value}")
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            return SAFE_OPERATORS[op_type](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            return SAFE_OPERATORS[op_type](_eval(node.operand))
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in SAFE_FUNCTIONS:
                args = [_eval(arg) for arg in node.args]
                return SAFE_FUNCTIONS[node.func.id](*args)
            raise ValueError(f"Unsupported function: {ast.dump(node.func)}")
        elif isinstance(node, ast.Name):
            if node.id in SAFE_FUNCTIONS:
                return SAFE_FUNCTIONS[node.id]
            raise ValueError(f"Unsupported name: {node.id}")
        else:
            raise ValueError(f"Unsupported expression: {ast.dump(node)}")

    return _eval(tree)


class CalculatorTool(BaseTool):
    """Evaluate mathematical expressions safely."""

    name = "calculator"
    description = "Evaluate a mathematical expression. Supports basic arithmetic, sqrt, log, trigonometric functions."
    parameters_schema = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate, e.g. '2 + 3 * 4' or 'sqrt(16)'",
            },
        },
        "required": ["expression"],
    }

    async def execute(self, expression: str, **kwargs) -> ToolResult:
        try:
            result = safe_eval(expression)
            return ToolResult(success=True, output={"expression": expression, "result": result})
        except Exception as e:
            return ToolResult(success=False, error=f"Calculation error: {str(e)}")
