from src.services.descubrir_droidcam import candidatos_red, url_droidcam


def test_url_droidcam():
    assert url_droidcam("192.168.1.20") == "http://192.168.1.20:4747/video"


def test_candidatos_red_omite_la_ip_local():
    candidatos = candidatos_red(["192.168.1.10"])
    assert "192.168.1.10" not in candidatos
    assert "192.168.1.20" in candidatos
    assert len(candidatos) == 254
