import ast
import operator

__all__ = ['safe_eval']

# Binary operators mapping
_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

def safe_eval(expr):
    """
    Safely evaluate simple math expressions like '2+3*4-(5/2)'.
    Supports: numbers, +, -, *, /, %, **, parentheses.
    Blocks: variables, functions, imports, etc.
    """
    try:
        tree = ast.parse(expr, mode='eval')
        
        if not isinstance(tree.body, ast.Expression):
            raise ValueError("Only simple expressions allowed")
            
        return _eval_node(tree.body.body)
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError) as e:
        raise ValueError(f"Invalid math expression: {e}")

def _eval_node(node):
    """Recursively evaluate safe AST nodes."""
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        op_func = _BINARY_OPS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op_func(left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        if isinstance(node.op, ast.USub):
            return -operand
        elif isinstance(node.op, ast.UAdd):
            return operand
        raise ValueError(f"Unsupported unary: {type(node.op).__name__}")
    elif isinstance(node, ast.Num):  # Legacy Python 3.7-
        return node.n
    else:
        raise ValueError(f"Unsupported node: {type(node).__name__}")

