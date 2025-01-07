from typing import List, Callable, Dict, Any
from types import FunctionType
import re
from .engine import IMPORT_TYPING_STRING

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

def extract_python_code(code: str) -> str:
    """
    Extract the python code block(s) from a multi-line string.
    Python code blocks are separated by ```python and ```, in 
    the markdown format.

    Args:
        code: A string containing python code blocks.
    Returns:
        A string containing the python code blocks.
    """
    # Find all python code blocks in the string
    code_blocks = re.findall(r"```python\n(.*?)```", code, re.DOTALL)
    return "\n".join(code_blocks).replace("\n\n", "\n")