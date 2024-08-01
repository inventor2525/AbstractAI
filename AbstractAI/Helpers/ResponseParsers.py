import re

def extract_paths_and_code(text):
    '''
    Extracts code blocks prefaced by paths
    '''
    path_pattern = r'^/[^\n]+$'
    code_start_pattern = r'^```\w+$'
    code_end_pattern = r'^```$'
    nested_code_start_pattern = r'(?<!`)```(?:python|rust|cpp|javascript|java|ruby|go|typescript|csharp|php|swift|kotlin|scala|haskell|r|matlab|sql|html|css|xml|json|yaml|toml|bash|sh|powershell)(?!`)'
    nested_code_pattern = r'(?!````.*$)```(?!`)'

    path_and_codes = []
    depth = 0
    fuzzy_depth = 0
    path = None
    code = ""

    lines = text.split('\n')
    for i, line in enumerate(lines):
        if re.match(path_pattern, line) and depth == 0:
            path = line.strip()
        elif path and depth == 0 and re.match(code_start_pattern, line):
            depth = 1
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
            elif re.search(nested_code_start_pattern, line):
                depth += 1
                code += line + "\n"
            elif re.search(nested_code_pattern, line):
                fuzzy_depth += 1
                code += line + "\n"
            else:
                code += line + "\n"
        else:
            path = None

    return path_and_codes