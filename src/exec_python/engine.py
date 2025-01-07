from typing import List, Callable, Dict, Any
import ast
from types import FunctionType
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import builtins

from pydantic import BaseModel

# Define constants
CODE_EXECUTION_TIMEOUT = 10  # seconds
IMPORT_TYPING_STRING = "from typing import List, Dict, Any, Union, Tuple, Callable, Optional"

# Define custom exception(s)
class NotAllowedError(Exception):
    """Raised when dangerous builtins are used in the code."""
    pass

class FunctionResults(BaseModel):
    """
    Results from executing functions, including return values, variables and errors.

    Attributes:
        function_results: A dictionary mapping function names to their return values.
        variables: A dictionary mapping variable names to their values.
        errors: A list of strings containing any errors that occurred during execution.
    """
    function_results: Dict[str, Any]
    variables: Dict[str, Any]
    errors: List[str]

def import_functions(functions_str: str) -> List[Callable]:
    """
    Import mock functions from a string containing function definitions and return them as callable functions.

    Args:
        functions_str: A string containing function definitions.
    Returns:
        A list of callable functions imported from the provided string.
    Raises:
        ValueError: If no functions are found in the provided string.
    """
    # Create a namespace to store the imported functions
    namespace = {}
    # Import typing functions and execute the functions_str in the namespace
    exec(IMPORT_TYPING_STRING, namespace)
    exec(functions_str, namespace)
    # Extract callable functions from the namespace
    functions = [obj for obj in namespace.values() if isinstance(obj, FunctionType)]

    if not functions:
        raise ValueError("No functions found in the provided mock functions string")
    
    return functions

def import_variables(variables_str: str) -> Dict[str, Any]:
    """
    Import variables from a string containing variable definitions and return them as a dictionary.

    Args:
        variables_str: A string containing variable definitions.
    Returns:
        A dictionary of variables imported from the provided string.
    """
    # Create a namespace to store the imported variables
    namespace = {}

    if len(variables_str) > 0:
        exec(variables_str, namespace)
        
    return namespace

def execute_python_code(
    code: str,
    functions: List[Callable] = [],
    context_variables: Dict[str, Any] = {},
    safe: bool = True,
    excluded_builtins: List[str] = []
) -> FunctionResults:
    """
    Execute Python code with given functions and context variables, and return the results.

    Args:
        code: The Python code (in string format) to execute
        functions: A list of functions to be imported to be used in the code. (Optional, default: [])
        context_variables: A dictionary of variables to be added to the execution environment. (Optional, default: {})
        safe: Whether to check for dangerous builtins and prevent execution if found. (Optional, default: True)
        excluded_builtins: A list of builtins to be excluded from the execution environment. (Optional, default: [])
    Returns:
        FunctionResults: An object containing the results of the code execution.
    """

    # Initialize environment with default builtins
    env = {"__builtins__": builtins.__dict__.copy()}
    
    if safe:
        # Define dangerous builtins
        if not excluded_builtins:
            dangerous_builtins = [
                "exec", "eval", "execfile", "compile", "exit", "input"
            ]
        else:
            dangerous_builtins = excluded_builtins

        # Check for dangerous builtin usage
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in dangerous_builtins:
                return FunctionResults(
                    function_results={},
                    variables={},
                    errors=[f"NotAllowedError: Usage of dangerous builtin '{node.id}' is not allowed"]
                )

        # Filter out dangerous builtins from environment
        env["__builtins__"] = {k: v for k, v in builtins.__dict__.items() if k not in dangerous_builtins}

    # Import typing functions and add context variables
    exec(IMPORT_TYPING_STRING, env)
    env.update(context_variables)

    # Record initial environment keys
    initial_keys = set(env.keys())

    # Dictionary to hold function call results mapped to variable names
    function_to_variable = {}

    # Parse AST to map function calls to their assignment variables
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                func_name = node.value.func.id
                var_name = node.targets[0].id
                function_to_variable.setdefault(func_name, []).append(var_name)

    # Wrap the provided functions to capture their return values
    call_results = {}

    def make_wrapper(func_name, func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            call_results.setdefault(func_name, []).append(result)
            return result
        return wrapper

    for func in functions:
        env[func.__name__] = make_wrapper(func.__name__, func)

    errors = []

    try:
        with ThreadPoolExecutor() as executor:
            future = executor.submit(exec, code, env)
            try:
                future.result(timeout=CODE_EXECUTION_TIMEOUT)
            except FuturesTimeoutError:
                errors.append("Code execution exceeded timeout limit.")
            except Exception as e:
                import traceback
                errors.append(f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}")
    except Exception as e:
        errors.append(str(e))

    # Collect variables defined in the code
    variables = {
        k: v
        for k, v in env.items()
        if k not in initial_keys and not k.startswith("__") and not callable(v)
    }

    # Create function results mapping
    function_results = {}
    for func_name, var_names in function_to_variable.items():
        function_results[func_name] = [call_results.get(func_name, [None])[i] for i in range(len(var_names))]

    return FunctionResults(
        function_results=function_results,
        variables=variables,
        errors=errors
    )