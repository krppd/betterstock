from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QBrush, QColor, QDesktopServices
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QStackedWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CheckBox,
    ComboBox,
    FluentIcon as FIF,
    LineEdit,
    MessageBox,
    PrimaryPushButton,
    PushButton,
    RadioButton,
    SimpleCardWidget,
    SubtitleLabel,
    TableWidget,
    qconfig,
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
from services.plan_motor import CONTACTO, limite, plan_actual
from ui.fluent import CLARO, OSCURO, color
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
ANCHO_CONTENIDO = 720
ANCHO_AVISO = 400


def _envuelto(etiqueta: BodyLabel, ancho: int = ANCHO_CONTENIDO) -> None:
    """Fija el alto mínimo de una etiqueta con texto envuelto.

    Qt no recalcula el alto de una etiqueta con ``word wrap`` cuando cambia el
    ancho disponible, así que el alto se calcula a mano para que no queden
    líneas cortadas.
    """
    etiqueta.setMinimumHeight(max(0, etiqueta.heightForWidth(ancho)))


def _tinta(nombre: str) -> tuple[QColor, QColor]:
    """Devuelve el par (claro, oscuro) de un token Fluent para labels adaptativos."""
    return QColor(CLARO[nombre]), QColor(OSCURO[nombre])


def _tarjeta(titulo: str, parent: QWidget) -> tuple[SimpleCardWidget, QVBoxLayout]:
    """Crea una tarjeta Fluent con su título y devuelve el layout para el contenido."""
    tarjeta = SimpleCardWidget(parent)
    tarjeta.setBorderRadius(8)
    disposicion = QVBoxLayout(tarjeta)
    disposicion.setContentsMargins(16, 14, 16, 14)
    disposicion.setSpacing(8)
    disposicion.addWidget(SubtitleLabel(titulo, tarjeta))
    return tarjeta, disposicion


class ImportadorProductos(QDialog):
    """Asistente para importar una lista de productos desde un archivo."""

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
        self._combos_columna: dict[str, ComboBox] = {}
        self._combos_seccion: list[ComboBox] = []
        self.setWindowTitle("Importar lista de productos")
        self.setObjectName("dlgImportador")
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

        self._aplicar_tema()
        qconfig.themeChanged.connect(self._aplicar_tema)

    def _aplicar_tema(self) -> None:
        """El fondo del asistente sigue al tema Fluent."""
        self.setStyleSheet(
            f"QDialog#{self.objectName()} {{ background-color: {color('fondo_suave')}; }}")

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
        self.lblResultado.setTextColor(*_tinta("alerta"))
        _envuelto(self.lblResultado)
        self.tblErrores.setRowCount(0)
        self.btnDeshacer.setEnabled(False)

    def _pagina_archivo(self) -> QWidget:
        pagina = QWidget(self)
        layout = QVBoxLayout(pagina)
        layout.setSpacing(10)

        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.txtArchivo = LineEdit(pagina)
        self.txtArchivo.setObjectName("txtArchivo")
        self.txtArchivo.setReadOnly(True)
        self.txtArchivo.setPlaceholderText("Elegí el archivo con la lista de productos")
        self.btnElegir = PushButton(FIF.FOLDER, "Elegir archivo…", pagina)
        self.btnElegir.setObjectName("btnElegir")
        self.btnElegir.clicked.connect(self.elegir_archivo)
        fila.addWidget(self.txtArchivo, 1)
        fila.addWidget(self.btnElegir)
        layout.addLayout(fila)

        self.lblResumen = BodyLabel("", pagina)
        self.lblResumen.setObjectName("lblResumen")
        self.lblResumen.setTextColor(*_tinta("texto_secundario"))
        self.lblResumen.setWordWrap(True)
        _envuelto(self.lblResumen)
        layout.addWidget(self.lblResumen)

        self.tblMuestra = TableWidget(pagina)
        self.tblMuestra.setObjectName("tblMuestra")
        self.tblMuestra.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblMuestra.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.tblMuestra, 1)
        layout.addLayout(self._fila_formato())
        return pagina

    def _fila_formato(self) -> QHBoxLayout:
        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.cmbFormato = ComboBox(self)
        self.cmbFormato.setObjectName("cmbFormato")
        self.cmbFormato.addItem(FORMATO_CSV, userData=None)
        for extra in self._servicio.importadores_disponibles():
            self.cmbFormato.addItem(extra["nombre"], userData=extra["clase"])
        self.cmbFormato.currentIndexChanged.connect(self._cambio_formato)
        fila.addWidget(BodyLabel("Formato del archivo:", self))
        fila.addWidget(self.cmbFormato, 1)
        return fila

    def _cambio_formato(self) -> None:
        self._servicio.usar_importador(self.cmbFormato.currentData())
        if self._deteccion is not None:
            self.cargar_archivo(self._deteccion.ruta)

    def _pagina_mapeo(self) -> QWidget:
        pagina = QWidget(self)
        layout = QVBoxLayout(pagina)
        layout.setSpacing(10)

        caja_secciones, secciones = _tarjeta("Secciones del archivo", pagina)
        self.tblSecciones = TableWidget(caja_secciones)
        self.tblSecciones.setObjectName("tblSecciones")
        self.tblSecciones.setColumnCount(3)
        self.tblSecciones.setHorizontalHeaderLabels(["Sección", "Filas", "Qué hacer"])
        self.tblSecciones.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblSecciones.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        secciones.addWidget(self.tblSecciones)
        layout.addWidget(caja_secciones, 1)

        caja_columnas, columnas = _tarjeta("Columnas del archivo", pagina)
        self.tblMapeo = TableWidget(caja_columnas)
        self.tblMapeo.setObjectName("tblMapeo")
        self.tblMapeo.setColumnCount(3)
        self.tblMapeo.setHorizontalHeaderLabels(["Campo", "Columna", "Ejemplos"])
        self.tblMapeo.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblMapeo.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        columnas.addWidget(self.tblMapeo)
        layout.addWidget(caja_columnas, 1)

        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.cmbTipoPrecio = ComboBox(pagina)
        self.cmbTipoPrecio.setObjectName("cmbTipoPrecio")
        self.cmbTipoPrecio.addItem("Venta", userData=PRECIO_VENTA)
        self.cmbTipoPrecio.addItem("Costo", userData=PRECIO_COSTO)
        self.cmbTipoPrecio.addItem(
            "Con IVA (se divide por 1,21)", userData=PRECIO_CON_IVA)
        self.cmbTipoPrecio.currentIndexChanged.connect(self._cambio_tipo_precio)
        fila.addWidget(BodyLabel("¿El precio del archivo es?", pagina))
        fila.addWidget(self.cmbTipoPrecio)
        fila.addStretch(1)
        layout.addLayout(fila)
        return pagina

    def _pagina_opciones(self) -> QWidget:
        pagina = QWidget(self)
        layout = QVBoxLayout(pagina)
        layout.setSpacing(10)

        caja, opciones = _tarjeta("Productos que ya existen", pagina)
        self.rbActualizarTodo = RadioButton(
            "Actualizar todo (nombre, categoría, unidad y precios)", caja)
        self.rbActualizarPrecios = RadioButton(
            "Actualizar solo los precios", caja)
        self.rbOmitir = RadioButton(
            "Omitir (dejarlos como están)", caja)
        self.rbActualizarTodo.setChecked(True)
        self._grupoExistentes = QButtonGroup(caja)
        self._grupoExistentes.addButton(self.rbActualizarTodo)
        self._grupoExistentes.addButton(self.rbActualizarPrecios)
        self._grupoExistentes.addButton(self.rbOmitir)
        opciones.addWidget(self.rbActualizarTodo)
        opciones.addWidget(self.rbActualizarPrecios)
        opciones.addWidget(self.rbOmitir)
        self.chkCrearNuevos = CheckBox(
            "Crear los productos que todavía no existen", caja)
        self.chkCrearNuevos.setChecked(True)
        opciones.addWidget(self.chkCrearNuevos)
        layout.addWidget(caja)

        caja_previa, previa = _tarjeta("Previsualización", pagina)
        self.tblPrevia = TableWidget(caja_previa)
        self.tblPrevia.setObjectName("tblPrevia")
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
        layout.setSpacing(10)

        self.lblResultado = BodyLabel("", pagina)
        self.lblResultado.setObjectName("lblResultado")
        self.lblResultado.setWordWrap(True)
        _envuelto(self.lblResultado)
        layout.addWidget(self.lblResultado)

        caja, contenido = _tarjeta("Errores de la importación", pagina)
        self.tblErrores = TableWidget(caja)
        self.tblErrores.setObjectName("tblErrores")
        self.tblErrores.setColumnCount(2)
        self.tblErrores.setHorizontalHeaderLabels(["Línea", "Motivo"])
        self.tblErrores.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tblErrores.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        contenido.addWidget(self.tblErrores)
        layout.addWidget(caja, 1)

        fila = QHBoxLayout()
        fila.setSpacing(8)
        self.btnDeshacer = PushButton(FIF.SKIP_BACK, "Deshacer esta importación", pagina)
        self.btnDeshacer.setObjectName("btnDeshacer")
        self.btnDeshacer.clicked.connect(self.deshacer)
        self.btnCerrar = PrimaryPushButton("Cerrar", pagina)
        self.btnCerrar.setObjectName("btnCerrar")
        self.btnCerrar.setDefault(True)
        self.btnCerrar.clicked.connect(self.accept)
        fila.addWidget(self.btnDeshacer)
        fila.addStretch(1)
        fila.addWidget(self.btnCerrar)
        layout.addLayout(fila)
        return pagina

    def _armar_botones(self) -> QHBoxLayout:
        botones = QHBoxLayout()
        botones.setSpacing(8)
        self.btnAtras = PushButton("Atrás", self)
        self.btnAtras.setObjectName("btnAtras")
        self.btnCancelar = PushButton("Cancelar", self)
        self.btnCancelar.setObjectName("btnCancelar")
        self.btnSiguiente = PrimaryPushButton("Siguiente", self)
        self.btnSiguiente.setObjectName("btnSiguiente")
        self.btnImportar = PrimaryPushButton("Importar", self)
        self.btnImportar.setObjectName("btnImportar")
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
            combo = ComboBox(self.tblSecciones)
            combo.setObjectName(f"cmbSeccion{indice}")
            for modo, etiqueta in MODOS_SECCION:
                combo.addItem(etiqueta, userData=modo)
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
            combo = ComboBox(self.tblMapeo)
            combo.setObjectName(f"cmbColumna_{campo}")
            combo.addItem(SIN_COLUMNAS, userData=-1)
            for columna in deteccion.columnas:
                combo.addItem(columna.nombre, userData=columna.indice)
            automatico = deteccion.mapeo.get(campo, -1)
            posicion = combo.findData(automatico)
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
            color_fila = self._color_de_fila(fila, actual)
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
                if color_fila:
                    item.setForeground(QBrush(QColor(color_fila)))
                self.tblPrevia.setItem(indice, columna, item)

    def _precio_texto(self, fila, campo: str) -> str:
        if campo not in fila.precios:
            return ""
        return formatear_dinero(fila.precios[campo])

    def _color_de_fila(self, fila, actual) -> str | None:
        if fila.errores:
            return color("error")
        if fila.avisos:
            return color("alerta")
        for campo in ("precio_venta", "precio_costo"):
            nuevo = fila.precios.get(campo)
            if nuevo is None:
                continue
            if nuevo <= 0:
                return color("alerta")
            if actual is None:
                continue
            viejo = float(getattr(actual, campo, 0.0) or 0.0)
            if viejo > 0 and (nuevo < viejo / 2 or nuevo > viejo * 2):
                return color("alerta")
        return None

    def _llenar_resultado(self, resultado: ResultadoImportacion) -> None:
        self.lblResultado.setTextColor(*_tinta("texto"))
        self.lblResultado.setText(
            f"Importación terminada.\n"
            f"Creados: {resultado.creados} · "
            f"Actualizados: {resultado.actualizados} · "
            f"Omitidos: {resultado.omitidos} · "
            f"Errores: {len(resultado.errores)}"
        )
        _envuelto(self.lblResultado)
        self.tblErrores.setRowCount(len(resultado.errores))
        for indice, (numero, motivo) in enumerate(resultado.errores):
            self.tblErrores.setItem(indice, 0, QTableWidgetItem(str(numero)))
            self.tblErrores.setItem(indice, 1, QTableWidgetItem(motivo))
        self.btnDeshacer.setEnabled(resultado.creados + resultado.actualizados > 0)

    def _caja_mensaje(self, titulo: str, mensaje: str) -> MessageBox:
        """Crea una caja de mensaje Fluent, centrada sobre el asistente."""
        caja = MessageBox(titulo, mensaje, self)
        centro = self.mapToGlobal(self.rect().center())
        caja.move(centro.x() - caja.width() // 2, centro.y() - caja.height() // 2)
        return caja

    def _avisar(self, titulo: str, mensaje: str) -> None:
        caja = self._caja_mensaje(titulo, mensaje)
        caja.yesButton.setText("Entendido")
        caja.hideCancelButton()
        caja.exec()

    def _confirmar(self, titulo: str, pregunta: str) -> bool:
        caja = self._caja_mensaje(titulo, pregunta)
        caja.yesButton.setText("Sí")
        caja.cancelButton.setText("No")
        return bool(caja.exec())


class AvisoPlanGratis(QDialog):
    """Avisa que el plan Gratis ya consumió las importaciones permitidas."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Plan Gratis")
        self.setObjectName("dlgAvisoPlanGratis")
        self.setMinimumWidth(460)

        maximo = limite("importaciones")
        titulo = plan_actual().get("titulo", "Gratis")
        permisos = f"{maximo} importación" if maximo is not None else "importaciones sin límite"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(SubtitleLabel("Llegaste al límite del plan Gratis", self))

        texto = BodyLabel(
            f"El plan {titulo} permite {permisos} de "
            "listas de productos, y ya la usaste.\n\n"
            "Las importaciones ilimitadas, con historial y deshacer, son del plan "
            "Mensual.\n\n"
            "Escribinos y lo activamos en el momento.",
            self,
        )
        texto.setWordWrap(True)
        _envuelto(texto, ANCHO_AVISO)
        layout.addWidget(texto)

        botones = QHBoxLayout()
        botones.setSpacing(8)
        self.btnCorreo = PushButton(f"Escribir a {CONTACTO}", self)
        self.btnCorreo.setObjectName("btnCorreo")
        self.btnCerrar = PrimaryPushButton("Entendido", self)
        self.btnCerrar.setObjectName("btnCerrar")
        self.btnCerrar.setDefault(True)
        self.btnCorreo.clicked.connect(self._escribir)
        self.btnCerrar.clicked.connect(self.accept)
        botones.addWidget(self.btnCorreo)
        botones.addStretch(1)
        botones.addWidget(self.btnCerrar)
        layout.addLayout(botones)

        self._aplicar_tema()
        qconfig.themeChanged.connect(self._aplicar_tema)

    def _aplicar_tema(self) -> None:
        """El fondo del diálogo sigue al tema Fluent."""
        self.setStyleSheet(
            f"QDialog#{self.objectName()} {{ background-color: {color('fondo_suave')}; }}")

    def _escribir(self) -> None:
        QDesktopServices.openUrl(QUrl(
            f"mailto:{CONTACTO}"
            "?subject=Plan%20Mensual%20-%20importaciones%20de%20listas"
        ))
