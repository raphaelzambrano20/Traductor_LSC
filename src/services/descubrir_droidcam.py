"""Arma la URL de DroidCam con la IP local de la red."""

from __future__ import annotations

import socket


PUERTO_DROIDCAM = 4747
RUTA_VIDEO = "/video"


def url_droidcam(ip, puerto=PUERTO_DROIDCAM):
    return f"http://{ip}:{puerto}{RUTA_VIDEO}"


def ip_de_la_red():
    try:
        prueba = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        prueba.connect(("8.8.8.8", 80))
        ip = prueba.getsockname()[0]
        prueba.close()
        if ip and not ip.startswith("127."):
            return ip
    except OSError:
        pass

    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip and not ip.startswith("127."):
                return ip
    except OSError:
        pass

    return None


def url_droidcam_red():
    ip = ip_de_la_red()
    if not ip:
        return None
    return {
        "ip": ip,
        "puerto": PUERTO_DROIDCAM,
        "url": url_droidcam(ip),
    }
