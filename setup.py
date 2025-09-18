from setuptools import setup, find_packages

setup(
    name="docdigest",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "anthropic",
        "mrkdwn-analysis"
    ],
    python_requires=">=3.8",
    author="Victoria",
    description="AI-powered documentation summarization tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    entry_points={
        'console_scripts': [
            'docdigest=docdigest.main:main',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
