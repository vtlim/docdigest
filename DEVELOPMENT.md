## Development setup

### Python

1. Install Python. Initial development used version 3.13.8.
1. Optionally create a dedicated environment:

   ```
   conda create --name summary
   conda activate summary
   ```

1. Install packages. Uses conda (conda-forge channel) when possible, pip otherwise.

   ```
   conda install anthropic
   pip install markdown-analysis
   ```

### Application

1. Git clone `docdigest`.
1. Go to the root directory of your repo.
1. Install the package in an editable mode:

   ```
   pip install -e .
   ```

### Test docs

For a fresh Docusaurus install:

```
npx create-docusaurus@latest example-docs classic
```

## Publishing the application

1. Get required Python packages:

   ```
   pip install build
   conda install twine
   ```

1. Verify contents of `pyproject.toml`.

1. Run build command:

   ```
   python -m build
   ```

1. Publish to test PyPI:

   ```
   twine upload --repository testpypi dist/*
   ```

1. When you've confirmed everything is correct, publish to production PyPI.
Be sure that you publish when you're sure you're ready.
You can't delete a release after 72 hours; you can only yank it but it's still public.

   ```
   twine upload dist/*
   ```

