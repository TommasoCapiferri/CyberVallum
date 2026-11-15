"""Conversions between number bases, IPv4 addresses and MAC addresses.

Linked to L2 of the study path (binary and hexadecimal). Pure logic: no system
calls, no print(), no input(). User errors raise ValueError with an Italian message.
"""

from __future__ import annotations

import ipaddress
from typing import Any

from cybervallum.core import registry

# Digits accepted for each base. Checked explicitly because int() would also
# accept "+", "_" and other forms that are not valid input for this tool.
_DIGITS = {2: "01", 10: "0123456789", 16: "0123456789ABCDEF"}


def numero(valore: str) -> dict[str, Any]:
    """Convert a non-negative integer written as 255, 0xFF or 0b1010."""
    text = valore.strip()
    if text.lower().startswith("0x"):
        base, cifre = 16, text[2:]
    elif text.lower().startswith("0b"):
        base, cifre = 2, text[2:]
    else:
        base, cifre = 10, text

    if not cifre or not all(c in _DIGITS[base] for c in cifre.upper()):
        raise ValueError(f"numero non valido: {valore!r}")

    n = int(cifre, base)
    binario = format(n, "b")
    return {
        "input": text,
        "decimale": n,
        "binario": binario,
        "esadecimale": format(n, "X"),
        "bit": len(binario),
    }


def ip(indirizzo: str) -> dict[str, Any]:
    """Show an IPv4 address as an integer, in binary and in hexadecimal."""
    try:
        addr = ipaddress.IPv4Address(indirizzo.strip())
    except ipaddress.AddressValueError:
        raise ValueError(f"indirizzo IPv4 non valido: {indirizzo!r}") from None
    ottetti = list(addr.packed)
    return {
        "indirizzo": str(addr),
        "intero": int(addr),
        "binario": ".".join(format(o, "08b") for o in ottetti),
        "esadecimale": ".".join(format(o, "02X") for o in ottetti),
        "privato": addr.is_private,
    }


def mac(indirizzo: str) -> dict[str, Any]:
    """Normalize a MAC address and read the multicast and locally administered bits."""
    cifre = indirizzo.strip().upper().replace(":", "").replace("-", "").replace(".", "")
    if len(cifre) != 12 or not all(c in _DIGITS[16] for c in cifre):
        raise ValueError(f"indirizzo MAC non valido: {indirizzo!r}")
    ottetti = [int(cifre[i:i + 2], 16) for i in range(0, 12, 2)]
    return {
        "mac": ":".join(format(o, "02X") for o in ottetti),
        "binario": ":".join(format(o, "08b") for o in ottetti),
        "oui": ":".join(format(o, "02X") for o in ottetti[:3]),
        "unicast": (ottetti[0] & 1) == 0,                   # bit 0 = 1 -> multicast
        "amministrato_localmente": (ottetti[0] & 2) != 0,   # bit 1 = 1 -> locally administered
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
