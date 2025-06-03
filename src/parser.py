import os
from springboot_regex import get_springboot_regex


def print_files_in_dir_nested(directory):
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".java"):
                with open(os.path.join(root, filename)) as f:
                    text = f.read().strip()
                    endpoint, repo, service, controller = get_springboot_regex(text)
                    for x in (endpoint, repo, service, controller):
                        if x:
                            print(x)
                continue
            else:
                continue


cwd = os.getcwd()
print_files_in_dir_nested(cwd)
