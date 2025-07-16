from setuptools import setup, find_packages

setup(
    name="document-formatting-system",
    version="1.0.0",
    description="Non-Destructive Document Formatting System with HTML Output",
    author="Claude AI Assistant",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "python-docx>=0.8.11",
        "beautifulsoup4>=4.11.0",
        "lxml>=4.9.0",
        "flask>=2.3.0",
        "pytest>=7.0.0",
        "python-dateutil>=2.8.0",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)