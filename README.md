# exec-python

Minimal engine to execute python code generated by LLMs, with a lot of customisation options.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (for development & testing)

## Installation

```bash
pip install exec-python 
```

## Running the tests

```bash
uv run test_engine.py
```


## Usage

### Quick Start 

```python
from exec_python import execute_python_code, import_functions

functions = """
def pair_sum(x: List[int], y: List[int]) -> List[int]:
    return x + y
"""

code = """
x = [1, 2]
y = [2, 3]
z = pair_sum(x, y)
k = pair_sum(z, z)
"""

results = execute_python_code(
    code = code,
    functions=import_functions(functions),
)
print(results)
```
Running the above code will output:

```
{
  "function_results": {
    "pair_sum": ["z","k"]
  },
  "variables": {
    "x": [1,2],
    "y": [2,3],
    "z": [1,2,2,3],
    "k": [1,2,2,3,1,2,2,3]
  },
  "errors": []
}
```
