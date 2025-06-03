import os
from springboot_regex import get_springboot_regex


# extract text of class using bracket stack
def get_class_text(text, match_obj):
    start = match_obj.start()

    i = match_obj.end()
    brace_count = 0
    while i < len(text):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                return text[start:i+1]
        i += 1
    return text[start:]


# walk directory and get java package classes
def print_files_in_dir_nested(directory):
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".java"):
                with open(os.path.join(root, filename)) as f:
                    text = f.read().strip()
                    matches = get_springboot_regex(text, API_only=True)
                    for match in matches:
                        if not match:
                            continue
                        class_block = get_class_text(text, match)
                        print(class_block)
                continue
            else:
                continue


cwd = os.getcwd()
print_files_in_dir_nested(cwd)
