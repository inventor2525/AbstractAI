import unittest
from AbstractAI.Helpers.ResponseParsers import extract_paths_and_code

class TestExtractPathsAndCode(unittest.TestCase):
    def test_extract_paths_and_code(self):
        text = r"""
This is some text.

/path/to/a/place
```python
my_str = "```python"
my_str += r'''some nested code\n
more\n
```
That was some markdown. Cool, eh?'''
print(my_str)
```

More text here.

/another/path
```javascript
console.log("Hello, world!");
```

Even more text.

```python
This block should be ignored because it has no path.
```
"""
        expected_path_and_codes = [
            (
                '/path/to/a/place',
                'my_str = "```python"\n'
                "my_str += r'''some nested code\\n\n"
                "more\\n\n"
                "```\n"
                "That was some markdown. Cool, eh?'''\n"
                'print(my_str)'
            ),
            (
                '/another/path',
                'console.log("Hello, world!");'
            )
        ]

        path_and_codes = extract_paths_and_code(text)

        self.assertEqual(path_and_codes, expected_path_and_codes)

    def test_nested_code_blocks(self):
        text = r"""
/nested/code/example
```python
def nested_function():
    print("This is a nested function")
    
    nested_code = ```
    This is a nested code block
    It should be included in the output
    ```
    
    print(nested_code)
```
"""
        expected_path_and_codes = [
            (
                '/nested/code/example',
                'def nested_function():\n'
                '    print("This is a nested function")\n'
                '    \n'
                '    nested_code = ```\n'
                '    This is a nested code block\n'
                '    It should be included in the output\n'
                '    ```\n'
                '    \n'
                '    print(nested_code)'
            )
        ]

        path_and_codes = extract_paths_and_code(text)

        self.assertEqual(path_and_codes, expected_path_and_codes)

    def test_no_valid_blocks(self):
        text = r"""
This is some text without any valid code blocks.

/path/without/code/block

```python
This block has no path, so it should be ignored.
```
"""
        expected_path_and_codes = []

        path_and_codes = extract_paths_and_code(text)

        self.assertEqual(path_and_codes, expected_path_and_codes)

if __name__ == '__main__':
    unittest.main()