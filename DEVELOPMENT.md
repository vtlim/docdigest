## Local development

Set up Python:

```
# create conda env
conda create --name summary
conda activate summary

# install packages
# uses conda when possible, pip otherwise
conda install anthropic
pip install markdown-analysis
```

Install application:

```
cd <docdigest root directory>
conda activate summary
pip install -e .
```

Download test docs:

```
# install fresh docusaurus
npx create-docusaurus@latest example-docs classic
```

