import pandas as pd
import csv
import subprocess
import os


fname = 'dataset.csv'
x = pd.read_csv(fname, delimiter=';', quoting=csv.QUOTE_NONE)

urls = x['URL']
for url in urls:
    name = url.split('/')[-1]
    repo_local = f'cloned/{name}'
    if not os.path.exists(repo_local):
        subprocess.run(['git', 'clone', url, repo_local])

