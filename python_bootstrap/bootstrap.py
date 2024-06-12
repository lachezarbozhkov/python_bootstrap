#!/usr/bin/env python3

import os
import subprocess
import sys
from textwrap import dedent


def run_command(command, check=True, capture_output=False, shell=True):
    """Runs a shell command and optionally captures the output."""
    result = subprocess.run(command, check=check, capture_output=capture_output, shell=shell, text=True)
    if capture_output:
        return result.stdout.strip()
    return result


def add_poetry_configs():
    """Adds the specified configurations to the Poetry pyproject.toml file."""
    poetry_config = dedent(
        """
        [tool.black]
        line-length = 120

        [tool.isort]
        atomic = true
        line_length = 120
        multi_line_output = 3
        include_trailing_comma = true
        force_grid_wrap = 0
        use_parentheses = true
        order_by_type = true
        case_sensitive = true
        skip=[".cache"]
        """
    )
    with open("pyproject.toml", "a") as f:
        f.write(poetry_config)


def create_flake8_config():
    basic_config = dedent(
        """[flake8]
        ; E203: black's space before ':' in list slices
        ; W503: line break before binary operator
        ignore = E203,W503
        max-line-length = 120
        """
    )

    with open(".flake8", "w") as f:
        f.write(basic_config)


def create_pre_commit_config():
    basic_config = """repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.0.1
    hooks:
    - id: trailing-whitespace
    - id: end-of-file-fixer
    - id: check-yaml
    - id: check-json
    - id: check-toml
    - id: check-added-large-files
      args:
        - maxkb=1024
    - id: check-executables-have-shebangs
    - id: check-merge-conflict

-   repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
    - id: black
-   repo: https://github.com/PyCQA/isort
    rev: 5.10.1
    hooks:
    - id: isort
-   repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.241
    hooks:
    - id: ruff
"""
    with open(".pre-commit-config.yaml", "w") as f:
        f.write(basic_config)


def install_packages(*packages, dev=False):
    for package in packages:
        group = "--group dev" if dev else ""
        run_command(f"poetry add {group} {package}")


def bootstrap(directory):
    """Bootstraps a new project in the specified directory."""

    if os.path.exists(directory):
        print(f"Directory {directory} already exists.")
        sys.exit(1)

    print("Bootstrapping the project...")

    os.makedirs(directory)
    os.chdir(directory)
    os.makedirs(directory)  # create the package directory for poetry

    python_version = run_command("python --version | cut -d ' ' -f 2", capture_output=True)
    print(f"💡 Using Python {python_version}")
    run_command(f"pyenv local {python_version}")
    run_command("git init")
    with open("README.md", "w") as f:
        f.write(f"# {directory}\n")

    # copy python gitignore from github to project folder
    run_command("curl -o .gitignore https://raw.githubusercontent.com/github/gitignore/master/Python.gitignore")

    run_command("pip install poetry")

    print("Creating a new Poetry project...")
    # in-project is bettter, but slow on shared disk
    run_command("poetry config virtualenvs.in-project false")
    run_command("poetry config virtualenvs.create true")
    run_command("poetry self add 'poetry-dynamic-versioning[plugin]'")

    run_command("poetry init -n")
    run_command("poetry check --no-ansi --quiet")
    add_poetry_configs()
    create_flake8_config()
    print("✅ Directory created.")

    print("Setting up pre-commit hooks...")
    create_pre_commit_config()
    run_command("poetry add --group dev pre-commit")
    run_command("poetry run pre-commit install")
    run_command("poetry run pre-commit autoupdate")
    run_command("poetry run pre-commit run --all-files")
    print("✅ pre-commit installed.")

    install_packages("black", "isort", "ruff", "pylint", "flake8", dev=True)
    install_packages("torch", "transformers", "scikit-learn", "pandas", "numpy", "scipy", "tqdm")
    install_packages("pytorch-lightning", "seaborn", "matplotlib", "torchmetrics", dev=True)
    install_packages("jupyterlab", "ipywidgets", dev=True)
    install_packages("psycopg2", "sqlalchemy")
    print("✅ Default packages installed.")

    run_command("poetry add --group dev ipykernel")
    run_command(f"poetry run python -m ipykernel install --user --name={directory}")
    print("✅ Jupyter kernel installed.")

    run_command(
        "git add .flake8 .pre-commit-config.yaml .python-version  README.md poetry.lock pyproject.toml .gitignore"
    )
    run_command("git commit -m 'Initial commit'")
    run_command("git branch -M main")  # rename to main branch

    print("✅ Initial structure committed in git.")

    print("✅ Bootstrap completed successfully.")
    print("🚀 Happy coding!")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        directory = sys.argv[1]
        bootstrap(directory)
    else:
        print("Usage: python bootstrap.py <directory>")
        sys.exit(1)
