import tomllib

import pytest

from cybersegugio.core import config, registry
from cybersegugio.core.config import ConfigError, Setting


def test_defaults_without_file(isolated_config):
    assert not isolated_config.exists()
    assert config.get_setting("api.host") == "127.0.0.1"
    assert config.get_setting("rete.consenti_ip_pubblici") is False


def test_set_saves_to_toml_and_converts_strings(isolated_config):
    result = config.set_setting("api.porta", "9000")
    assert result == {"chiave": "api.porta", "valore": 9000, "file": str(isolated_config)}
    with isolated_config.open("rb") as fh:
        assert tomllib.load(fh) == {"api": {"porta": 9000}}
    assert config.get_setting("api.porta") == 9000


def test_set_bool_and_list():
    config.set_setting("rete.consenti_ip_pubblici", "true")
    config.set_setting("aggiornamenti.fonti", "https://a.example/x.json, https://b.example/y")
    assert config.get_setting("rete.consenti_ip_pubblici") is True
    assert config.get_setting("aggiornamenti.fonti") == ["https://a.example/x.json", "https://b.example/y"]


@pytest.mark.parametrize(
    "key, value",
    [
        ("api.host", "0.0.0.0"),  # rule 10: loopback only
        ("api.host", "192.168.1.10"),
        ("api.porta", "80"),  # below 1024
        ("api.porta", "abc"),
        ("ai.provider", "chatgpt"),  # not in choices
        ("rete.consenti_ip_pubblici", "forse"),
        ("aggiornamenti.fonti", "http://insicuro.example/lista"),  # rule 11: HTTPS only
        ("ai.ollama_url", "ftp://127.0.0.1"),
    ],
)
def test_invalid_values_are_rejected(key, value, isolated_config):
    with pytest.raises(ConfigError):
        config.set_setting(key, value)
    assert not isolated_config.exists()  # nothing saved


def test_unknown_key():
    with pytest.raises(ConfigError, match="sconosciuta"):
        config.get_setting("non.esiste")
    with pytest.raises(ConfigError):
        config.set_setting("non.esiste", "1")


def test_list_marks_origin_and_broken_values(isolated_config):
    isolated_config.write_text('[api]\nporta = 9001\nhost = "0.0.0.0"\n', encoding="utf-8")
    entries = {e["chiave"]: e for e in config.list_settings()}
    assert entries["api.porta"]["valore"] == 9001
    assert entries["api.porta"]["origine"] == "file"
    assert entries["ai.provider"]["origine"] == "predefinito"
    # An invalid value in the file is reported, and the default is shown instead.
    assert entries["api.host"]["errore"] is not None
    assert entries["api.host"]["valore"] == "127.0.0.1"


def test_corrupted_file_raises_config_error(isolated_config):
    isolated_config.write_text("questo non è toml [", encoding="utf-8")
    with pytest.raises(ConfigError, match="impossibile leggere"):
        config.get_setting("api.porta")


def test_set_keeps_other_values():
    config.set_setting("api.porta", 9002)
    config.set_setting("ai.modello", "altro:7b")
    assert config.get_setting("api.porta") == 9002
    assert config.get_setting("ai.modello") == "altro:7b"


def test_register_setting_validates_key_and_default():
    with pytest.raises(ConfigError):
        config.register_setting(Setting("senzasezione", str, "x", "chiave errata"))
    with pytest.raises(ConfigError):
        config.register_setting(Setting("api.host", str, "127.0.0.1", "duplicata"))
    with pytest.raises(ConfigError):
        config.register_setting(Setting("prova.porta", int, 10, "default non valido", config._port))


def test_config_path_per_platform(monkeypatch, tmp_path):
    monkeypatch.delenv(config.ENV_CONFIG_PATH)
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setattr(config, "_is_windows", lambda: True)
    assert config.config_path() == tmp_path / "roaming" / "CyberSegugio" / "config.toml"
    monkeypatch.setattr(config, "_is_windows", lambda: False)
    assert config.config_path() == tmp_path / "xdg" / "cybersegugio" / "config.toml"


def test_config_actions_go_through_registry():
    ok = registry.run("config.set", {"chiave": "api.porta", "valore": "9100"})
    assert ok["stato"] == "ok" and ok["dati"]["valore"] == 9100
    assert registry.run("config.get", {"chiave": "api.porta"})["dati"]["valore"] == 9100

    bad = registry.run("config.set", {"chiave": "api.host", "valore": "0.0.0.0"})
    assert bad["stato"] == "errore"
    assert "api.host" in bad["errore"]
    assert not bad["errore"].startswith("ConfigError")  # user message, no technical prefix
