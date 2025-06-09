import pandas as pd
import csv
import subprocess
import os


fname = 'dataset.csv'
x = pd.read_csv(fname, delimiter=';', quoting=csv.QUOTE_NONE)

urls = x['URL']
for url in urls:
    username = url.split('/')[-2]
    repo_name = url.split('/')[-1]
    repo = f'git@github.com:{username}/{repo_name}.git'
    repo_local = f'cloned/{repo_name}'
    if not os.path.exists(repo_local):
        subprocess.run(['git', 'clone', repo, repo_local])
