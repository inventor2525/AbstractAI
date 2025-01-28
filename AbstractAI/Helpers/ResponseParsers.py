from dataclasses import dataclass
from typing import List, Optional, Union, Tuple
import re
import os

@dataclass
class MarkdownCodeBlockInfo:
    language: str
    content: str
    path: Optional[str] = None

def extract_code_blocks(text: str) -> List[Union[MarkdownCodeBlockInfo, str]]:
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
    
    other_lines = []
    
    file_name:str = None
    looking_for_file_end = False
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if depth == 0:
            if re.match(path_pattern, line):
                path = line.strip()
            elif re.match(code_start_pattern, line):
                depth = 1
                language = re.match(code_start_pattern, line).group(1) or "text"
                if path is None:
                    looking_for_file_end = False
                else:
                    file_name = os.path.basename(path)
                    looking_for_file_end = f"\n`"+"``\n{file_name}\n" in text
                    #Parser still can't handle the above line ^ without the "+" in the middle of the ` ` `
                
                if len(other_lines)>0:
                    code_blocks.append("\n".join(other_lines))
                    other_lines.clear()
            else:
                if path is not None:
                    other_lines.append(path)
                other_lines.append(line)
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
                def is_it_actually():
                    if looking_for_file_end:
                        return lines[i+1] == file_name
                    return True
                if could_this_be_the_end() and is_it_actually():
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
    if len(other_lines)>0:
        code_blocks.append("\n".join(other_lines))
    return code_blocks

def extract_paths_and_code(x:List[Union[MarkdownCodeBlockInfo, str]]) -> List[Tuple[str,str]]:
    '''Legacy method usage support'''
    code_blocks = [cb for cb in extract_code_blocks(x) if isinstance(cb, MarkdownCodeBlockInfo)]
    return [(code_block.path, code_block.content) for code_block in code_blocks if code_block.path]