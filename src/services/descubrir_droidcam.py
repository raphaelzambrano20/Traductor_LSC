"""Busca un DroidCam en la red local para no pedir la IP a mano."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from ipaddress import ip_network
import socket
from urllib.error import URLError
from urllib.request import Request, urlopen


PUERTO_DROIDCAM = 4747
RUTA_VIDEO = "/video"
TIEMPO_PUERTO = 0.18
TIEMPO_HTTP = 0.6
TRABAJADORES = 64


def url_droidcam(ip, puerto=PUERTO_DROIDCAM):
    return f"http://{ip}:{puerto}{RUTA_VIDEO}"


def ips_locales():
    encontradas = []
    try:
        prueba = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        prueba.connect(("8.8.8.8", 80))
        encontradas.append(prueba.getsockname()[0])
        prueba.close()
    except OSError:
        pass

    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            encontradas.append(info[4][0])
    except OSError:
        pass

    unicas = []
    for ip in encontradas:
        if ip.startswith("127.") or ip in unicas:
            continue
        unicas.append(ip)
    return unicas


def candidatos_red(ips=None):
    ips = ips if ips is not None else ips_locales()
    vistas = []
    for ip in ips:
        try:
            red = ip_network(f"{ip}/24", strict=False)
        except ValueError:
            continue
        for host in red.hosts():
            candidato = str(host)
            if candidato == ip or candidato in vistas:
                continue
            vistas.append(candidato)
    return vistas


def puerto_abierto(ip, puerto=PUERTO_DROIDCAM, timeout=TIEMPO_PUERTO):
    try:
        with socket.create_connection((ip, puerto), timeout=timeout):
            return True
    except OSError:
        return False


def parece_droidcam(ip, puerto=PUERTO_DROIDCAM, timeout=TIEMPO_HTTP):
    if not puerto_abierto(ip, puerto):
        return False

    for ruta in ("/", RUTA_VIDEO):
        request = Request(
            f"http://{ip}:{puerto}{ruta}",
            headers={"User-Agent": "LSCNOVA"},
            method="GET",
        )
        try:
            with urlopen(request, timeout=timeout) as respuesta:
                tipo = (respuesta.headers.get("Content-Type") or "").lower()
                if respuesta.status == 200:
                    if ruta == RUTA_VIDEO:
                        return "image" in tipo or "multipart" in tipo or tipo == ""
                    cuerpo = respuesta.read(400).decode("latin-1", errors="ignore").lower()
                    if "droidcam" in cuerpo or "mjpeg" in cuerpo or "video" in cuerpo:
                        return True
                    return True
        except (URLError, TimeoutError, OSError):
            continue
    return False


def descubrir_droidcam(ips=None):
    hallados = []
    with ThreadPoolExecutor(max_workers=TRABAJADORES) as pool:
        futuros = {
            pool.submit(parece_droidcam, ip): ip
            for ip in candidatos_red(ips)
        }
        for futuro in as_completed(futuros):
            ip = futuros[futuro]
            try:
                if futuro.result():
                    hallados.append({
                        "ip": ip,
                        "puerto": PUERTO_DROIDCAM,
                        "url": url_droidcam(ip),
                    })
            except Exception:
                continue

    hallados.sort(key=lambda item: item["ip"])
    return hallados
