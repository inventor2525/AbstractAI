import re
from typing import List, Tuple

def extract_paths_and_code(text: str) -> List[Tuple[str, str]]:
    '''
    Extracts code blocks prefaced by paths
    '''
    path_pattern = r'^/[^\n]+$'
    code_start_pattern = r'^```\w+$'
    code_end_pattern = r'^```$'
    nested_code_start_pattern = r'(?<!`)```(?:python|txt|rust|cpp|javascript|java|ruby|go|typescript|csharp|php|swift|kotlin|scala|haskell|r|matlab|sql|html|css|xml|json|yaml|toml|bash|sh|powershell|markdown)(?!`)'
    nested_code_pattern = r'(?!````.*$)```(?!`)'

    path_and_codes = []
    depth = 0
    fuzzy_depth = 0
    path = None
    code = ""

    lines = text.split('\n')
    for i, line in enumerate(lines):
        if depth == 0:
            if re.match(path_pattern, line):
                path = line.strip()
            elif path and re.match(code_start_pattern, line):
                depth = 1
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
                    path_and_codes.append((path, code.strip()))
                    path = None
                    code = ""
                    depth = 0
                    fuzzy_depth = 0
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

    return path_and_codes