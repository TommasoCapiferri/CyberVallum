"""Tests of the `converti` module: pure functions, no mocks needed."""

import pytest

from cybervallum.core import converti, registry


@pytest.mark.parametrize("valore, atteso", [
    ("0xFF", {"input": "0xFF", "decimale": 255, "binario": "11111111", "esadecimale": "FF", "bit": 8}),
    ("0", {"input": "0", "decimale": 0, "binario": "0", "esadecimale": "0", "bit": 1}),
    ("10", {"input": "10", "decimale": 10, "binario": "1010", "esadecimale": "A", "bit": 4}),
    ("0b1010", {"input": "0b1010", "decimale": 10, "binario": "1010", "esadecimale": "A", "bit": 4}),
    (" 0Xff ", {"input": "0Xff", "decimale": 255, "binario": "11111111", "esadecimale": "FF", "bit": 8}),
])
def test_numero_ok(valore, atteso):
    assert converti.numero(valore) == atteso


@pytest.mark.parametrize("valore", ["", "-5", "12a", "0xZZ", "0b102", "0x", "+5", "1_000", "0x-5"])
def test_numero_errore(valore):
    with pytest.raises(ValueError):
        converti.numero(valore)


def test_ip_ok():
    assert converti.ip("192.168.1.10") == {
        "indirizzo": "192.168.1.10",
        "intero": 3232235786,
        "binario": "11000000.10101000.00000001.00001010",
        "esadecimale": "C0.A8.01.0A",
        "privato": True,
    }


def test_ip_pubblico():
    assert converti.ip("8.8.8.8")["privato"] is False


@pytest.mark.parametrize("indirizzo", ["256.1.1.1", "ciao", "::1", "", "1.2.3", "01.2.3.4"])
def test_ip_errore(indirizzo):
    with pytest.raises(ValueError):
        converti.ip(indirizzo)


@pytest.mark.parametrize("indirizzo", ["00:1A:2B:3C:4D:5E", "00-1a-2b-3c-4d-5e", "001A.2B3C.4D5E"])
def test_mac_formati(indirizzo):
    assert converti.mac(indirizzo)["mac"] == "00:1A:2B:3C:4D:5E"


def test_mac_dettagli():
    r = converti.mac("00:1A:2B:3C:4D:5E")
    assert r["binario"].startswith("00000000:00011010")
    assert r["oui"] == "00:1A:2B"
    assert r["unicast"] is True
    assert r["amministrato_localmente"] is False


def test_mac_multicast_e_locale():
    assert converti.mac("01:00:5E:00:00:01")["unicast"] is False
    assert converti.mac("02:00:00:00:00:01")["amministrato_localmente"] is True


@pytest.mark.parametrize("indirizzo", ["00:1A:2B", "GG:00:00:00:00:00", "", "00:1A:2B:3C:4D:5E:6F"])
def test_mac_errore(indirizzo):
    with pytest.raises(ValueError):
        converti.mac(indirizzo)


def test_registry_ok():
    r = registry.run("converti.numero", {"valore": "0xFF"})
    assert r["stato"] == "ok"
    assert r["dati"]["decimale"] == 255


def test_registry_errore():
    r = registry.run("converti.ip", {"indirizzo": "ciao"})
    assert r["stato"] == "errore"
    assert r["errore"]  # not None and not empty (`!= ""` would also accept None)

