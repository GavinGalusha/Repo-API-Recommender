#!/usr/bin/env python3
"""
Read dataset csv file released in https://dl.acm.org/doi/10.1145/3643991.3644890
and clone each repository. These are later used to parse REST API endpoints
with LLMs.
"""

import csv
import subprocess
import os
import pandas as pd

FNAME = 'dataset.csv'
x = pd.read_csv(FNAME, delimiter=';', quoting=csv.QUOTE_NONE)

urls = x['URL']
for url in urls:
    username = url.split('/')[-2]
    repo_name = url.split('/')[-1]
    repo = f'git@github.com:{username}/{repo_name}.git'
    repo_local = f'cloned/{repo_name}'
    if not os.path.exists(repo_local):
        subprocess.run(['git', 'clone', repo, repo_local])
