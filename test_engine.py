import unittest
from src.exec_python import import_functions, import_variables, execute_python_code, extract_python_code

# Define static test variables
IMPORT_FUNCS_STR = """
def get_coordinates() -> Tuple[int, int]:
    return (10, 20)
"""

WORKING_CODE = """
coords_1 = get_coordinates()
coords_2 = get_coordinates()
a = 1
b = 2
"""

UNSAFE_CODE = """
exec("print('This should not execute')")
"""

LONG_RUNNING_CODE = """
import time
time.sleep(15)
"""

INVALID_IMPORT_FUNCS_STR = """
# No function definitions
x = 42
"""

CONTEXT_VARIABLES = {
    "test_var": 42
}

CONTEXT_VARIABLES_STR = """
test_var = 42
"""

CODE_WITH_CONTEXT_VARIABLES = """
test_var_2 = test_var + 1
"""

CUSTOM_EXCLUDED_BUILTINS = ["print"]

CODE_WITH_CUSTOM_EXCLUDED_BUILTINS = """
print("This should be blocked")
x = len([1, 2, 3])  
"""

STRING_WITH_SINGLE_CODE_BLOCK = """
```python
x = [1, 2, 3]
```
"""

STRING_WITH_MULTIPLE_CODE_BLOCKS = """
some llm output
```python
x = [1, 2, 3]
```
some more llm output
```python
y = [4, 5, 6]
```
even more llm output
"""

# Define test class
class TestExecutePythonCode(unittest.TestCase):
    def setUp(self):
        """
        Set up the test environment by importing functions from the provided string.
        """
        self.mock_functions = import_functions(IMPORT_FUNCS_STR)
    
    def test_execute_safe_code(self):
        result = execute_python_code(
            code=WORKING_CODE,
            functions=self.mock_functions,
            safe=True
        )
        expected_function_results = {
            "get_coordinates": ["coords_1", "coords_2"]
        }
        expected_variables = {
            "coords_1": (10, 20),
            "coords_2": (10, 20),
            "a": 1,
            "b": 2
        }
        self.assertEqual(result.errors, [])
        self.assertEqual(result.variables, expected_variables)
        self.assertEqual(result.function_results, expected_function_results)
    
    def test_execute_unsafe_code(self):
        result = execute_python_code(
            code=UNSAFE_CODE,
            functions=self.mock_functions,
            safe=True
        )
        self.assertIn("NotAllowedError: Usage of dangerous builtin 'exec' is not allowed", result.errors)
        self.assertEqual(result.variables, {})
        self.assertEqual(result.function_results, {})
    
    def test_execution_timeout(self):
        result = execute_python_code(
            code=LONG_RUNNING_CODE,
            functions=self.mock_functions,
            safe=True
        )
        self.assertIn("Code execution exceeded timeout limit.", result.errors)
        self.assertIn("time", result.variables)
        self.assertEqual(len(result.variables), 1)
        self.assertEqual(result.function_results, {})
    
    def test_invalid_functions_import(self):
        with self.assertRaises(ValueError) as context:
            import_functions(INVALID_IMPORT_FUNCS_STR)
        self.assertEqual(str(context.exception), "No functions found in the provided mock functions string")
        
    def test_context_variables(self):
        result = execute_python_code(
            code=CODE_WITH_CONTEXT_VARIABLES,
            functions=self.mock_functions,
            context_variables=CONTEXT_VARIABLES,
            safe=True
        )
        self.assertEqual(result.variables, {"test_var_2": 43})

        result_2 = execute_python_code(
            code=CODE_WITH_CONTEXT_VARIABLES,
            functions=self.mock_functions,
            context_variables=import_variables(CONTEXT_VARIABLES_STR),
            safe=True
        )
        self.assertEqual(result_2.variables, {"test_var_2": 43})

    def test_custom_excluded_builtins(self):
        result = execute_python_code(
            code=CODE_WITH_CUSTOM_EXCLUDED_BUILTINS,
            functions=self.mock_functions,
            excluded_builtins=CUSTOM_EXCLUDED_BUILTINS,
            safe=True
        )
        self.assertIn("NotAllowedError: Usage of dangerous builtin 'print' is not allowed", result.errors)

class TestExtractPythonCode(unittest.TestCase):
    def test_extract_single_code_block(self):
        self.assertEqual(extract_python_code(STRING_WITH_SINGLE_CODE_BLOCK), "x = [1, 2, 3]\n")
    
    def test_extract_multiple_code_blocks(self):
        self.assertEqual(extract_python_code(STRING_WITH_MULTIPLE_CODE_BLOCKS), "x = [1, 2, 3]\ny = [4, 5, 6]\n")
    
if __name__ == "__main__":
    unittest.main()