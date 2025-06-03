import os


def print_files_in_dir_nested(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".java"):
            with open(os.path.join(directory, filename)) as f:
                text = f.read().strip()
                print(text)
            continue
        elif os.path.isdir(filename):
            print_files_in_dir_nested(filename)
        else:
            continue


cwd = os.getcwd()
print_files_in_dir_nested(cwd)
