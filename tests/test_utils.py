"""Tests para las funciones de utils.py."""

from datetime import datetime

import pytest

from utils import (
    formatear_duracion,
    generar_slug,
    obtener_año_actual,
    validar_año,
    validar_correo,
)


@pytest.mark.parametrize(
    "correo", ["a@b.co", "nombre.apellido@mail.com", "x+tag@sub.dominio.org"]
)
def test_validar_correo_valido(correo):
    assert validar_correo(correo)


@pytest.mark.parametrize("correo", ["", "sin-arroba", "a@b", "@x.com", "a b@c.com"])
def test_validar_correo_invalido(correo):
    assert not validar_correo(correo)


@pytest.mark.parametrize(
    ("segundos", "esperado"), [(0, "00:00"), (59, "00:59"), (245, "04:05")]
)
def test_formatear_duracion(segundos, esperado):
    assert formatear_duracion(segundos) == esperado


def test_generar_slug():
    assert generar_slug("  Hola   Mundo!! -- Rock ") == "hola-mundo-rock"


def test_obtener_año_actual():
    assert obtener_año_actual() == datetime.now().year


def test_validar_año():
    assert validar_año(1900)
    assert validar_año(obtener_año_actual())
    assert not validar_año(1899)
    assert not validar_año(obtener_año_actual() + 1)
