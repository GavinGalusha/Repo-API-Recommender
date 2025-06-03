import os
from springboot_regex import get_endpoint_regex


def print_files_in_dir_nested(directory):
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".java"):
                with open(os.path.join(root, filename)) as f:
                    text = f.read().strip()
                    c, r, u, d = get_endpoint_regex(text)
                    for x in [c,r,u,d]:
                        if x:
                            print(x)
                continue
            else:
                continue


cwd = os.getcwd()
print_files_in_dir_nested(cwd)
