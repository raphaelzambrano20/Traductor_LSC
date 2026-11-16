from src.services.descubrir_droidcam import url_droidcam, url_droidcam_red


def test_url_droidcam():
    assert url_droidcam("192.168.1.20") == "http://192.168.1.20:4747/video"


def test_url_droidcam_red_usa_ip_y_ruta_fija(monkeypatch):
    monkeypatch.setattr("src.services.descubrir_droidcam.ip_de_la_red", lambda: "192.168.0.14")
    assert url_droidcam_red() == {
        "ip": "192.168.0.14",
        "puerto": 4747,
        "url": "http://192.168.0.14:4747/video",
    }
