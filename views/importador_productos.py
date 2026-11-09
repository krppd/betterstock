from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QBrush, QColor, QDesktopServices
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config import OUTPUT_DIR
from services.importador.modelo import (
    Deteccion,
    EXISTENTE_ACTUALIZAR_PRECIOS,
    EXISTENTE_ACTUALIZAR_TODO,
    EXISTENTE_OMITIR,
    MODO_CATALOGO,
    MODO_IGNORAR,
    MODO_PRECIOS,
    MODO_STOCK,
    Opciones,
    PRECIO_CON_IVA,
    PRECIO_COSTO,
    PRECIO_VENTA,
    ResultadoImportacion,
)
from services.importador.servicio import ServicioImportacion
from services.plan_motor import CONTACTO, limite
from ui.estilos import AMBAR_TEXTO, ROJO_TEXTO
from utils.formato import formatear_dinero

CAMPOS = (
    ("codigo", "Código"),
    ("nombre", "Nombre"),
    ("categoria", "Categoría"),
    ("unidad_medida", "Unidad de medida"),
    ("precio_costo", "Precio de costo"),
    ("precio_venta", "Precio de venta"),
)

MODOS_SECCION = (
    (MODO_IGNORAR, "Ignorar"),
    (MODO_CATALOGO, "Catálogo (código + nombre)"),
    (MODO_PRECIOS, "Precios (por código)"),
    (MODO_STOCK, "Stock (por código)"),
)

SIN_COLUMNAS = "— no importar —"
FORMATO_CSV = "CSV o TXT (columnas separadas por coma, punto y coma o tab)"


class ImportadorProductos(QDialog):

    FILAS_MUESTRA = 8
    FILAS_PREVIA = 10

    def __init__(
        self,
        servicio: ServicioImportacion,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._servicio = servicio
        self._deteccion: Deteccion | None = None
        self._resultado: ResultadoImportacion | None = None
        self._opciones = Opciones()
        self._combos_columna: dict[str, QComboBox] = {}
        self._combos_seccion: list[QComboBox] = []
        self.setWindowTitle("Importar lista de productos")
        self.setMinimumSize(780, 560)
        self.resize(900, 640)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        self._paginas = QStackedWidget(self)
        layout.addWidget(self._paginas, 1)
        self._paginas.addWidget(self._pagina_archivo())
        self._paginas.addWidget(self._pagina_mapeo())
        self._paginas.addWidget(self._pagina_opciones())
        self._paginas.addWidget(self._pagina_resultado())
        layout.addLayout(self._armar_botones())
        self._actualizar_botones()

    def exec(self) -> int:
        if self._servicio.limite_alcanzado():
            AvisoPlanGratis(self).exec()
            return QDialog.DialogCode.Rejected
        return super().exec()

    def cargar_archivo(self, ruta: str | Path) -> None:
        try:
            deteccion = self._servicio.detectar(ruta)
        except Exception as error:
            self._avisar("No se pudo leer el archivo", str(error))
            return
        self._deteccion = deteccion
        self.txtArchivo.setText(str(ruta))
        self._llenar_muestra(deteccion)
        self._llenar_resumen(deteccion)
        self._llenar_secciones(deteccion)
        self._llenar_columnas(deteccion)
        self._actualizar_botones()

    def elegir_archivo(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Elegir lista de productos",
            str(OUTPUT_DIR),
            "Listas de productos (*.csv *.txt);;Todos los archivos (*)",
        )
        if not ruta:
            return
        self.cargar_archivo(ruta)

    def atras(self) -> None:
        self._ir_a(max(0, self._paginas.currentIndex() - 1))

    def siguiente(self) -> None:
        indice = self._paginas.currentIndex()
        if indice == 0:
            if self._deteccion is None:
                return
            self._ir_a(1)
        elif indice == 1:
            if not self._mapeo_completo():
                self._avisar(
                    "Faltan columnas",
                    "Indicá la columna del código y la del nombre del producto.",
                )
                return
            self._llenar_previa()
            self._ir_a(2)

    def importar(self) -> None:
        if self._deteccion is None:
            return
        opciones = self._opciones_actuales()
        try:
            resultado = self._servicio.importar(self._deteccion.ruta, opciones)
        except Exception as error:
            self._avisar("No se pudo importar la lista", str(error))
            return
        self._resultado = resultado
        self._llenar_resultado(resultado)
        self._ir_a(3)

    def resultado(self) -> ResultadoImportacion | None:
        """Resultado de la importación aplicada, o None si aún no hay."""
        return self._resultado

    def deshacer(self) -> None:
        if not self._confirmar(
            "Deshacer la importación",
            "Se va a restaurar la copia de seguridad tomada antes de importar.\n\n"
            "Se perderán los cambios hechos después de esa copia: ventas, "
            "movimientos de stock y todo lo demás.\n\n"
            "La importación no tocó el stock, pero al restaurar la copia se "
            "vuelve al estado de ese momento.\n\n¿Querés seguir?",
        ):
            return
        try:
            self._servicio.deshacer()
        except Exception as error:
            self._avisar("No se pudo deshacer la importación", str(error))
            return
        self.lblResultado.setText(
            self.lblResultado.text()
            + "\n\nSe deshizo la importación: la base de datos volvió al estado "
              "anterior a importarla."
        )
        self.lblResultado.setStyleSheet(f"color: {AMBAR_TEXTO};")
        self.tblErrores.setRowCount(0)
        self.btnDeshacer.setEnabled(False)

    def _pagina_archivo(self) -> QWidget:
        pagina = QWidget(self)
        layout = QVBoxLayout(pagina)
        fila = QHBoxLayout()
        self.txtArchivo = QLineEdit(pagina)
        self.txtArchivo.setReadOnly(True)
        self.txtArchivo.setPlaceholderText("Elegí el archivo con la lista de productos")
        self.btnElegir = QPushButton("Elegir archivo…", pagina)
        self.btnElegir.clicked.connect(self.elegir_archivo)
        fila.addWidget(self.txtArchivo, 1)
        fila.addWidget(self.btnElegir)
        layout.addLayout(fila)
        self.lblResumen = QLabel("", pagina)
        self.lblResumen.setWordWrap(True)
        layout.addWidget(self.lblResumen)
        self.tblMuestra = QTableWidget(pagina)
        self.tblMuestra.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblMuestra.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.tblMuestra, 1)
        layout.addLayout(self._fila_formato())
        return pagina

    def _fila_formato(self) -> QHBoxLayout:
        fila = QHBoxLayout()
        self.cmbFormato = QComboBox(self)
        self.cmbFormato.addItem(FORMATO_CSV, None)
        for extra in self._servicio.importadores_disponibles():
            self.cmbFormato.addItem(extra["nombre"], extra["clase"])
        self.cmbFormato.currentIndexChanged.connect(self._cambio_formato)
        fila.addWidget(QLabel("Formato del archivo:", self))
        fila.addWidget(self.cmbFormato, 1)
        return fila

    def _cambio_formato(self) -> None:
        self._servicio.usar_importador(self.cmbFormato.currentData())
        if self._deteccion is not None:
            self.cargar_archivo(self._deteccion.ruta)

    def _pagina_mapeo(self) -> QWidget:
        pagina = QWidget(self)
        layout = QVBoxLayout(pagina)
        layout.setSpacing(8)

        caja_secciones = QGroupBox("Secciones del archivo", pagina)
        secciones = QVBoxLayout(caja_secciones)
        self.tblSecciones = QTableWidget(caja_secciones)
        self.tblSecciones.setColumnCount(3)
        self.tblSecciones.setHorizontalHeaderLabels(["Sección", "Filas", "Qué hacer"])
        self.tblSecciones.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblSecciones.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        secciones.addWidget(self.tblSecciones)
        layout.addWidget(caja_secciones, 1)

        caja_columnas = QGroupBox("Columnas del archivo", pagina)
        columnas = QVBoxLayout(caja_columnas)
        self.tblMapeo = QTableWidget(caja_columnas)
        self.tblMapeo.setColumnCount(3)
        self.tblMapeo.setHorizontalHeaderLabels(["Campo", "Columna", "Ejemplos"])
        self.tblMapeo.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblMapeo.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        columnas.addWidget(self.tblMapeo)
        layout.addWidget(caja_columnas, 1)

        fila = QHBoxLayout()
        self.cmbTipoPrecio = QComboBox(pagina)
        self.cmbTipoPrecio.addItem("Venta", PRECIO_VENTA)
        self.cmbTipoPrecio.addItem("Costo", PRECIO_COSTO)
        self.cmbTipoPrecio.addItem("Con IVA (se divide por 1,21)", PRECIO_CON_IVA)
        self.cmbTipoPrecio.currentIndexChanged.connect(self._cambio_tipo_precio)
        fila.addWidget(QLabel("¿El precio del archivo es?", pagina))
        fila.addWidget(self.cmbTipoPrecio)
        fila.addStretch(1)
        layout.addLayout(fila)
        return pagina

    def _pagina_opciones(self) -> QWidget:
        pagina = QWidget(self)
        layout = QVBoxLayout(pagina)
        layout.setSpacing(8)

        caja = QGroupBox("Productos que ya existen", pagina)
        opciones = QVBoxLayout(caja)
        self.rbActualizarTodo = QRadioButton(
            "Actualizar todo (nombre, categoría, unidad y precios)", caja)
        self.rbActualizarPrecios = QRadioButton(
            "Actualizar solo los precios", caja)
        self.rbOmitir = QRadioButton(
            "Omitir (dejarlos como están)", caja)
        self.rbActualizarTodo.setChecked(True)
        self._grupoExistentes = QButtonGroup(caja)
        self._grupoExistentes.addButton(self.rbActualizarTodo)
        self._grupoExistentes.addButton(self.rbActualizarPrecios)
        self._grupoExistentes.addButton(self.rbOmitir)
        opciones.addWidget(self.rbActualizarTodo)
        opciones.addWidget(self.rbActualizarPrecios)
        opciones.addWidget(self.rbOmitir)
        self.chkCrearNuevos = QCheckBox(
            "Crear los productos que todavía no existen", caja)
        self.chkCrearNuevos.setChecked(True)
        opciones.addWidget(self.chkCrearNuevos)
        layout.addWidget(caja)

        caja_previa = QGroupBox("Previsualización", pagina)
        previa = QVBoxLayout(caja_previa)
        self.tblPrevia = QTableWidget(caja_previa)
        self.tblPrevia.setColumnCount(8)
        self.tblPrevia.setHorizontalHeaderLabels(
            ["Línea", "Código", "Nombre", "Categoría", "Unidad", "Costo", "Venta", "Aviso"])
        self.tblPrevia.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblPrevia.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        previa.addWidget(self.tblPrevia)
        layout.addWidget(caja_previa, 1)
        return pagina

    def _pagina_resultado(self) -> QWidget:
        pagina = QWidget(self)
        layout = QVBoxLayout(pagina)
        layout.setSpacing(8)
        self.lblResultado = QLabel("", pagina)
        self.lblResultado.setWordWrap(True)
        layout.addWidget(self.lblResultado)
        self.tblErrores = QTableWidget(pagina)
        self.tblErrores.setColumnCount(2)
        self.tblErrores.setHorizontalHeaderLabels(["Línea", "Motivo"])
        self.tblErrores.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblErrores.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tblErrores, 1)
        fila = QHBoxLayout()
        self.btnDeshacer = QPushButton("Deshacer esta importación", pagina)
        self.btnDeshacer.clicked.connect(self.deshacer)
        self.btnCerrar = QPushButton("Cerrar", pagina)
        self.btnCerrar.setDefault(True)
        self.btnCerrar.clicked.connect(self.accept)
        fila.addWidget(self.btnDeshacer)
        fila.addStretch(1)
        fila.addWidget(self.btnCerrar)
        layout.addLayout(fila)
        return pagina

    def _armar_botones(self) -> QHBoxLayout:
        botones = QHBoxLayout()
        self.btnAtras = QPushButton("Atrás", self)
        self.btnCancelar = QPushButton("Cancelar", self)
        self.btnSiguiente = QPushButton("Siguiente", self)
        self.btnImportar = QPushButton("Importar", self)
        for boton in (self.btnAtras, self.btnCancelar, self.btnSiguiente, self.btnImportar):
            boton.setAutoDefault(False)
        self.btnAtras.clicked.connect(self.atras)
        self.btnCancelar.clicked.connect(self.reject)
        self.btnSiguiente.clicked.connect(self.siguiente)
        self.btnImportar.clicked.connect(self.importar)
        botones.addWidget(self.btnAtras)
        botones.addStretch(1)
        botones.addWidget(self.btnCancelar)
        botones.addWidget(self.btnSiguiente)
        botones.addWidget(self.btnImportar)
        return botones

    def _ir_a(self, indice: int) -> None:
        self._paginas.setCurrentIndex(indice)
        self._actualizar_botones()

    def _actualizar_botones(self) -> None:
        indice = self._paginas.currentIndex()
        self.btnAtras.setEnabled(indice > 0)
        self.btnAtras.setVisible(indice > 0)
        self.btnSiguiente.setVisible(indice < 2)
        if indice == 0:
            self.btnSiguiente.setEnabled(self._deteccion is not None)
        elif indice == 1:
            self.btnSiguiente.setEnabled(self._mapeo_completo())
        else:
            self.btnSiguiente.setEnabled(False)
        self.btnImportar.setVisible(indice == 2)
        self.btnCancelar.setVisible(indice < 3)

    def _llenar_muestra(self, deteccion: Deteccion) -> None:
        filas = deteccion.filas[:self.FILAS_MUESTRA]
        columnas = max((len(fila) for fila in filas), default=0)
        self.tblMuestra.setColumnCount(columnas)
        self.tblMuestra.setRowCount(len(filas))
        self.tblMuestra.setHorizontalHeaderLabels(
            [f"Columna {indice + 1}" for indice in range(columnas)])
        for indice_fila, fila in enumerate(filas):
            for indice_columna, celda in enumerate(fila):
                self.tblMuestra.setItem(
                    indice_fila, indice_columna, QTableWidgetItem(celda))

    def _llenar_resumen(self, deteccion: Deteccion) -> None:
        secciones = len(deteccion.secciones)
        separador = " · "
        partes = [
            f"Delimitador: {deteccion.delimitador!r}",
            f"Codificación: {deteccion.codificacion}",
            f"Filas: {len(deteccion.filas)}",
            f"Secciones: {secciones}",
        ]
        self.lblResumen.setText(separador.join(partes))

    def _llenar_secciones(self, deteccion: Deteccion) -> None:
        self._combos_seccion = []
        self.tblSecciones.setRowCount(len(deteccion.secciones))
        for indice, seccion in enumerate(deteccion.secciones):
            titulo = seccion.titulo or "(inicio del archivo)"
            self.tblSecciones.setItem(indice, 0, QTableWidgetItem(titulo))
            self.tblSecciones.setItem(
                indice, 1, QTableWidgetItem(str(len(seccion.filas))))
            combo = QComboBox(self.tblSecciones)
            for modo, etiqueta in MODOS_SECCION:
                combo.addItem(etiqueta, modo)
            posicion = combo.findData(seccion.tipo_sugerido)
            combo.setCurrentIndex(posicion if posicion >= 0 else 0)
            combo.currentIndexChanged.connect(self._cambio_seccion)
            self._combos_seccion.append(combo)
            self.tblSecciones.setCellWidget(indice, 2, combo)

    def _llenar_columnas(self, deteccion: Deteccion) -> None:
        self._combos_columna = {}
        self.tblMapeo.setRowCount(len(CAMPOS))
        for indice, (campo, etiqueta) in enumerate(CAMPOS):
            self.tblMapeo.setItem(indice, 0, QTableWidgetItem(etiqueta))
            combo = QComboBox(self.tblMapeo)
            combo.addItem(SIN_COLUMNAS, -1)
            for columna in deteccion.columnas:
                combo.addItem(columna.nombre, columna.indice)
            Automatico = deteccion.mapeo.get(campo, -1)
            posicion = combo.findData(Automatico)
            combo.setCurrentIndex(posicion if posicion >= 0 else 0)
            combo.currentIndexChanged.connect(
                lambda _indice, el_campo=campo: self._cambio_columna(el_campo))
            self._combos_columna[campo] = combo
            self.tblMapeo.setCellWidget(indice, 1, combo)
            self.tblMapeo.setItem(indice, 2, QTableWidgetItem(""))
            self._cambio_columna(campo)

    def _cambio_columna(self, campo: str) -> None:
        combo = self._combos_columna.get(campo)
        if combo is None or self._deteccion is None:
            return
        indice = combo.currentData()
        fila = [clave for clave, _ in CAMPOS].index(campo)
        ejemplos: list[str] = []
        for columna in self._deteccion.columnas:
            if columna.indice == indice:
                ejemplos = columna.ejemplos
                break
        item = self.tblMapeo.item(fila, 2)
        texto = " · ".join(ejemplos) if ejemplos else "—"
        if item is None:
            item = QTableWidgetItem("")
            self.tblMapeo.setItem(fila, 2, item)
        item.setText(texto)

    def _cambio_seccion(self) -> None:
        self._actualizar_botones()

    def _cambio_tipo_precio(self) -> None:
        self._opciones.mapeo.tipo_precio = self.cmbTipoPrecio.currentData()

    def _mapeo_actual(self) -> dict[str, int]:
        columnas: dict[str, int] = {}
        for campo, combo in self._combos_columna.items():
            indice = combo.currentData()
            if indice is not None and int(indice) >= 0:
                columnas[campo] = int(indice)
        return columnas

    def _modos_actuales(self) -> dict[int, str]:
        modos: dict[int, str] = {}
        for indice, combo in enumerate(self._combos_seccion):
            modos[indice] = combo.currentData()
        return modos

    def _opciones_actuales(self) -> Opciones:
        if self.rbOmitir.isChecked():
            existentes = EXISTENTE_OMITIR
        elif self.rbActualizarPrecios.isChecked():
            existentes = EXISTENTE_ACTUALIZAR_PRECIOS
        else:
            existentes = EXISTENTE_ACTUALIZAR_TODO
        opciones = Opciones(
            mapeo=self._opciones.mapeo,
            existentes=existentes,
            crear_nuevos=self.chkCrearNuevos.isChecked(),
        )
        opciones.mapeo.columnas = self._mapeo_actual()
        opciones.mapeo.secciones = self._modos_actuales()
        opciones.mapeo.tipo_precio = self.cmbTipoPrecio.currentData()
        return opciones

    def _mapeo_completo(self) -> bool:
        columnas = self._mapeo_actual()
        if "codigo" not in columnas:
            return False
        modos = self._modos_actuales()
        if any(modo == MODO_CATALOGO for modo in modos.values()):
            return "nombre" in columnas
        return True

    def _llenar_previa(self) -> None:
        if self._deteccion is None:
            return
        opciones = self._opciones_actuales()
        try:
            filas = self._servicio.previsualizar(self._deteccion.ruta, opciones)
        except Exception as error:
            self._avisar("No se pudo leer la lista", str(error))
            return
        mostrar = filas[:self.FILAS_PREVIA]
        self.tblPrevia.setRowCount(len(mostrar))
        for indice, fila in enumerate(mostrar):
            codigo = fila.valores.get("codigo", "")
            actual = self._servicio.producto_por_codigo(codigo) if codigo else None
            color = self._color_de_fila(fila, actual)
            valores = [
                str(fila.numero),
                codigo,
                fila.valores.get("nombre", ""),
                fila.valores.get("categoria", ""),
                fila.valores.get("unidad_medida", ""),
                self._precio_texto(fila, "precio_costo"),
                self._precio_texto(fila, "precio_venta"),
                " · ".join(fila.avisos + fila.errores),
            ]
            for columna, texto in enumerate(valores):
                item = QTableWidgetItem(texto)
                if color:
                    item.setForeground(QBrush(QColor(color)))
                self.tblPrevia.setItem(indice, columna, item)

    def _precio_texto(self, fila, campo: str) -> str:
        if campo not in fila.precios:
            return ""
        return formatear_dinero(fila.precios[campo])

    def _color_de_fila(self, fila, actual) -> str | None:
        if fila.errores:
            return ROJO_TEXTO
        if fila.avisos:
            return AMBAR_TEXTO
        for campo in ("precio_venta", "precio_costo"):
            nuevo = fila.precios.get(campo)
            if nuevo is None:
                continue
            if nuevo <= 0:
                return AMBAR_TEXTO
            if actual is None:
                continue
            viejo = float(getattr(actual, campo, 0.0) or 0.0)
            if viejo > 0 and (nuevo < viejo / 2 or nuevo > viejo * 2):
                return AMBAR_TEXTO
        return None

    def _llenar_resultado(self, resultado: ResultadoImportacion) -> None:
        self.lblResultado.setStyleSheet("")
        self.lblResultado.setText(
            f"Importación terminada.\n"
            f"Creados: {resultado.creados} · "
            f"Actualizados: {resultado.actualizados} · "
            f"Omitidos: {resultado.omitidos} · "
            f"Errores: {len(resultado.errores)}"
        )
        self.tblErrores.setRowCount(len(resultado.errores))
        for indice, (numero, motivo) in enumerate(resultado.errores):
            self.tblErrores.setItem(indice, 0, QTableWidgetItem(str(numero)))
            self.tblErrores.setItem(indice, 1, QTableWidgetItem(motivo))
        self.btnDeshacer.setEnabled(resultado.creados + resultado.actualizados > 0)

    def _avisar(self, titulo: str, mensaje: str) -> None:
        QMessageBox.warning(self, titulo, mensaje)

    def _confirmar(self, titulo: str, pregunta: str) -> bool:
        respuesta = QMessageBox.question(
            self, titulo, pregunta,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return respuesta == QMessageBox.StandardButton.Yes


class AvisoPlanGratis(QDialog):

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Plan Gratis")
        self.setMinimumWidth(460)

        maximo = limite("importaciones")
        titulo = "Gratis"
        permisos = f"{maximo} importación" if maximo is not None else "importaciones sin límite"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        titulo_label = QLabel("Llegaste al límite del plan Gratis", self)
        titulo_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(titulo_label)

        texto = QLabel(
            f"El plan {titulo} permite {permisos} de "
            "listas de productos, y ya la usaste.\n\n"
            "Las importaciones ilimitadas, con historial y deshacer, son del plan "
            "Mensual.\n\n"
            "Escribinos y lo activamos en el momento.",
            self,
        )
        texto.setWordWrap(True)
        layout.addWidget(texto)

        botones = QHBoxLayout()
        self.btnCorreo = QPushButton(f"Escribir a {CONTACTO}", self)
        self.btnCerrar = QPushButton("Entendido", self)
        self.btnCerrar.setDefault(True)
        self.btnCorreo.clicked.connect(self._escribir)
        self.btnCerrar.clicked.connect(self.accept)
        botones.addWidget(self.btnCorreo)
        botones.addStretch(1)
        botones.addWidget(self.btnCerrar)
        layout.addLayout(botones)

    def _escribir(self) -> None:
        QDesktopServices.openUrl(QUrl(
            f"mailto:{CONTACTO}"
            "?subject=Plan%20Mensual%20-%20importaciones%20de%20listas"
        ))
