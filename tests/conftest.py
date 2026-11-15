"""Shared fixtures: tests never touch the real config.toml of the developer."""

import pytest

from cybervallum.core import config


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Point config.toml to a temporary folder for every test."""
    path = tmp_path / "config.toml"
    monkeypatch.setenv(config.ENV_CONFIG_PATH, str(path))
    return path
