from __future__ import annotations

from datetime import datetime
from pathlib import Path

from models.producto import Producto
from repositories.importacion_repositorio import ImportacionRepositorio
from repositories.producto_repositorio import ProductoRepositorio
from repositories.sqlite import conectar, ruta_db
from services.backup import ServicioBackup
from services.importador.csv_importador import ImportadorCSV
from services.importador.modelo import (
    Deteccion,
    EXISTENTE_ACTUALIZAR_PRECIOS,
    EXISTENTE_OMITIR,
    FilaMapeada,
    Opciones,
    ResultadoImportacion,
)
from services.plan_motor import limite
from utils.formato import parsear_fecha

_COLUMNAS = (
    "codigo, nombre, categoria, unidad_medida, precio_costo, precio_venta,"
    " stock_actual, stock_minimo, alicuota_iva, precio_oferta,"
    " fecha_vencimiento"
)

_CAMPOS_TEXTO = ("nombre", "categoria", "unidad_medida")
_CAMPOS_PRECIO = ("precio_costo", "precio_venta")


class ErrorImportacion(RuntimeError):
    pass


class ServicioImportacion:

    def __init__(
        self,
        productos: ProductoRepositorio,
        importaciones: ImportacionRepositorio | None = None,
        backup: ServicioBackup | None = None,
        base: str | Path | None = None,
    ) -> None:
        self._productos = productos
        self._base = ruta_db(base if base is not None else productos.ruta_archivo)
        self._importaciones = (
            importaciones if importaciones is not None
            else ImportacionRepositorio(self._base)
        )
        self._backup = backup if backup is not None else ServicioBackup(base=self._base)
        self._importador = ImportadorCSV()

    @property
    def base(self) -> Path:
        return self._base

    @property
    def backup(self) -> ServicioBackup:
        return self._backup

    @property
    def importaciones(self) -> ImportacionRepositorio:
        return self._importaciones

    @property
    def importador(self):
        return self._importador

    def importaciones_realizadas(self) -> int:
        return self._importaciones.total()

    def limite_alcanzado(self) -> bool:
        maximo = limite("importaciones")
        if maximo is None:
            return False
        return self.importaciones_realizadas() >= maximo

    def importadores_disponibles(self) -> list[dict]:
        # Edición libre: no hay plugins premium externos.
        return []

    def usar_importador(self, clase) -> None:
        if clase is None:
            self._importador = ImportadorCSV()
            return
        try:
            self._importador = clase() if isinstance(clase, type) else clase
        except Exception:
            self._importador = ImportadorCSV()

    def producto_por_codigo(self, codigo: str) -> Producto | None:
        return self._productos.buscar(codigo)

    def detectar(self, ruta: str | Path) -> Deteccion:
        return self._importador.detectar(ruta)

    def previsualizar(self, ruta: str | Path, opciones: Opciones) -> list[FilaMapeada]:
        deteccion = self._importador.detectar(ruta)
        return self._importador.parsear(
            ruta, opciones.mapeo, deteccion.secciones, deteccion)

    def importar(self, ruta: str | Path, opciones: Opciones) -> ResultadoImportacion:
        ruta = Path(ruta)
        resultado = ResultadoImportacion(archivo=str(ruta))
        filas = self.previsualizar(ruta, opciones)
        copia = self._backup.generar()
        resultado.backup = str(copia)
        conexion = conectar(self._base)
        conexion.isolation_level = None
        try:
            conexion.execute("BEGIN IMMEDIATE")
            self._aplicar_filas(conexion, filas, opciones, resultado)
            self._importaciones.registrar(
                archivo=ruta.name,
                creados=resultado.creados,
                actualizados=resultado.actualizados,
                omitidos=resultado.omitidos,
                errores=len(resultado.errores),
                backup=str(copia),
                fecha=datetime.now().isoformat(timespec="seconds"),
                conexion=conexion,
            )
            conexion.execute("COMMIT")
        except BaseException:
            try:
                conexion.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            conexion.close()
        return resultado

    def deshacer(self, id_importacion: int | None = None) -> bool:
        registro = (
            self._importaciones.obtener(id_importacion)
            if id_importacion is not None
            else self._importaciones.ultima()
        )
        if registro is None:
            return False
        copia = str(registro.get("backup") or "")
        if not copia or not Path(copia).is_file():
            raise ErrorImportacion(
                "No se encontró la copia de seguridad de la importación.")
        self._backup.restaurar(copia)
        self._importaciones.eliminar(int(registro["id"]))
        return True

    def _aplicar_filas(
        self,
        conexion,
        filas: list[FilaMapeada],
        opciones: Opciones,
        resultado: ResultadoImportacion,
    ) -> None:
        creados: set[str] = set()
        actualizados: set[str] = set()
        omitidos: set[str] = set()
        cupo = self._cupo_productos(conexion)
        recortados = 0
        total_nuevos = 0
        for fila in filas:
            resultado.avisos.extend(fila.avisos)
            if fila.errores:
                for motivo in fila.errores:
                    resultado.errores.append((fila.numero, motivo))
                continue
            codigo = str(fila.valores.get("codigo") or "").strip()
            if not codigo:
                resultado.errores.append((fila.numero, "Falta el código del producto."))
                continue
            if "nombre" in fila.valores and not str(fila.valores["nombre"]).strip():
                resultado.errores.append((fila.numero, "Falta el nombre del producto."))
                continue
            existente = self._buscar(conexion, codigo)
            if existente is None:
                if not opciones.crear_nuevos:
                    omitidos.add(codigo)
                    continue
                if cupo is not None and cupo <= 0:
                    total_nuevos += 1
                    continue
                if self._crear(conexion, fila, codigo, resultado):
                    creados.add(codigo)
                    if cupo is not None:
                        cupo -= 1
            else:
                if self._actualizar(conexion, fila, codigo, opciones, resultado):
                    if codigo not in creados:
                        actualizados.add(codigo)
                else:
                    omitidos.add(codigo)
        resultado.creados = len(creados)
        resultado.actualizados = len(actualizados)
        resultado.omitidos = len(omitidos)
        resultado.recortados = total_nuevos
        if total_nuevos:
            titulo = "Gratis"
            maximo = limite("productos")
            resultado.avisos.append(
                f"Límite del plan {titulo}: admite hasta {maximo} productos; "
                f"{total_nuevos} filas nuevas quedaron fuera de la importación.")

    def _cupo_productos(self, conexion) -> int | None:
        """Cupos disponibles según el límite de productos del plan; None ilimitado."""
        maximo = limite("productos")
        if maximo is None:
            return None
        total = conexion.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
        return max(0, maximo - int(total))

    def _buscar(self, conexion, codigo: str):
        return conexion.execute(
            f"SELECT {_COLUMNAS} FROM productos WHERE codigo = ?", (codigo,)).fetchone()

    def _crear(
        self,
        conexion,
        fila: FilaMapeada,
        codigo: str,
        resultado: ResultadoImportacion,
    ) -> bool:
        try:
            producto = Producto(
                codigo=codigo,
                nombre=str(fila.valores.get("nombre") or codigo),
                categoria=str(fila.valores.get("categoria") or ""),
                unidad_medida=str(fila.valores.get("unidad_medida") or ""),
                precio_costo=fila.precios.get("precio_costo", 0.0),
                precio_venta=fila.precios.get("precio_venta", 0.0),
                fecha_vencimiento=self._fecha_de_vencimiento(fila, resultado),
            )
        except ValueError as error:
            resultado.errores.append((fila.numero, str(error)))
            return False
        datos = producto.to_dict()
        conexion.execute(
            f"INSERT INTO productos({_COLUMNAS})"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            tuple(datos[columna] for columna in Producto.COLUMNAS),
        )
        return True

    def _actualizar(
        self,
        conexion,
        fila: FilaMapeada,
        codigo: str,
        opciones: Opciones,
        resultado: ResultadoImportacion,
    ) -> bool:
        if opciones.existentes == EXISTENTE_OMITIR:
            return False
        campos = self._campos_a_actualizar(fila, opciones, resultado)
        if not campos:
            return False
        columnas = ", ".join(f"{campo} = ?" for campo in campos)
        valores = list(campos.values()) + [codigo]
        conexion.execute(
            f"UPDATE productos SET {columnas} WHERE codigo = ?", valores)
        return True

    def _campos_a_actualizar(
        self, fila: FilaMapeada, opciones: Opciones, resultado: ResultadoImportacion,
    ) -> dict:
        campos: dict[str, object] = {}
        if opciones.existentes != EXISTENTE_ACTUALIZAR_PRECIOS:
            for campo in _CAMPOS_TEXTO:
                valor = str(fila.valores.get(campo) or "").strip()
                if valor:
                    campos[campo] = valor
            fecha = self._fecha_de_vencimiento(fila, resultado)
            if fecha is not None:
                campos["fecha_vencimiento"] = fecha.isoformat()
        for campo in _CAMPOS_PRECIO:
            if campo in fila.precios:
                campos[campo] = fila.precios[campo]
        return campos

    @staticmethod
    def _fecha_de_vencimiento(fila: FilaMapeada, resultado: ResultadoImportacion):
        texto = str(fila.valores.get("fecha_vencimiento") or "").strip()
        if not texto:
            return None
        fecha = parsear_fecha(texto)
        if fecha is None:
            resultado.avisos.append(
                f"Vencimiento inválido en la fila {fila.numero}: '{texto}'.")
        return fecha
