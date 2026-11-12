from __future__ import annotations


def test_las_fuentes_se_registran_una_sola_vez() -> None:
    from ui import estilos

    estilos._cargar_fuentes()
    identificadores = list(estilos._fuentes_cache[2])
    assert identificadores, "las fuentes empaquetadas deberían quedar registradas"

    estilos._cargar_fuentes()
    assert estilos._fuentes_cache[2] == identificadores


def test_el_estilo_es_el_nativo_en_windows(monkeypatch) -> None:
    from ui import estilos

    monkeypatch.setattr(estilos.sys, "platform", "win32")
    assert estilos._estilo_base() == "windowsvista"

    monkeypatch.setattr(estilos.sys, "platform", "linux")
    assert estilos._estilo_base() == "Fusion"
