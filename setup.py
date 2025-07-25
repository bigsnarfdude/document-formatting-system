from setuptools import setup, find_packages

setup(
    name="document-formatting-system",
    version="2.0.0",
    description="AI-Powered Document Formatting System with Multi-Stage Processing",
    author="Claude AI Assistant",
    packages=find_packages(),
    install_requires=[
        "python-docx>=0.8.11",
        "requests>=2.31.0",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    entry_points={
        "console_scripts": [
            "document-formatter=multi_stage_formatter:main",
        ],
    },
)