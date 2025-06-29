"""
Setup script para o Orquestrador
"""

from setuptools import setup, find_packages
from pathlib import Path

# Ler README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Ler requirements
requirements = []
if (this_directory / "requirements.txt").exists():
    requirements = (this_directory / "requirements.txt").read_text().strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="orquestrador",
    version="1.1.0",
    author="Jesse Freitas",
    author_email="jesse@example.com",
    description="Sistema de orquestração de tarefas e processos automatizados",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jessefreitas/orquestrador",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "orquestrador=src.release_cli:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "src": ["*.yaml", "*.json"],
    },
    keywords="orchestration, workflow, automation, tasks, pipeline, scheduler",
    project_urls={
        "Bug Reports": "https://github.com/jessefreitas/orquestrador/issues",
        "Source": "https://github.com/jessefreitas/orquestrador",
        "Documentation": "https://github.com/jessefreitas/orquestrador#readme",
    },
) 