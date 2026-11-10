from __future__ import annotations

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from config import RECURSOS_DIR
from ui.estilos import TAMANO_BODY, TAMANO_MICRO, TAMANO_SUBTITLE, escala, fuente
from ui.tema import BLANCO, COLORES

ANCHO_EXPANDIDO = 220
ANCHO_COLAPSADO = 74
ANCHO_ITEM_COLAPSADO = 48
ALTO_ITEM = 40
LADO_ICONO = 20
LADO_LOGO = 30
LADO_MENU = 24

_CACHE_ICONOS: dict[tuple[str, str], QIcon] = {}


def _px(valor: int) -> int:
    return round(valor * escala())


def _ruta_icono(nombre: str) -> str:
    return str(RECURSOS_DIR / "iconos" / nombre)


def _icono(nombre: str, color: str) -> QIcon:
    clave = (nombre, color)
    if clave in _CACHE_ICONOS:
        return _CACHE_ICONOS[clave]
    original = QPixmap(_ruta_icono(nombre))
    if original.isNull():
        return QIcon()
    pintado = QPixmap(original.size())
    pintado.fill(Qt.GlobalColor.transparent)
    pincel = QPainter(pintado)
    pincel.drawPixmap(0, 0, original)
    pincel.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    pincel.fillRect(pintado.rect(), QColor(COLORES[color]))
    pincel.end()
    icono = QIcon(pintado)
    _CACHE_ICONOS[clave] = icono
    return icono


class ItemSidebar(QPushButton):
    def __init__(self, clave: str, texto: str, icono: str, parent=None) -> None:
        super().__init__(texto, parent)
        self.clave = clave
        self._texto = texto
        self._icono = icono
        self._activo = False
        self._colapsado = False
        self.setObjectName("itemSidebar")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.setAutoDefault(False)
        self.setMinimumHeight(_px(ALTO_ITEM))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setIconSize(QSize(_px(LADO_ICONO), _px(LADO_ICONO)))
        self.setFont(fuente(TAMANO_BODY))
        self._pintar_icono()

    def _pintar_icono(self) -> None:
        color = "sidebar_activo_texto" if self._activo else "blanco"
        self.setIcon(_icono(self._icono, color))

    def marcar(self, activo: bool) -> None:
        self._activo = activo
        self.setProperty("activo", activo)
        self._pintar_icono()
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def set_colapsado(self, colapsado: bool) -> None:
        self._colapsado = colapsado
        if colapsado:
            self.setText("")
            self.setToolTip(self._texto)
            self.setMinimumWidth(_px(ANCHO_ITEM_COLAPSADO))
        else:
            self.setText(self._texto)
            self.setToolTip("")
            self.setMinimumWidth(0)


class GrupoSidebar(QWidget):
    def __init__(self, titulo: str, parent=None) -> None:
        super().__init__(parent)
        self._abierto = True
        self.items: list[ItemSidebar] = []
        self.setObjectName("grupoSidebar")
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(_px(2))

        cabecera = QWidget(self)
        fila = QHBoxLayout(cabecera)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(_px(4))
        self.etiqueta = QLabel(titulo, cabecera)
        self.etiqueta.setObjectName("grupoSidebar")
        self.etiqueta.setFont(fuente(TAMANO_MICRO, negrita=True))
        self.flecha = QPushButton("⌄", cabecera)
        self.flecha.setObjectName("flechaGrupo")
        self.flecha.setCursor(Qt.CursorShape.PointingHandCursor)
        self.flecha.setFlat(True)
        self.flecha.setFixedSize(_px(20), _px(20))
        self.flecha.setFont(fuente(TAMANO_MICRO, negrita=True))
        self.flecha.clicked.connect(self.alternar)
        fila.addWidget(self.etiqueta)
        fila.addStretch(1)
        fila.addWidget(self.flecha)

        self.cuerpo = QWidget(self)
        self.cuerpo.setObjectName("cuerpoGrupoSidebar")
        self.cuerpo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self._cuerpo_layout = QVBoxLayout(self.cuerpo)
        self._cuerpo_layout.setContentsMargins(0, 0, 0, 0)
        self._cuerpo_layout.setSpacing(_px(2))

        raiz.addWidget(cabecera)
        raiz.addWidget(self.cuerpo)

    def agregar(self, item: ItemSidebar) -> None:
        self.items.append(item)
        self._cuerpo_layout.addWidget(item)

    def alternar(self) -> None:
        self.set_abierto(not self._abierto)

    def set_abierto(self, abierto: bool) -> None:
        self._abierto = abierto
        self.cuerpo.setVisible(abierto)
        self.flecha.setText("⌄" if abierto else "›")

    def set_colapsado(self, colapsado: bool) -> None:
        self.etiqueta.setVisible(not colapsado)
        self.flecha.setVisible(not colapsado)
        self.cuerpo.setVisible(True if colapsado else self._abierto)


class Sidebar(QFrame):
    navegar = pyqtSignal(str)
    ajustes_click = pyqtSignal()
    usuario_click = pyqtSignal()
    menu_click = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("frameSidebar")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self._colapsado = False
        self._usuario_texto = ""
        self._usuario_tooltip = ""
        self._items: dict[str, ItemSidebar] = {}
        self._grupos: list[GrupoSidebar] = []
        self._construir()
        self.set_colapsado(False)
        self.style().unpolish(self)
        self.style().polish(self)

    def _construir(self) -> None:
        self._raiz = QVBoxLayout(self)
        self._raiz.setContentsMargins(_px(12), _px(14), _px(12), _px(12))
        self._raiz.setSpacing(_px(6))

        cabecera = QWidget(self)
        fila = QHBoxLayout(cabecera)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(_px(8))

        self.logo = QLabel(cabecera)
        self.logo.setObjectName("logoBadge")
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo.setFixedSize(_px(LADO_LOGO), _px(LADO_LOGO))
        self.logo.setStyleSheet(
            f"QLabel#logoBadge {{ background-color: {BLANCO}; border-radius: 8px; }}")
        self._poner_logo()

        textos = QWidget(cabecera)
        columna = QVBoxLayout(textos)
        columna.setContentsMargins(0, 0, 0, 0)
        columna.setSpacing(0)
        self.marca = QLabel("BetterStock", textos)
        self.marca.setObjectName("marcaSidebar")
        self.marca.setFont(fuente(TAMANO_SUBTITLE, negrita=True))
        self.submarca = QLabel("Control de stock", textos)
        self.submarca.setObjectName("subMarcaSidebar")
        self.submarca.setFont(fuente(TAMANO_MICRO))
        columna.addWidget(self.marca)
        columna.addWidget(self.submarca)

        self.btnMenu = QPushButton("«", cabecera)
        self.btnMenu.setObjectName("btnMenu")
        self.btnMenu.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnMenu.setFlat(True)
        self.btnMenu.setFixedSize(_px(LADO_MENU), _px(LADO_MENU))
        self.btnMenu.setFont(fuente(TAMANO_BODY, negrita=True))
        self.btnMenu.clicked.connect(self.menu_click.emit)
        self.btnMenu.setVisible(escala() > 1.0)

        fila.addWidget(self.logo)
        fila.addWidget(textos, 1)
        fila.addWidget(self.btnMenu)
        self._cabecera = cabecera
        self._raiz.addWidget(cabecera)

        self.scroll = QScrollArea(self)
        self.scroll.setObjectName("scrollSidebar")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        contenido = QWidget()
        contenido.setObjectName("contenidoSidebar")
        self._navegacion = QVBoxLayout(contenido)
        self._navegacion.setContentsMargins(0, 0, 0, 0)
        self._navegacion.setSpacing(_px(2))
        self.scroll.setWidget(contenido)
        self._raiz.addWidget(self.scroll, 1)

        self.lblSeccionStock = self._grupo("STOCK", (
            ("productos", "Productos (F1)", "productos.png"),
            ("movimientos", "Movimientos (F2)", "movimientos.png"),
            ("alertas", "Alertas (F4)", "alertas.png"),
        ))
        self.lblSeccionCaja = self._grupo("CAJA", (
            ("ventas", "Ventas (F5)", "ventas.png"),
            ("cierre", "Caja (F6)", "cierre.png"),
            ("consulta", "Consulta precio (F7)", "consulta.png"),
        ))
        self.lblSeccionAnalisis = self._grupo("ANÁLISIS", (
            ("estadisticas", "Estadísticas (F8)", "estadisticas.png"),
        ))
        self._navegacion.addStretch(1)

        self.btnReportes = ItemSidebar("reportes", "Premium", "estadisticas.png", self)
        self.btnReportes.hide()
        self._raiz.addWidget(self.btnReportes)

        self.btnAjustes = ItemSidebar("ajustes", "Ajustes", "ajustes.png", self)
        self.btnAjustes.clicked.connect(self.ajustes_click.emit)
        self._raiz.addWidget(self.btnAjustes)

        self.btnUsuario = QPushButton(self)
        self.btnUsuario.setObjectName("usuarioSidebar")
        self.btnUsuario.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnUsuario.setFlat(True)
        self.btnUsuario.setMinimumHeight(_px(48))
        self.btnUsuario.setIcon(_icono("user.png", "blanco"))
        self.btnUsuario.setIconSize(QSize(_px(26), _px(26)))
        self.btnUsuario.setFont(fuente(TAMANO_BODY))
        self.btnUsuario.clicked.connect(self.usuario_click.emit)
        self._raiz.addWidget(self.btnUsuario)

        self._items["ajustes"] = self.btnAjustes
        for clave, item in self._items.items():
            item.clicked.connect(lambda _=False, c=clave: self.navegar.emit(c))

    def _grupo(self, titulo: str, definicion) -> QLabel:
        grupo = GrupoSidebar(titulo, self.scroll.widget())
        for clave, texto, icono in definicion:
            item = ItemSidebar(clave, texto, icono, grupo)
            grupo.agregar(item)
            self._items[clave] = item
            setattr(self, f"btn{clave.capitalize()}", item)
        self._grupos.append(grupo)
        self._navegacion.addWidget(grupo)
        return grupo.etiqueta

    def showEvent(self, evento) -> None:
        super().showEvent(evento)
        self.style().unpolish(self)
        self.style().polish(self)

    def _poner_logo(self) -> None:
        ruta = RECURSOS_DIR / "logo_sf.png"
        logo = QPixmap(str(ruta))
        if logo.isNull():
            return
        lado = _px(22)
        self.logo.setPixmap(logo.scaled(
            lado, lado,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))

    def set_usuario(self, texto: str, tooltip: str = "") -> None:
        self._usuario_texto = texto
        self._usuario_tooltip = tooltip
        if not texto:
            self.btnUsuario.hide()
            return
        self.btnUsuario.show()
        if self._colapsado:
            self.btnUsuario.setText("")
            self.btnUsuario.setToolTip(tooltip)
        else:
            self.btnUsuario.setText(texto)
            self.btnUsuario.setToolTip("")

    def marcar_activa(self, clave: str) -> None:
        for nombre, item in self._items.items():
            item.marcar(nombre == clave)
        if clave:
            for grupo in self._grupos:
                if any(item.clave == clave for item in grupo.items):
                    grupo.set_abierto(True)

    def set_colapsado(self, colapsado: bool) -> None:
        self._colapsado = colapsado
        ancho = ANCHO_COLAPSADO if colapsado else ANCHO_EXPANDIDO
        self.setMinimumWidth(_px(ancho))
        self.setMaximumWidth(_px(ancho))
        margen = 8 if colapsado else 12
        self._raiz.setContentsMargins(_px(margen), _px(14), _px(margen), _px(12))
        self.marca.setVisible(not colapsado)
        self.submarca.setVisible(not colapsado)
        for grupo in self._grupos:
            grupo.set_colapsado(colapsado)
        for item in self._items.values():
            item.set_colapsado(colapsado)
        self.btnReportes.set_colapsado(colapsado)
        self.btnMenu.setText("»" if colapsado else "«")
        if self._usuario_texto:
            self.set_usuario(self._usuario_texto, self._usuario_tooltip)
