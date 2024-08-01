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
    
    def test_extract_all_package_files(self):
        # Define the file extensions we want to include
        valid_extensions = ['.py', '.md', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.txt', '.rst', '.html', '.css', '.js', '.ts', '.jsx', '.tsx']
        extension_to_language = {
            '.py': 'python',
            '.md': 'markdown',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.ini': 'ini',
            '.cfg': 'ini',
            '.txt': 'text',
            '.rst': 'rst',
            '.html': 'html',
            '.css': 'css',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx'
        }
        
        # Function to get all files with valid extensions in a directory
        def get_files_with_extensions(directory):
            file_paths = []
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.endswith(ext) for ext in valid_extensions):
                        file_paths.append(os.path.join(root, file))
            return file_paths
        
        def get_package_root(package):
            """Get the root directory of a package."""
            package_path = os.path.abspath(package.__file__)
            return os.path.dirname(os.path.dirname(package_path))
        
        import AbstractAI
        import ClassyFlaskDB
        # Get the root directory of AbstractAI and ClassyFlaskDB
        abstract_ai_root = get_package_root(AbstractAI)
        classy_flask_db_root = get_package_root(ClassyFlaskDB)
        
        # Get all valid files from both packages
        abstract_ai_files = get_files_with_extensions(abstract_ai_root)
        classy_flask_db_files = get_files_with_extensions(classy_flask_db_root)

        all_files = abstract_ai_files + classy_flask_db_files

        # Read the contents of all files
        file_contents = []
        for file_path in all_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                file_contents.append((file_path, content))

        # Create a Jinja2 template for the markdown
        template_string = """
This is a large markdown file containing all code-like files from AbstractAI and ClassyFlaskDB packages.

{% for path, content in file_contents %}

some more random stuff `n code `n such
{{ path }}
```{{ extension_to_language.get(os.path.splitext(path)[1], 'text') }}
{{ content }}
```

{% endfor %}

End of the large markdown file.
"""

        # Render the template
        template = Template(template_string)
        rendered_markdown = template.render(
            file_contents=file_contents,
            extension_to_language=extension_to_language,
            os=os
        )

        # Extract paths and code from the rendered markdown
        extracted_paths_and_code = extract_paths_and_code(rendered_markdown)

        # Assert that each extracted path and code matches the original
        for (original_path, original_content), (extracted_path, extracted_content) in zip(file_contents, extracted_paths_and_code):
            self.assertEqual(extracted_path, original_path)
            self.assertEqual(extracted_content.strip(), original_content.strip())
            
        # Assert that we extracted the correct number of code blocks
        self.assertEqual(len(extracted_paths_and_code), len(file_contents))
if __name__ == '__main__':
    unittest.main()