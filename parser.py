import os
from springboot_regex import get_endpoint_regex


def print_files_in_dir_nested(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".java"):
            with open(os.path.join(directory, filename)) as f:
                text = f.read().strip()
                c, r, u, d = get_endpoint_regex(text)
                for x in [c,r,u,d]:
                    if x:
                        print(x)
            continue
        elif os.path.isdir(filename):
            print_files_in_dir_nested(filename)
        else:
            continue


cwd = os.getcwd()
print_files_in_dir_nested(cwd)
