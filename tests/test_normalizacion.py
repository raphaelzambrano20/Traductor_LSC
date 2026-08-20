"""Ejemplo de pruebas unitarias para el módulo de normalización de texto."""

import pytest

from src.services.normalizacion import normalizar_texto, tokenizar


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("  Hola  ", "hola"),
        ("BUENOS_DÍAS", "buenos dias"),
        ("¿Cómo estás?", "como estas"),
        ("hola   mundo", "hola mundo"),
        ("", ""),
    ],
)
def test_normalizar_texto(entrada, esperado):
    assert normalizar_texto(entrada) == esperado


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("Hola mundo", ["hola", "mundo"]),
        ("  una   frase  ", ["una", "frase"]),
        ("", []),
        ("   ", []),
    ],
)
def test_tokenizar(entrada, esperado):
    assert tokenizar(entrada) == esperado
