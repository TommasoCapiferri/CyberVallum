"""Conversions between number bases, IPv4 addresses and MAC addresses.

Linked to L2 of the study path (binary and hexadecimal). Pure logic: no system
calls, no print(), no input(). User errors raise ValueError with an Italian message.
"""

from __future__ import annotations

import ipaddress
from typing import Any

from cybervallum.core import registry

def numero(valore: str) -> dict[str, Any]:
    text = valore.strip()
    if text.lower().startswith("0x"):
        base = 16
        cifre = text[2:]
    elif text.lower().startswith("0b"):
        base = 2
        cifre = text[2:]
    else:
        base = 10
        cifre = text

    if not cifre or cifre.startswith("-"):
        raise ValueError(f"numero non valido: {valore!r}")

    try:
        n = int(cifre, base)
    except ValueError:
        raise ValueError(f"numero non valido: {valore!r}")

    return {
        "input": text,
        "decimale": n,
        "binario": format(n, "b"),
        "esadecimale": format(n, "X"),
        "bit": len(format(n, "b"))
    }


def ip(indirizzo: str) -> dict[str, Any]:
    try:
        addr = ipaddress.IPv4Address(indirizzo.strip())
    except ipaddress.AddressValueError:
        raise ValueError(f"indirizzo IPv4 non valido: {indirizzo!r}")
    ottetti = list(addr.packed)
    return {
        "indirizzo": str(addr),
        "intero": int(addr),
        "binario": ".".join(format(o, "08b") for o in ottetti),
        "esadecimale": ".".join(format(o, "02X") for o in ottetti),
        "privato": addr.is_private,
    }




def mac(indirizzo: str) -> dict[str, Any]:
    cifre = indirizzo.strip().upper().replace(":", "").replace("-", "").replace(".", "")
    if len(cifre) != 12 or not all(c in "0123456789ABCDEF" for c in cifre):
        raise ValueError(f"indirizzo MAC non valido: {indirizzo!r}")
    ottetti = [int(cifre[i:i + 2], 16) for i in range(0, 12, 2)]
    return {
        "mac": ":".join(format(o, "02X") for o in ottetti),
        "binario": ":".join(format(o, "08b") for o in ottetti),
        "oui": ":".join(format(o, "02X") for o in ottetti[:3]),
        "unicast": (ottetti[0] & 1) == 0,
        "amministrato_localmente": (ottetti[0] & 2) != 0,
    }



@registry.action("converti.numero", "Converte un numero tra decimale, binario ed esadecimale",
                 params={"valore": registry.Param(str, required=True, description="Numero: 255, 0xFF o 0b1010")})
def _action_numero(valore: str) -> dict[str, Any]:
    return numero(valore)


@registry.action("converti.ip", "Mostra un indirizzo IPv4 in binario, esadecimale e come intero",
                 params={"indirizzo": registry.Param(str, required=True, description="Indirizzo IPv4")})
def _action_ip(indirizzo: str) -> dict[str, Any]:
    return ip(indirizzo)


@registry.action("converti.mac", "Mostra un indirizzo MAC in binario, con OUI e tipo",
                 params={"indirizzo": registry.Param(str, required=True, description="Indirizzo MAC")})
def _action_mac(indirizzo: str) -> dict[str, Any]:
    return mac(indirizzo)
