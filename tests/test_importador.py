from __future__ import annotations

from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication, QDialog

from models.producto import Producto
from repositories.importacion_repositorio import ImportacionRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.sqlite import conectar, ruta_db
from services.backup import ServicioBackup
from services.importador.csv_importador import ImportadorCSV
from services.importador.deteccion import (
    coincidir_columnas,
    detectar_codificacion,
    detectar_delimitador,
    normalizar,
    parsear_precio,
)
from services.importador.modelo import (
    EXISTENTE_ACTUALIZAR_PRECIOS,
    EXISTENTE_OMITIR,
    MODO_CATALOGO,
    MODO_IGNORAR,
    MODO_PRECIOS,
    MODO_STOCK,
    Mapeo,
    Opciones,
)
from services.importador.secciones import detectar_secciones
from services.importador.servicio import ServicioImportacion
from services.planes import PLAN_GRATIS
from views.importador_productos import AvisoPlanGratis, ImportadorProductos


@pytest.fixture(scope="session")
def aplicacion() -> QApplication:
    existente = QApplication.instance()
    if existente is not None:
        return existente
    return QApplication([])


@pytest.fixture
def base(tmp_path) -> Path:
    ruta = ruta_db(tmp_path / "datos" / "betterstock.db")
    conexion = conectar(ruta)
    conexion.close()
    return ruta


@pytest.fixture
def servicio(base, tmp_path) -> ServicioImportacion:
    return ServicioImportacion(
        ProductoRepositorio(base),
        ImportacionRepositorio(base),
        backup=ServicioBackup(base=base, directorio=tmp_path / "backups"),
        base=base,
    )


def _csv(tmp_path, lineas, nombre="lista.csv", encoding="utf-8") -> Path:
    ruta = tmp_path / nombre
    ruta.write_text("\n".join(lineas) + "\n", encoding=encoding)
    return ruta


def _guardar(base, codigo, nombre, precio_venta=0.0, stock=0) -> Producto:
    producto = Producto(
        codigo=codigo,
        nombre=nombre,
        precio_venta=precio_venta,
        stock_actual=stock,
    )
    ProductoRepositorio(base).guardar(producto)
    return producto


def _mapeo(**columnas) -> Mapeo:
    return Mapeo(columnas=dict(columnas))


def _cerrar(asistente: ImportadorProductos) -> None:
    asistente.close()
    asistente.deleteLater()
    aplicacion_actual().processEvents()


def aplicacion_actual() -> QApplication:
    return QApplication.instance()


def _opciones(columnas, secciones=None, existentes=None, crear_nuevos=True) -> Opciones:
    opciones = Opciones(mapeo=Mapeo(columnas=dict(columnas)))
    if secciones is not None:
        opciones.mapeo.secciones = dict(secciones)
    if existentes is not None:
        opciones.existentes = existentes
    opciones.crear_nuevos = crear_nuevos
    return opciones


@pytest.mark.parametrize("delimitador", [",", ";", "\t"])
def test_detectar_delimitador(tmp_path, delimitador):
    ruta = _csv(tmp_path, [
        delimitador.join(["codigo", "nombre", "precio"]),
        delimitador.join(["A1", "Gaseosa", "100"]),
        delimitador.join(["A2", "Pizza", "250"]),
    ])

    deteccion = ImportadorCSV().detectar(ruta)

    assert deteccion.delimitador == delimitador
    assert deteccion.encabezados == ["codigo", "nombre", "precio"]


def test_detectar_delimitador_con_punto_y_coma(tmp_path):
    ruta = _csv(tmp_path, [
        "codigo;nombre;precio",
        "A1;Gaseosa;1.234,56",
        "A2;Pizza;2.500,00",
    ])

    assert ImportadorCSV().detectar(ruta).delimitador == ";"


def test_detectar_codificacion_utf8(tmp_path):
    ruta = tmp_path / "utf8.csv"
    ruta.write_bytes("codigo;nombre\nA1;Gaseosa con Ñoño\n".encode("utf-8"))

    assert detectar_codificacion(ruta) == "utf-8"


def test_detectar_codificacion_latin1(tmp_path):
    ruta = tmp_path / "latin1.csv"
    ruta.write_bytes("codigo;nombre\nA1;Gaseosa con Ñoño\n".encode("latin-1"))

    assert detectar_codificacion(ruta) == "latin-1"


def test_leer_un_archivo_latin1_conserva_los_acentos(tmp_path):
    ruta = tmp_path / "latin1.csv"
    ruta.write_bytes(
        "codigo;nombre;precio\nA1;Gaseosa Ñoño;100\n".encode("latin-1"))

    deteccion = ImportadorCSV().detectar(ruta)

    assert deteccion.filas[1][1] == "Gaseosa Ñoño"


def test_normalizar_saca_acentos_y_signos():
    assert normalizar("Código de Barras") == "codigodebarras"
    assert normalizar("PRECIO-VENTA (€)") == "precioventa"


def test_coincidir_columnas_por_alias_con_acentos():
    columnas = coincidir_columnas(["Descripción", "CÓDIGO", "Precio de Venta"])

    assert columnas == {"nombre": 0, "codigo": 1, "precio_venta": 2}


def test_coincidir_columnas_no_importa_el_orden():
    columnas = coincidir_columnas(["precio", "codigo", "nombre"])

    assert columnas == {"codigo": 1, "nombre": 2, "precio_venta": 0}


def test_coincidir_columnas_reconoce_el_codigo_de_barras():
    columnas = coincidir_columnas(["Código de barras", "Descripción", "Costo", "UM"])

    assert columnas["codigo"] == 0
    assert columnas["nombre"] == 1
    assert columnas["precio_costo"] == 2
    assert columnas["unidad_medida"] == 3


def test_coincidir_columnas_no_repite_columna():
    columnas = coincidir_columnas(["nombre", "descripcion"])

    assert columnas.get("nombre") is not None
    assert len(set(columnas.values())) == len(columnas)


def test_detectar_secciones_de_un_csv_con_bloques(tmp_path):
    ruta = _csv(tmp_path, [
        "CATALOGO",
        "Codigo;Nombre;Precio",
        "A1;Gaseosa;100",
        "A2;Pizza;250",
        "PRECIOS",
        "Codigo;Precio",
        "A3;300",
    ])

    deteccion = ImportadorCSV().detectar(ruta)

    assert [seccion.titulo for seccion in deteccion.secciones] == ["CATALOGO", "PRECIOS"]
    primera, segunda = deteccion.secciones
    assert primera.filas == [2, 3]
    assert primera.cabeceras == ["Codigo", "Nombre", "Precio"]
    assert primera.fila_inicio == 0
    assert primera.fila_fin == 3
    assert segunda.filas == [6]
    assert segunda.cabeceras == ["Codigo", "Precio"]
    assert segunda.tipo_sugerido == MODO_PRECIOS


def test_detectar_secciones_de_un_csv_sin_bloques(tmp_path):
    ruta = _csv(tmp_path, ["Codigo;Nombre", "A1;Gaseosa"])

    secciones = ImportadorCSV().detectar(ruta).secciones

    assert len(secciones) == 1
    assert secciones[0].filas == [1]
    assert secciones[0].cabeceras == ["Codigo", "Nombre"]


def test_detectar_secciones_marca_las_filas_vacias():
    filas = [["Codigo", "Nombre"], [], ["A1", "Gaseosa"]]

    secciones = detectar_secciones(filas)

    assert len(secciones) == 1
    assert secciones[0].filas == [2]


@pytest.mark.parametrize("texto,esperado", [
    ("1.234,56", 1234.56),
    ("1234.56", 1234.56),
    ("$ 1.234,56", 1234.56),
    ("1234", 1234.0),
])
def test_parsear_precio(texto, esperado):
    assert parsear_precio(texto) == pytest.approx(esperado)


def test_parsear_precio_de_un_texto_invalido():
    assert parsear_precio("no es un numero") is None
    assert parsear_precio("") is None


def test_importar_crea_los_productos_nuevos(tmp_path, servicio, base):
    ruta = _csv(tmp_path, ["Codigo;Nombre;Categoria;Precio", "A1;Gaseosa;Comidas;1.234,56"])

    resultado = servicio.importar(ruta, _opciones(
        {"codigo": 0, "nombre": 1, "categoria": 2, "precio_venta": 3}))

    assert resultado.creados == 1
    assert resultado.actualizados == 0
    assert resultado.errores == []
    producto = ProductoRepositorio(base).buscar("A1")
    assert producto is not None
    assert producto.nombre == "Gaseosa"
    assert producto.categoria == "Comidas"
    assert producto.precio_venta == pytest.approx(1234.56)


def test_los_productos_nuevos_nacen_con_los_valores_por_defecto(tmp_path, servicio, base):
    ruta = _csv(tmp_path, ["Codigo;Nombre;Precio", "A1;Gaseosa;100"])

    servicio.importar(ruta, _opciones({"codigo": 0, "nombre": 1, "precio_venta": 2}))

    producto = ProductoRepositorio(base).buscar("A1")
    assert producto.stock_actual == 0
    assert producto.stock_minimo == 0
    assert producto.alicuota_iva == Producto.ALICUOTA_POR_DEFECTO
    assert producto.precio_oferta == 0


def test_importar_actualiza_el_precio_y_el_nombre_de_los_existentes(tmp_path, servicio, base):
    _guardar(base, "A1", "Gaseosa vieja", precio_venta=100.0, stock=7)
    ruta = _csv(tmp_path, ["Codigo;Nombre;Precio", "A1;Gaseosa nueva;250"])

    resultado = servicio.importar(ruta, _opciones(
        {"codigo": 0, "nombre": 1, "precio_venta": 2}))

    assert resultado.creados == 0
    assert resultado.actualizados == 1
    producto = ProductoRepositorio(base).buscar("A1")
    assert producto.nombre == "Gaseosa nueva"
    assert producto.precio_venta == pytest.approx(250.0)


def test_importar_omite_los_existentes_si_se_pide_omitirlos(tmp_path, servicio, base):
    _guardar(base, "A1", "Gaseosa vieja", precio_venta=100.0)
    ruta = _csv(tmp_path, ["Codigo;Nombre;Precio", "A1;Gaseosa nueva;250"])

    resultado = servicio.importar(ruta, _opciones(
        {"codigo": 0, "nombre": 1, "precio_venta": 2},
        existentes=EXISTENTE_OMITIR))

    assert resultado.actualizados == 0
    assert resultado.omitidos == 1
    producto = ProductoRepositorio(base).buscar("A1")
    assert producto.nombre == "Gaseosa vieja"
    assert producto.precio_venta == pytest.approx(100.0)


def test_importar_actualiza_solo_los_precios(tmp_path, servicio, base):
    _guardar(base, "A1", "Gaseosa vieja", precio_venta=100.0)
    ruta = _csv(tmp_path, ["Codigo;Nombre;Precio", "A1;Gaseosa nueva;250"])

    resultado = servicio.importar(ruta, _opciones(
        {"codigo": 0, "nombre": 1, "precio_venta": 2},
        existentes=EXISTENTE_ACTUALIZAR_PRECIOS))

    assert resultado.actualizados == 1
    producto = ProductoRepositorio(base).buscar("A1")
    assert producto.nombre == "Gaseosa vieja"
    assert producto.precio_venta == pytest.approx(250.0)


def test_un_producto_creado_y_actualizado_solo_cuenta_una_vez(tmp_path, servicio, base):
    ruta = _csv(tmp_path, [
        "CATALOGO",
        "Codigo;Nombre",
        "A1;Gaseosa",
        "PRECIOS",
        "Codigo;Precio",
        "A1;250",
    ])
    opciones = _opciones(
        {"codigo": 0, "nombre": 1},
        secciones={0: MODO_CATALOGO, 1: MODO_PRECIOS})

    resultado = servicio.importar(ruta, opciones)

    assert resultado.creados == 1
    assert resultado.actualizados == 0
    producto = ProductoRepositorio(base).buscar("A1")
    assert producto.precio_venta == pytest.approx(250.0)


def test_un_producto_omitido_no_cuenta_como_actualizado(tmp_path, servicio, base):
    _guardar(base, "A1", "Gaseosa", precio_venta=100.0)
    ruta = _csv(tmp_path, ["Codigo;Nombre;Precio", "A1;Gaseosa;250"])

    resultado = servicio.importar(ruta, _opciones(
        {"codigo": 0, "nombre": 1, "precio_venta": 2},
        existentes=EXISTENTE_OMITIR))

    assert resultado.omitidos == 1
    assert resultado.actualizados == 0


def test_importar_salta_las_filas_invalidas_y_las_reporta(tmp_path, servicio, base):
    ruta = _csv(tmp_path, [
        "Codigo;Nombre;Precio",
        "A1;Gaseosa;100",
        ";Sin codigo;200",
        "A3;;300",
        "A4;Gaseosa 4;no es un precio",
    ])

    resultado = servicio.importar(ruta, _opciones(
        {"codigo": 0, "nombre": 1, "precio_venta": 2}))

    assert resultado.creados == 1
    assert len(resultado.errores) == 3
    numeros = [numero for numero, _ in resultado.errores]
    assert numeros == [3, 4, 5]
    assert "código" in resultado.errores[0][1]
    assert "nombre" in resultado.errores[1][1]
    assert ProductoRepositorio(base).buscar("A2") is None


def test_importar_no_modifica_el_stock_de_los_existentes(tmp_path, servicio, base):
    _guardar(base, "A1", "Gaseosa", precio_venta=100.0, stock=42)
    ruta = _csv(tmp_path, ["Codigo;Nombre;Precio;Stock", "A1;Gaseosa nueva;250;999"])

    servicio.importar(ruta, _opciones(
        {"codigo": 0, "nombre": 1, "precio_venta": 2}))

    producto = ProductoRepositorio(base).buscar("A1")
    assert producto.stock_actual == 42


def test_la_seccion_de_stock_se_ignora(tmp_path, servicio, base):
    ruta = _csv(tmp_path, [
        "CATALOGO",
        "Codigo;Nombre",
        "A1;Gaseosa",
        "STOCK",
        "Codigo;Stock",
        "A1;500",
    ])
    opciones = _opciones(
        {"codigo": 0, "nombre": 1},
        secciones={0: MODO_CATALOGO, 1: MODO_STOCK})

    resultado = servicio.importar(ruta, opciones)

    assert resultado.creados == 1
    producto = ProductoRepositorio(base).buscar("A1")
    assert producto.stock_actual == 0


def test_la_seccion_de_precios_actualiza_solo_el_precio(tmp_path, servicio, base):
    _guardar(base, "A1", "Gaseosa", precio_venta=100.0, stock=9)
    ruta = _csv(tmp_path, [
        "CATALOGO",
        "Codigo;Nombre",
        "A2;Pizza",
        "PRECIOS",
        "Codigo;Precio",
        "A1;250",
    ])
    opciones = _opciones(
        {"codigo": 0, "nombre": 1},
        secciones={0: MODO_CATALOGO, 1: MODO_PRECIOS})

    resultado = servicio.importar(ruta, opciones)

    assert resultado.creados == 1
    assert resultado.actualizados == 1
    producto = ProductoRepositorio(base).buscar("A1")
    assert producto.precio_venta == pytest.approx(250.0)
    assert producto.nombre == "Gaseosa"
    assert producto.stock_actual == 9


def test_una_seccion_ignorada_no_importa_nada(tmp_path, servicio, base):
    ruta = _csv(tmp_path, [
        "CATALOGO",
        "Codigo;Nombre",
        "A1;Gaseosa",
    ])
    opciones = _opciones({"codigo": 0, "nombre": 1}, secciones={0: MODO_IGNORAR})

    resultado = servicio.importar(ruta, opciones)

    assert resultado.creados == 0
    assert ProductoRepositorio(base).buscar("A1") is None


def test_el_precio_con_iva_se_divide(tmp_path, servicio, base):
    ruta = _csv(tmp_path, ["Codigo;Nombre;Precio", "A1;Gaseosa;121"])
    opciones = _opciones({"codigo": 0, "nombre": 1, "precio_venta": 2})
    opciones.mapeo.tipo_precio = "con_iva"

    servicio.importar(ruta, opciones)

    producto = ProductoRepositorio(base).buscar("A1")
    assert producto.precio_venta == pytest.approx(100.0)


def test_el_precio_del_archivo_se_importa_como_costo(tmp_path, servicio, base):
    ruta = _csv(tmp_path, ["Codigo;Nombre;Precio", "A1;Gaseosa;80"])
    opciones = _opciones({"codigo": 0, "nombre": 1, "precio_venta": 2})
    opciones.mapeo.tipo_precio = "costo"

    servicio.importar(ruta, opciones)

    producto = ProductoRepositorio(base).buscar("A1")
    assert producto.precio_costo == pytest.approx(80.0)
    assert producto.precio_venta == 0


def test_un_precio_negativo_se_importa_como_cero_con_aviso(tmp_path, servicio, base):
    ruta = _csv(tmp_path, ["Codigo;Nombre;Precio", "A1;Gaseosa;-50"])

    resultado = servicio.importar(ruta, _opciones(
        {"codigo": 0, "nombre": 1, "precio_venta": 2}))

    producto = ProductoRepositorio(base).buscar("A1")
    assert producto.precio_venta == 0
    assert resultado.avisos


def test_si_una_falla_a_la_medio_no_queda_nada_importado(tmp_path, servicio, base, monkeypatch):
    ruta = _csv(tmp_path, ["Codigo;Nombre", "A1;Gaseosa", "A2;Pizza"])
    original = ServicioImportacion._crear
    llamadas: list[str] = []

    def _crear(self, conexion, fila, codigo, resultado):
        llamadas.append(codigo)
        if len(llamadas) == 2:
            raise RuntimeError("se rompio a la mitad")
        return original(self, conexion, fila, codigo, resultado)

    monkeypatch.setattr(ServicioImportacion, "_crear", _crear)

    with pytest.raises(RuntimeError):
        servicio.importar(ruta, _opciones({"codigo": 0, "nombre": 1}))

    assert ProductoRepositorio(base).listar() == []
    assert servicio.importaciones.historial() == []


def test_la_importacion_queda_registrada_en_el_historial(tmp_path, servicio):
    ruta = _csv(tmp_path, ["Codigo;Nombre;Precio", "A1;Gaseosa;100"])

    servicio.importar(ruta, _opciones({"codigo": 0, "nombre": 1, "precio_venta": 2}))

    historial = servicio.importaciones.historial()
    assert len(historial) == 1
    registro = historial[0]
    assert registro["archivo"] == "lista.csv"
    assert registro["creados"] == 1
    assert registro["errores"] == 0
    assert Path(registro["backup"]).is_file()


def test_deshacer_restaura_el_backup_y_deja_el_stock_como_estaba(tmp_path, servicio, base):
    _guardar(base, "A1", "Gaseosa", precio_venta=100.0, stock=12)
    ruta = _csv(tmp_path, ["Codigo;Nombre;Precio", "A1;Gaseosa nueva;250"])

    servicio.importar(ruta, _opciones(
        {"codigo": 0, "nombre": 1, "precio_venta": 2}))
    assert ProductoRepositorio(base).buscar("A1").nombre == "Gaseosa nueva"

    assert servicio.deshacer() is True

    producto = ProductoRepositorio(base).buscar("A1")
    assert producto.nombre == "Gaseosa"
    assert producto.precio_venta == pytest.approx(100.0)
    assert producto.stock_actual == 12
    assert servicio.importaciones.historial() == []


def test_deshacer_sin_importaciones_no_hace_nada(servicio):
    assert servicio.deshacer() is False


def test_el_plan_gratis_limita_las_importaciones(tmp_path, servicio):
    ruta = _csv(tmp_path, ["Codigo;Nombre", "A1;Gaseosa"])
    opciones = _opciones({"codigo": 0, "nombre": 1})

    assert servicio.limite_alcanzado() is False
    servicio.importar(ruta, opciones)
    assert servicio.limite_alcanzado() is True
    assert PLAN_GRATIS["limites"]["importaciones"] == 1


def test_el_plan_gratis_recorta_las_filas_nuevas_sobre_el_limite(tmp_path, servicio, base):
    for numero in range(PLAN_GRATIS["limites"]["productos"]):
        _guardar(base, f"P{numero:03d}", f"Producto {numero}")
    _guardar(base, "A1", "Existente")
    ruta = _csv(tmp_path, [
        "Codigo;Nombre",
        "N1;Nueva 1",
        "N2;Nueva 2",
        "N3;Nueva 3",
        "A1;Actualizada",
    ])

    resultado = servicio.importar(ruta, _opciones({"codigo": 0, "nombre": 1}))

    assert resultado.creados == 0
    assert resultado.recortados == 3
    assert any("quedaron fuera" in aviso for aviso in resultado.avisos)
    repositorio = ProductoRepositorio(base)
    assert repositorio.buscar("N1") is None
    assert repositorio.buscar("N3") is None
    assert repositorio.buscar("A1").nombre == "Actualizada"


def test_el_asistente_no_arranca_cuando_se_alcanzo_el_limite(tmp_path, servicio, aplicacion, monkeypatch):
    ruta = _csv(tmp_path, ["Codigo;Nombre", "A1;Gaseosa"])
    servicio.importar(ruta, _opciones({"codigo": 0, "nombre": 1}))
    avisos: list[str] = []
    monkeypatch.setattr(AvisoPlanGratis, "exec", lambda self: avisos.append("mostrado"))

    asistente = ImportadorProductos(servicio)

    assert asistente.exec() == QDialog.DialogCode.Rejected
    assert avisos == ["mostrado"]
    _cerrar(asistente)


def test_el_asistente_importa_de_punta_a_punta(tmp_path, servicio, base, aplicacion):
    ruta = _csv(tmp_path, [
        "CATALOGO",
        "Codigo;Nombre;Precio",
        "A1;Gaseosa;100",
        "A2;Pizza;250",
    ])
    asistente = ImportadorProductos(servicio)

    asistente.cargar_archivo(ruta)
    assert asistente._paginas.currentIndex() == 0
    assert asistente.tblMuestra.rowCount() == 4

    asistente.siguiente()
    assert asistente._paginas.currentIndex() == 1
    assert asistente.tblSecciones.rowCount() == 1
    assert asistente.tblMapeo.rowCount() == 6

    asistente.siguiente()
    assert asistente._paginas.currentIndex() == 2
    assert asistente.tblPrevia.rowCount() == 2

    asistente.importar()
    assert asistente._paginas.currentIndex() == 3
    assert ProductoRepositorio(base).buscar("A1") is not None
    assert ProductoRepositorio(base).buscar("A2") is not None
    assert asistente.btnDeshacer.isEnabled()
    _cerrar(asistente)


def test_el_asistente_muestra_los_errores_de_la_importacion(tmp_path, servicio, aplicacion):
    ruta = _csv(tmp_path, ["Codigo;Nombre", "A1;Gaseosa", ";Sin codigo"])
    asistente = ImportadorProductos(servicio)

    asistente.cargar_archivo(ruta)
    asistente.siguiente()
    asistente.siguiente()
    asistente.importar()

    assert asistente._paginas.currentIndex() == 3
    assert asistente.tblErrores.rowCount() == 1
    assert asistente.tblErrores.item(0, 0).text() == "3"
    _cerrar(asistente)


def test_el_asistente_deshace_la_importacion_con_confirmacion(
    tmp_path, servicio, base, aplicacion, monkeypatch
):
    _guardar(base, "A1", "Gaseosa", precio_venta=100.0, stock=5)
    ruta = _csv(tmp_path, ["Codigo;Nombre;Precio", "A1;Gaseosa nueva;250"])
    asistente = ImportadorProductos(servicio)

    asistente.cargar_archivo(ruta)
    asistente.siguiente()
    asistente.siguiente()
    asistente.importar()
    assert ProductoRepositorio(base).buscar("A1").nombre == "Gaseosa nueva"

    preguntas: list[str] = []
    monkeypatch.setattr(
        ImportadorProductos, "_confirmar",
        lambda _self, titulo, pregunta: preguntas.append(pregunta) or True)

    asistente.deshacer()

    assert preguntas
    producto = ProductoRepositorio(base).buscar("A1")
    assert producto.nombre == "Gaseosa"
    assert producto.precio_venta == pytest.approx(100.0)
    assert producto.stock_actual == 5
    assert servicio.importaciones.historial() == []
    assert asistente.btnDeshacer.isEnabled() is False
    _cerrar(asistente)
