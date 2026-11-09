from __future__ import annotations

import os
import sqlite3
from datetime import date

import pytest
from PyQt6.QtWidgets import QApplication

from repositories.cierre_repositorio import CierreRepositorio
from repositories.sqlite import conectar, ruta_db
from repositories.venta_repositorio import VentaRepositorio
from services.backup import ErrorBackup, ServicioBackup, tamano_legible
from services.cierre_caja import ServicioCierre
from services.estadisticas_ventas import EstadisticasVentas
from ui.widgets.notificacion import Notificacion
from views.ventana_base import VentanaBase
from views.ventana_cierre import VentanaCierre
from views.ventana_configuracion import VentanaConfiguracion


def gestor_dummy():
    class Dumm:
        def configurar(self, *args):
            return None
    return Dumm()


def _base(tmp_path):
    ruta = ruta_db(tmp_path / "datos" / "betterstock.db")
    conexion = conectar(ruta)
    conexion.execute("INSERT INTO categorias(nombre) VALUES ('Bebidas')")
    conexion.commit()
    conexion.close()
    return ruta


def _servicio(tmp_path, base=None):
    return ServicioBackup(base=base or _base(tmp_path), directorio=tmp_path / "backups")


def _filas(ruta):
    conexion = sqlite3.connect(str(ruta))
    try:
        return conexion.execute("SELECT nombre FROM categorias").fetchall()
    finally:
        conexion.close()


def _con_mtime(ruta, momento):
    os.utime(ruta, (momento, momento))


def test_directorio_por_defecto_es_output_backups():
    servicio = ServicioBackup()
    assert servicio.directorio_backups().name == "backups"
    assert servicio.directorio_backups().parent.name == "output"


def test_generar_devuelve_una_copia_legible(tmp_path):
    servicio = _servicio(tmp_path)
    copia = servicio.generar()

    assert copia.is_file()
    assert copia.name.startswith("betterstock_") and copia.name.endswith(".db")
    assert _filas(copia) == [("Bebidas",)]


def test_no_sobrescribe_la_copia_del_dia(tmp_path):
    servicio = _servicio(tmp_path)
    primera = servicio.generar()
    segunda = servicio.generar()

    assert primera != segunda
    assert primera.exists() and segunda.exists()
    assert len(servicio.listar()) == 2


def test_listar_ordena_de_mas_nuevo_a_mas_viejo(tmp_path):
    servicio = _servicio(tmp_path)
    copias = [servicio.generar() for _ in range(3)]
    for indice, copia in enumerate(copias):
        _con_mtime(copia, 1_700_000_000 + indice * 60)

    assert servicio.listar() == [copias[2], copias[1], copias[0]]


def test_rotar_deja_las_mas_recientes(tmp_path):
    servicio = _servicio(tmp_path)
    copias = [servicio.generar() for _ in range(3)]
    for indice, copia in enumerate(copias):
        _con_mtime(copia, 1_700_000_000 + indice * 60)

    servicio.rotar(2)

    restantes = servicio.listar()
    assert len(restantes) == 2
    assert restantes == [copias[2], copias[1]]
    assert not copias[0].exists()


def test_rotar_no_toca_archivos_que_no_son_copias(tmp_path):
    servicio = _servicio(tmp_path)
    servicio.generar()
    intruso = servicio.directorio_backups() / "notas.txt"
    intruso.write_text("no me borres")

    servicio.rotar(0)

    assert intruso.exists()
    assert servicio.listar() == []


def test_restaurar_repone_los_datos_anteriores(tmp_path):
    base = _base(tmp_path)
    servicio = _servicio(tmp_path, base=base)
    copia = servicio.generar()

    conexion = conectar(base)
    conexion.execute("INSERT INTO categorias(nombre) VALUES ('Limpieza')")
    conexion.commit()
    conexion.close()

    servicio.restaurar(copia)

    assert [nombre for nombre, in _filas(base)] == ["Bebidas"]
    assert len(servicio.listar()) == 2


def test_restaurar_rechaza_una_copia_corrupta_sin_tocar_la_base(tmp_path):
    base = _base(tmp_path)
    servicio = _servicio(tmp_path, base=base)
    corrupta = servicio.directorio_backups() / "betterstock_20200101_101010.db"
    servicio.directorio_backups().mkdir(parents=True, exist_ok=True)
    corrupta.write_bytes(b"esto no es una base de datos" * 50)

    with pytest.raises(ErrorBackup):
        servicio.restaurar(corrupta)

    assert _filas(base) == [("Bebidas",)]
    assert not (base.with_name(base.name + ".restaurando")).exists()


def test_restaurar_falla_si_la_copia_no_existe(tmp_path):
    servicio = _servicio(tmp_path)
    with pytest.raises(ErrorBackup):
        servicio.restaurar(servicio.directorio_backups() / "betterstock_19990101.db")


def test_generar_falla_si_no_hay_base(tmp_path):
    servicio = ServicioBackup(base=tmp_path / "no-existe" / "betterstock.db",
                              directorio=tmp_path / "backups")
    with pytest.raises(ErrorBackup):
        servicio.generar()


def test_cierre_guarda_backup_y_no_falla_si_la_copia_falla(tmp_path):
    base = _base(tmp_path)
    cierres = CierreRepositorio(base)
    estadisticas = EstadisticasVentas(VentaRepositorio(base))
    servicio = ServicioCierre(estadisticas, cierres)

    class Roto:
        def generar(self):
            raise OSError("no hay espacio")

        def rotar(self, cantidad=15):
            return []

        def total(self):
            return 0

    servicio._backup = Roto()
    dia = date(2023, 11, 14)

    with pytest.warns(RuntimeWarning):
        registro = servicio.cerrar(dia, 0.0)

    assert registro is not None
    assert servicio.ultimo_backup is None
    assert cierres.ya_cerrado(dia)


def test_cierre_deja_una_copia_de_la_base(tmp_path):
    base = _base(tmp_path)
    backups = ServicioBackup(base=base, directorio=tmp_path / "backups")
    servicio = ServicioCierre(
        EstadisticasVentas(VentaRepositorio(base)),
        CierreRepositorio(base),
        backup=backups,
    )

    servicio.cerrar(date(2023, 11, 14), 0.0)

    assert servicio.ultimo_backup is not None
    assert servicio.ultimo_backup.exists()
    assert _filas(servicio.ultimo_backup) == [("Bebidas",)]
    assert servicio.total_backups() == 1


def test_ventana_cierre_avisa_la_copia_sin_modal(tmp_path, aplicacion, monkeypatch):
    base = _base(tmp_path)
    backup = ServicioBackup(base=base, directorio=tmp_path / "backups")
    cierre = ServicioCierre(
        EstadisticasVentas(VentaRepositorio(base)),
        CierreRepositorio(base),
        backup=backup,
    )
    ventana = VentanaCierre(cierre)
    ventana.ui.dateDia.setDate(date(2023, 11, 14))
    ventana.recalcular()
    ventana.ui.spnEfectivo.setValue(0.0)
    avisos = []
    monkeypatch.setattr(VentanaBase, "mostrar_informacion", lambda *a: None)
    monkeypatch.setattr(VentanaBase, "confirmar", lambda *a: True)
    monkeypatch.setattr(Notificacion, "mostrar", lambda _self, titulo, texto: avisos.append((titulo, texto)))

    ventana.cerrar_caja()

    assert avisos and avisos[0][0] == "Copia de seguridad"
    assert len(backup.listar()) == 1
    assert cierre.ya_cerrado(date(2023, 11, 14))


def test_tamano_legible():
    class Falso:
        def __init__(self, bytes_totales):
            self._bytes = bytes_totales

        def stat(self):
            class Dato:
                st_size = self._bytes
            return Dato()

    assert tamano_legible(Falso(500)) == "500 B"
    assert tamano_legible(Falso(2048)) == "2 KB"
    assert tamano_legible(Falso(3 * 1024 * 1024)) == "3.0 MB"


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


def test_configuracion_lista_las_copias_y_hace_una_nueva(tmp_path, aplicacion, monkeypatch):
    base = _base(tmp_path)
    backup = ServicioBackup(base=base, directorio=tmp_path / "backups")
    backup.generar()
    ventana = VentanaConfiguracion(gestor_dummy(), backup=backup)
    monkeypatch.setattr(VentanaConfiguracion, "mostrar_advertencia", lambda *a: None)

    assert ventana.tblBackups.rowCount() == 1
    assert ventana.tblBackups.item(0, 0).text() == backup.listar()[0].name

    ventana.hacer_copia()

    assert ventana.tblBackups.rowCount() == 2
    assert ventana.btnRestaurar.isEnabled()
    assert len(backup.listar()) == 2


def test_configuracion_no_hace_nada_sin_confirmar(tmp_path, aplicacion, monkeypatch):
    base = _base(tmp_path)
    backup = ServicioBackup(base=base, directorio=tmp_path / "backups")
    backup.generar()
    ventana = VentanaConfiguracion(gestor_dummy(), backup=backup)
    ventana.tblBackups.selectRow(0)
    monkeypatch.setattr(VentanaConfiguracion, "mostrar_advertencia", lambda *a: None)
    monkeypatch.setattr(VentanaConfiguracion, "confirmar", lambda *a: False)

    ventana.restaurar()

    assert _filas(base) == [("Bebidas",)]


def test_configuracion_restaura_con_confirmacion(tmp_path, aplicacion, monkeypatch):
    base = _base(tmp_path)
    backup = ServicioBackup(base=base, directorio=tmp_path / "backups")
    copia = backup.generar()
    conexion = conectar(base)
    conexion.execute("INSERT INTO categorias(nombre) VALUES ('Limpieza')")
    conexion.commit()
    conexion.close()
    ventana = VentanaConfiguracion(gestor_dummy(), backup=backup)
    ventana.tblBackups.selectRow(0)
    monkeypatch.setattr(VentanaConfiguracion, "mostrar_advertencia", lambda *a: None)
    preguntas = []
    monkeypatch.setattr(VentanaConfiguracion, "confirmar",
                        lambda _self, titulo, pregunta: preguntas.append(pregunta) or True)

    ventana.restaurar()

    assert preguntas and "reemplaza todos los datos actuales" in preguntas[0]
    assert [nombre for nombre, in _filas(base)] == ["Bebidas"]
    assert copia.exists()