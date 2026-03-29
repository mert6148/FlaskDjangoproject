import os
import pytest


def test_docker_files_exist():
    assert os.path.exists("Dockerfile"), "Dockerfile bulunamadi"
    assert os.path.exists("docker-compose.yml"), "docker-compose.yml bulunamadi"


def test_venv_scripts_exist():
    assert os.path.exists("scripts/setup_venv.sh"), "setup_venv.sh bulunamadi"
    assert os.path.exists("scripts/activate_venv.ps1"), "activate_venv.ps1 bulunamadi"


def test_requirements_headers():
    with open("requirements.txt", "r", encoding="utf-8") as f:
        content = f.read()
    assert "flask" in content
    assert "django" in content
    assert "pytest" in content
