import unittest
import os
import inspect
from jinja2 import Template
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
    
    def test_inception(self):
        # Get the contents of the current test file
        current_file_path = inspect.getfile(inspect.currentframe())
        with open(current_file_path, 'r') as f:
            test_file_contents = f.read()

        # Get the contents of the ResponseParsers.py file
        response_parsers_path = os.path.join(os.path.dirname(os.path.dirname(current_file_path)), 'AbstractAI', 'Helpers', 'ResponseParsers.py')
        with open(response_parsers_path, 'r') as f:
            response_parsers_contents = f.read()

        # Define the Jinja2 template
        template_string = """
This is some random text to start our inception test.

/path/to/test_file
```python
{{ test_file_contents }}
```

Here's some more random text between code blocks.

/path/to/response_parsers
```python
{{ response_parsers_contents }}
```

And here's some final random text to conclude our inception test.
"""

        # Render the template
        template = Template(template_string)
        rendered_markdown = template.render(
            test_file_contents=test_file_contents,
            response_parsers_contents=response_parsers_contents
        )

        # Extract paths and code from the rendered markdown
        extracted_paths_and_code = extract_paths_and_code(rendered_markdown)

        # Assert that we extracted two code blocks
        self.assertEqual(len(extracted_paths_and_code), 2)

        # Assert that the extracted paths are correct
        self.assertEqual(extracted_paths_and_code[0][0], '/path/to/test_file')
        self.assertEqual(extracted_paths_and_code[1][0], '/path/to/response_parsers')

        # Assert that the extracted code contents match the original file contents
        self.assertEqual(extracted_paths_and_code[0][1].strip(), test_file_contents.strip())
        self.assertEqual(extracted_paths_and_code[1][1].strip(), response_parsers_contents.strip())

if __name__ == '__main__':
    unittest.main()