from dataclasses import dataclass
from typing import List, Optional
import re

@dataclass
class MarkdownCodeBlockInfo:
    language: str
    content: str
    path: Optional[str] = None

def extract_code_blocks(text: str) -> List[MarkdownCodeBlockInfo]:
    '''
    Extracts code blocks from markdown and any path they are prefaced by.
    '''
    language_list = [
        'python', 'bash', 'sh', 'rust', 'cpp', 'javascript', 'java', 'ruby', 'go',
        'typescript', 'csharp', 'php', 'swift', 'kotlin', 'scala', 'haskell', 'r',
        'matlab', 'sql', 'html', 'css', 'xml', 'json', 'yaml', 'toml', 'powershell',
        'markdown', 'md', 'text', 'txt', 'vhdl'
    ]
    language_pattern = '|'.join(language_list)
    
    path_pattern = r'^/[^\n]+$'
    code_start_pattern = fr'^```((?:{language_pattern}))$'
    code_end_pattern = r'^```$'
    nested_code_start_pattern = fr'(?<!`)```(?:{language_pattern})(?!`)'
    nested_code_pattern = r'(?!````.*$)```(?!`)'

    code_blocks = []
    depth = 0
    fuzzy_depth = 0
    path = None
    code = ""
    language = ""

    lines = text.split('\n')
    for i, line in enumerate(lines):
        if depth == 0:
            if re.match(path_pattern, line):
                path = line.strip()
            elif re.match(code_start_pattern, line):
                depth = 1
                language = re.match(code_start_pattern, line).group(1) or "text"
            else:
                path = None
        elif depth >= 1:
            pseudo_depth = depth + fuzzy_depth
            if pseudo_depth % 2 == 1 and re.match(code_end_pattern, line):
                fuzzy_depth += 1
                def could_this_be_the_end():
                    if depth>fuzzy_depth:
                        return False
                    if (fuzzy_depth-depth) % 2 == 0:
                        return True
                    return False
                if could_this_be_the_end():
                    code_blocks.append(MarkdownCodeBlockInfo(language, code.strip(), path))
                    path = None
                    code = ""
                    depth = 0
                    fuzzy_depth = 0
                    language = ""
                else:
                    code += line + "\n"
            else:
                code += line + "\n"
                nested_start_matches = list(re.finditer(nested_code_start_pattern, line))
                nested_end_matches = list(re.finditer(nested_code_pattern, line))
                
                if nested_start_matches:
                    last_start_pos = nested_start_matches[-1].end()
                    end_after_start = any(m.start() > last_start_pos for m in nested_end_matches)
                    
                    if not end_after_start:
                        depth += 1
                elif nested_end_matches:
                    fuzzy_depth += 1

    return code_blocks

def extract_paths_and_code(x):
    '''Legacy method usage support'''
    code_blocks = extract_code_blocks(x)
    return [(code_block.path, code_block.content) for code_block in code_blocks if code_block.path]