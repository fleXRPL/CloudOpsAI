from setuptools import setup, find_packages

setup(
    name="ai-noc-agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "boto3>=1.28.0",
        "pyyaml>=6.0",
        "anthropic>=0.3.0",
        "python-json-logger>=2.0.0",
        "rich>=13.7.0",
        "click>=8.1.7",
        "prompt-toolkit>=3.0.43"
    ],
    entry_points={
        'console_scripts': [
            'cloudopsai=ai_noc.cli:main',
        ],
    },
    python_requires=">=3.12",
)
