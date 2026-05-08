import ast
import operator

__all__ = ["safe_eval"]

# Limits to reduce abuse / denial-of-service vectors.
_MAX_EXPR_LEN = 128  # characters
_MAX_EXPONENT_ABS = 20  # disallow extremely large powers
_MAX_RESULT_ABS = 1e12  # prevent huge intermediate/ex final results
_MAX_STEPS = 2000  # cap evaluation recursion workload

# Binary operators mapping
_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}


def safe_eval(expr: str):
    """
    Safely evaluate simple math expressions like '2+3*4-(5/2)'.

    AST-only evaluator:
    - Supports: numbers, +, -, *, /, %, **, parentheses
    - Blocks: variables, functions, imports, attribute access, etc.

    Security hardening:
    - Limits expression length
    - Limits exponent magnitude for '**'
    - Caps absolute result magnitude
    - Caps evaluation steps
    """
    if not isinstance(expr, str):
        raise ValueError("Expression must be a string")
    if len(expr) > _MAX_EXPR_LEN:
        raise ValueError("Expression too long")

    try:
        tree = ast.parse(expr, mode="eval")
        # ast.parse(..., mode="eval") returns ast.Expression
        if not isinstance(tree, ast.Expression):
            raise ValueError("Only simple expressions allowed")

        steps = {"count": 0}
        result = _eval_node(tree.body, steps=steps)
        if abs(result) > _MAX_RESULT_ABS:
            raise ValueError("Result out of bounds")
        return result
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError) as e:
        raise ValueError(f"Invalid math expression: {e}")


def _eval_node(node, *, steps: dict):
    """Recursively evaluate safe AST nodes with step counting + result bounds."""
    steps["count"] += 1
    if steps["count"] > _MAX_STEPS:
        raise ValueError("Expression too complex")

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric constants are allowed")

    if isinstance(node, ast.Num):  # Legacy Python 3.7-
        return node.n

    if isinstance(node, ast.BinOp):
        # Special-case pow (**): enforce exponent magnitude.
        if isinstance(node.op, ast.Pow):
            left = _eval_node(node.left, steps=steps)
            right = _eval_node(node.right, steps=steps)
            if not isinstance(right, (int, float)):
                raise ValueError("Invalid exponent")

            # Disallow huge exponent magnitude.
            if abs(right) > _MAX_EXPONENT_ABS:
                raise ValueError("Exponent out of bounds")

            result = operator.pow(left, right)
            if abs(result) > _MAX_RESULT_ABS:
                raise ValueError("Result out of bounds")
            return result

        left = _eval_node(node.left, steps=steps)
        right = _eval_node(node.right, steps=steps)
        op_func = _BINARY_OPS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")

        result = op_func(left, right)
        if abs(result) > _MAX_RESULT_ABS:
            raise ValueError("Result out of bounds")
        return result

    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand, steps=steps)
        if isinstance(node.op, ast.USub):
            result = -operand
        elif isinstance(node.op, ast.UAdd):
            result = operand
        else:
            raise ValueError(f"Unsupported unary: {type(node.op).__name__}")

        if abs(result) > _MAX_RESULT_ABS:
            raise ValueError("Result out of bounds")
        return result

    raise ValueError(f"Unsupported node: {type(node).__name__}")
