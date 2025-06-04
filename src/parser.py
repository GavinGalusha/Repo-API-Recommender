import os
import re


valid_extensions = ['.py', '.java', '.js', '.ts', '.go', '.rb', '.php', '.cs']

endpoint_regex = [
    # literals
    r'["\'](/(?:api|v\d+)[^"\']*)["\']',

    # java spring
    r'@(?:Get|Post|Put|Delete|Patch)Mapping\s*\(\s*["\']([^"\']+)["\']',

    # express.js
    r'\b(?:app|router)\.(?:get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',

    # fastapi/flask
    r'\b(?:path|route)\s*\(\s*["\']([^"\']+)["\']',

    # raw http
    r'\b(?:GET|POST|PUT|DELETE|PATCH)\s+["\']?(/[^"\']+)["\']?'
]

def get_code(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in valid_extensions):
                yield os.path.join(root, file)

def get_endpoints(text):
    endpoints = set()
    for pattern in endpoint_regex:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                endpoints.add(match[-1])
            else:
                endpoints.add(match)
    return endpoints

def parse(root_directory):
    endpoints = set()
    for path in get_code(root_directory):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            cur_endpoints = get_endpoints(text)
            endpoints.update(cur_endpoints)
        except Exception as e:
            print(e)
    return endpoints


if __name__ == '__main__':
    endpoints = parse('cloned')
    with open('output.txt', 'w+') as f:
        for endpoint in endpoints:
            f.write(endpoint)
            #print(endpoint)
