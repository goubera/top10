# Diagnosis

## Root cause
The GitHub Actions run failed in the **Install deps** step:
```
ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'
```

## Why it happens
The workflow executed commands from the repository root while the project and its `requirements.txt` live in the `solana-meme-top10-collector/` subfolder. As a result, pip could not find the file and the job exited early.

## Fix applied
The workflow now installs dependencies using the correct path and sets the working directory for all relevant steps. Additional logging, a pip cache, and checks were added to harden the workflow.
