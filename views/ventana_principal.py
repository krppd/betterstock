from __future__ import annotations

from typing import Callable

from PyQt6 import QtCore
from PyQt6.QtCore import (
    QEvent,
    QObject,
    QPropertyAnimation,
    QSize,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QCloseEvent,
    QKeySequence,
    QPixmap,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from config import ALERTAS_EN_AVISO_STOCK, RECURSOS_DIR
from models.producto import Producto
from models.usuario import Usuario
from services.autenticacion import Autenticacion
from services.cierre_caja import ServicioCierre
from services.estadisticas_ventas import EstadisticasVentas
from services.gestor_anulaciones import GestorAnulaciones
from services.gestor_comercio import GestorComercio
from services.gestor_fiado import GestorFiado
from services.gestor_stock import GestorStock
from services.gestor_ventas import GestorVentas
from services.turnos import ServicioTurnos
from ui.estilo_ventana import aplicar_estilo_ventana
from ui.estilos import (
    ESCALA_NORMAL,
    TAMANO_BODY,
    TAMANO_MICRO,
    TAMANO_SMALL,
    escala,
    fuente,
)
from ui.generated.main_ui import Ui_MainWindow
from ui.tema import color
from ui.widgets.notificacion import Notificacion
from ui.widgets.sidebar import (
    ANCHO_COLAPSADO,
    ANCHO_EXPANDIDO,
    ANCHO_ITEM_COLAPSADO,
)
from utils.formato import formatear_cantidad
from views.componentes_sidebar import BotonSidebar, _icono_tintado, _px
from views.ventana_alertas import VentanaAlertas
from views.ventana_base import VentanaBase
from views.ventana_caja import VentanaCaja, VentanaCierre
from views.ventana_clientes import VentanaClientes
from views.ventana_configuracion import VentanaConfiguracion
from views.ventana_consulta import VentanaConsulta
from views.ventana_dashboard import DashboardPrincipalWidget
from views.ventana_estadisticas import VentanaEstadisticas
from views.ventana_movimientos import VentanaMovimientos
from views.ventana_productos import VentanaProductos
from views.ventana_reportes import VentanaReportes
from views.ventana_ventas import VentanaVentas

def _px(valor: int) -> int:
    return round(valor * escala())


class VentanaPrincipal(QMainWindow, VentanaBase):

    MAXIMO_ALERTAS_EN_MENSAJE = ALERTAS_EN_AVISO_STOCK
    LADO_ICONO = 24
    ANCHO_BARRA_COLAPSADA = ANCHO_COLAPSADO
    ANCHO_BOTON_COLAPSADO = ANCHO_ITEM_COLAPSADO
    LADO_BOTON_MENU = 24

    sesion_cerrada = pyqtSignal()

    def __init__(
        self,
        gestor_stock: GestorStock,
        gestor_comercio: GestorComercio,
        estadisticas: EstadisticasVentas,
        cierre: ServicioCierre | None = None,
        usuario_actual: str = "",
        fiado: GestorFiado | None = None,
        gestor_ventas: GestorVentas | None = None,
        anulaciones: GestorAnulaciones | None = None,
        permiso: str = "",
        autenticacion: Autenticacion | None = None,
        turnos: ServicioTurnos | None = None,
        caja=None,
    ) -> None:
        super().__init__()
        self._gestor_stock = gestor_stock
        self._gestor_comercio = gestor_comercio
        self._estadisticas = estadisticas
        self._cierre = cierre
        self._caja = caja
        self._usuario_actual = usuario_actual
        self._permiso = permiso
        self._cierre_controlado = False
        self._barra_colapsada = False
        self._fiado = fiado
        self._gestor_ventas = gestor_ventas if gestor_ventas is not None else \
            GestorVentas(gestor_stock, estadisticas, fiado, cierre)
        self._anulaciones = anulaciones
        self._autenticacion = autenticacion
        self._turnos = turnos
        self._caja = caja
        self._paginas: QStackedWidget | None = None
        self._inicio: QLabel | None = None
        self._aviso_stock: Notificacion | None = None
        self._indices: dict[str, int] = {}
        self._pixmap_logo = self._cargar_logo()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setStyleSheet(
            f"QMainWindow#MainWindow {{ background-color: {color('blanco')}; border: none; }} "
            f"QWidget#centralwidget {{ background-color: {color('blanco')}; border: none; }}"
        )

        self._acomodar_widgets()
        self.setMinimumSize(round(940 * escala()), 620)
        self._preparar_animacion()
        self._preparar_barra_estado()
        self._conectar_botones()
        self._conectar_atajos()

        QtCore.QTimer.singleShot(500, self.verificar_alertas)

    @staticmethod
    def _cargar_logo() -> QPixmap:
        logo = QPixmap(str(RECURSOS_DIR / "logo_sf.png"))
        if logo.isNull():
            logo = QPixmap(":/Imagenes/logo_sf.png")
        return logo

    def _preparar_barra_estado(self) -> None:
        self._reloj = QLabel()
        self._reloj.setFont(fuente(TAMANO_SMALL, tabular=True))
        self.statusBar().addPermanentWidget(self._reloj)
        self._actualizar_reloj()
        temporizador = QtCore.QTimer(self)
        temporizador.setInterval(1000)
        temporizador.timeout.connect(self._actualizar_reloj)
        temporizador.start()

    def _actualizar_reloj(self) -> None:
        self._reloj.setText(QtCore.QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm"))

    def _preparar_animacion(self) -> None:
        self._animacion = QPropertyAnimation(self, b"windowOpacity")
        self._animacion.setDuration(200)
        self._animacion.setStartValue(0.0)
        self._animacion.setEndValue(1.0)
        self._animada = False

    def _acomodar_widgets(self) -> None:
        self.ui.widget.setVisible(False)
        self.ui.label.setVisible(False)

        self._dashboard = DashboardPrincipalWidget(
            gestor_stock=self._gestor_stock,
            estadisticas=self._estadisticas,
            fiado=self._fiado,
            usuario=self._usuario_actual or "Admin",
            parent=self,
        )

        self._paginas = QStackedWidget()
        pagina_inicio = QWidget()
        layout_inicio = QVBoxLayout(pagina_inicio)
        layout_inicio.setContentsMargins(0, 0, 0, 0)
        layout_inicio.addWidget(self._dashboard)

        self._inicio = QLabel(pagina_inicio)
        self._inicio.setVisible(False)
        self._inicio.installEventFilter(self)

        self._indices["inicio"] = self._paginas.addWidget(pagina_inicio)

        layout = self.ui.horizontalLayout
        while layout.count():
            layout.takeAt(0)

        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self._construir_sidebar_moderno()

        self._aplicar_posicion_sidebar()

    def _aplicar_posicion_sidebar(self, posicion: str | None = None) -> None:
        if posicion is None:
            try:
                from services.preferencias import posicion_menu
                posicion = posicion_menu()
            except Exception:
                posicion = "izquierda"

        self._posicion_sidebar = posicion
        layout = self.ui.horizontalLayout
        layout.removeWidget(self.ui.frameSidebar)
        layout.removeWidget(self._paginas)

        if posicion == "derecha":
            layout.addWidget(self._paginas, 1)
            layout.addWidget(self.ui.frameSidebar)
        else:
            layout.addWidget(self.ui.frameSidebar)
            layout.addWidget(self._paginas, 1)

        self._vestir_boton_menu()

    def _construir_sidebar_moderno(self) -> None:
        """Construye el frameSidebar con estética nativa, degradé verde BetterStock y bordes."""
        frame = self.ui.frameSidebar
        frame.setObjectName("frameSidebar")
        frame.setStyleSheet(
            "QFrame#frameSidebar { "
            f"background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 {color('verde_lateral_inicio')}, stop:1 {color('verde_lateral_fin')}); "
            "border: 1px solid rgba(0, 0, 0, 0.08); "
            "border-radius: 14px; "
            "}"
        )
        self._ancho_pilar = ANCHO_EXPANDIDO
        frame.setMinimumWidth(round(self._ancho_pilar * escala()))
        frame.setMaximumWidth(round(self._ancho_pilar * escala()))

        layout_viejo = frame.layout()
        if layout_viejo is not None:
            QWidget().setLayout(layout_viejo)

        layout_raiz = QVBoxLayout(frame)
        layout_raiz.setContentsMargins(_px(10), _px(12), _px(10), _px(12))
        layout_raiz.setSpacing(_px(6))

        nombre_tienda = "BetterStock"
        if self._gestor_comercio:
            try:
                if self._gestor_comercio.comercio and isinstance(self._gestor_comercio.comercio.nombre, str):
                    nombre_tienda = self._gestor_comercio.comercio.nombre
                elif hasattr(self._gestor_comercio, "obtener_nombre_comercio"):
                    n = self._gestor_comercio.obtener_nombre_comercio()
                    if n and isinstance(n, str):
                        nombre_tienda = n
            except Exception:
                pass
        nombre_tienda = str(nombre_tienda)

        etiqueta_rol = Usuario.ETIQUETAS_PERMISO.get(self._permiso, "Profesional") if self._permiso else "Profesional"

        self._card_tienda = QFrame(frame)
        self._card_tienda.setObjectName("btnSwitcherTienda")
        self._card_tienda.setCursor(Qt.CursorShape.PointingHandCursor)
        self._card_tienda.setFixedHeight(_px(46))
        self._card_tienda.setStyleSheet(
            "QFrame#btnSwitcherTienda { "
            f"background-color: {color('sidebar_btn_inactivo_fondo')}; "
            f"border: 1px solid {color('sidebar_btn_inactivo_borde')}; "
            f"border-radius: {_px(10)}px; "
            "} "
            "QFrame#btnSwitcherTienda:hover { "
            f"background-color: {color('sidebar_btn_hover_fondo')}; "
            f"border-color: {color('sidebar_btn_hover_borde')}; "
            "}"
        )
        lay_tienda = QHBoxLayout(self._card_tienda)
        lay_tienda.setContentsMargins(_px(12), _px(2), _px(12), _px(6))
        lay_tienda.setSpacing(_px(10))
        lay_tienda.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        ico_box = QLabel(self._card_tienda)
        ico_box.setFixedSize(_px(20), _px(20))
        ico_box.setStyleSheet("background: transparent; border: none;")
        ico_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico_box.setPixmap(_icono_tintado("tienda.png", color("blanco"), 20).pixmap(_px(20), _px(20)))
        lay_tienda.addWidget(ico_box, 0, Qt.AlignmentFlag.AlignVCenter)

        col_t = QVBoxLayout()
        col_t.setContentsMargins(0, 0, 0, _px(2))
        col_t.setSpacing(_px(1))
        col_t.addStretch(1)
        lbl_t_nom = QLabel(nombre_tienda, self._card_tienda)
        lbl_t_nom.setStyleSheet(f"color: {color('blanco')}; font-weight: 700; font-size: {_px(13)}px; background: transparent; border: none;")
        lbl_t_nom.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        lbl_t_rol = QLabel(etiqueta_rol, self._card_tienda)
        lbl_t_rol.setStyleSheet(f"color: rgba(255, 255, 255, 0.65); font-size: {_px(11)}px; background: transparent; border: none;")
        lbl_t_rol.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        col_t.addWidget(lbl_t_nom)
        col_t.addWidget(lbl_t_rol)
        col_t.addStretch(1)
        lay_tienda.addLayout(col_t, 0)
        lay_tienda.addStretch(1)

        self._card_tienda.mousePressEvent = lambda _: self.mostrar_inicio()
        layout_raiz.addWidget(self._card_tienda)

        self._btn_menu = QPushButton("«", frame)
        self._btn_menu.setObjectName("btnMenu")
        self._btn_menu.setFixedSize(_px(self.LADO_BOTON_MENU), _px(self.LADO_BOTON_MENU))
        self._btn_menu.setFont(fuente(TAMANO_BODY, negrita=True))
        self._btn_menu.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; color: {color('blanco')}; }} "
            "QPushButton:hover { background: rgba(255, 255, 255, 0.18); border-radius: 6px; } "
            "QPushButton:pressed { background: rgba(255, 255, 255, 0.30); border-radius: 6px; }"
        )
        self._btn_menu.setVisible(escala() > ESCALA_NORMAL)
        self._btn_menu.clicked.connect(self._alternar_barra)
        layout_raiz.addWidget(self._btn_menu, 0, Qt.AlignmentFlag.AlignRight)

        scroll_nav = QScrollArea(frame)
        scroll_nav.setWidgetResizable(True)
        scroll_nav.setFrameShape(QFrame.Shape.NoFrame)
        scroll_nav.setStyleSheet(
            "QScrollArea { background: transparent; border: none; } "
            "QScrollBar:vertical { width: 4px; background: transparent; } "
            "QScrollBar::handle:vertical { background: rgba(255, 255, 255, 0.2); border-radius: 2px; } "
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
        )

        contenedor_nav = QWidget()
        contenedor_nav.setStyleSheet("background: transparent;")
        lay_nav = QVBoxLayout(contenedor_nav)
        lay_nav.setContentsMargins(0, 4, 0, 4)
        lay_nav.setSpacing(_px(6))

        self.ui.btnProductos = BotonSidebar("productos", "Productos (F1)", "productos.png", contenedor_nav)
        self.ui.btnMovimientos = BotonSidebar("movimientos", "Movimientos (F2)", "movimientos.png", contenedor_nav)
        self.ui.btnAlertas = BotonSidebar("alertas", "Alertas (F4)", "alertas.png", contenedor_nav)
        self.ui.btnReportes = BotonSidebar("reportes", "Reportes", "estadisticas.png", contenedor_nav)

        self.ui.btnEstadisticas = BotonSidebar("estadisticas", "Estadísticas (F8)", "estadisticas.png", contenedor_nav)

        self.ui.btnVentas = BotonSidebar("ventas", "Ventas (F5)", "ventas.png", contenedor_nav)
        self.ui.btnCierre = BotonSidebar("cierre", "Caja (F6)", "cierre.png", contenedor_nav)
        self.ui.btnConsulta = BotonSidebar("consulta", "Consulta precio (F7)", "consulta.png", contenedor_nav)
        self.ui.btnAjustes = BotonSidebar("ajustes", "Ajustes", "ajustes.png", contenedor_nav)

        self.ui.lblSeccionStock = QLabel("STOCK", contenedor_nav)
        self.ui.lblSeccionCaja = QLabel("VENTAS Y CAJA", contenedor_nav)
        self.ui.lblSeccionAnalisis = QLabel("REPORTES", contenedor_nav)

        for lbl in (self.ui.lblSeccionStock, self.ui.lblSeccionCaja, self.ui.lblSeccionAnalisis):
            lbl.setFont(fuente(TAMANO_MICRO, negrita=True))
            lbl.setStyleSheet(
                "color: rgba(255, 255, 255, 0.65); "
                f"font-size: {_px(10)}px; "
                "font-weight: 700; "
                "letter-spacing: 0.8px; "
                "background: transparent; "
                "border: none; "
                f"padding: {_px(10)}px {_px(4)}px {_px(2)}px {_px(4)}px;"
            )

        lay_nav.addWidget(self.ui.lblSeccionStock)
        lay_nav.addWidget(self.ui.btnProductos)
        lay_nav.addWidget(self.ui.btnMovimientos)
        lay_nav.addWidget(self.ui.btnAlertas)

        lay_nav.addWidget(self.ui.lblSeccionCaja)
        lay_nav.addWidget(self.ui.btnVentas)
        lay_nav.addWidget(self.ui.btnCierre)
        lay_nav.addWidget(self.ui.btnConsulta)

        lay_nav.addWidget(self.ui.lblSeccionAnalisis)
        lay_nav.addWidget(self.ui.btnEstadisticas)

        lay_nav.addStretch(1)
        scroll_nav.setWidget(contenedor_nav)
        layout_raiz.addWidget(scroll_nav, 1)

        self._divisor = QFrame(frame)
        self._divisor.setFixedHeight(1)
        self._divisor.setStyleSheet("background-color: rgba(255, 255, 255, 0.15); margin: 2px 0px;")
        layout_raiz.addWidget(self._divisor)

        self.ui.btnUsuario = QPushButton(frame)
        self.ui.btnUsuario.setObjectName("btnUsuario")
        self.ui.btnUsuario.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ui.btnUsuario.setMinimumHeight(_px(46))
        layout_raiz.addWidget(self.ui.btnUsuario)

        layout_raiz.addWidget(self.ui.btnAjustes)

        self._titulos_sidebar = {
            "btnProductos": "Productos (F1)",
            "btnMovimientos": "Movimientos (F2)",
            "btnAlertas": "Alertas (F4)",
            "btnEstadisticas": "Estadísticas (F8)",
            "btnVentas": "Ventas (F5)",
            "btnCierre": "Caja (F6)",
            "btnConsulta": "Consulta precio (F7)",
            "btnAjustes": "Ajustes",
        }

    def _conectar_botones(self) -> None:
        self.ui.btnProductos.setText("Productos (F1)")
        self.ui.btnMovimientos.setText("Movimientos (F2)")
        self.ui.btnAlertas.setText("Alertas (F4)")
        self.ui.btnEstadisticas.setText("Estadísticas (F8)")
        self.ui.btnVentas.setText("Ventas (F5)")
        self.ui.btnCierre.setText("Caja (F6)")
        self.ui.btnConsulta.setText("Consulta precio (F7)")
        self.ui.btnAlertas.setVisible(True)
        self.ui.btnReportes.setVisible(False)

        self._armar_boton_usuario()

        self.ui.btnAlertas.clicked.connect(self.abrir_alertas)
        self.ui.btnProductos.clicked.connect(self.abrir_productos)
        self.ui.btnMovimientos.clicked.connect(self.abrir_movimientos)
        self.ui.btnReportes.clicked.connect(self.abrir_reportes)
        self.ui.btnEstadisticas.clicked.connect(self.abrir_estadisticas)
        self.ui.btnVentas.clicked.connect(self.abrir_ventas)
        self.ui.btnCierre.clicked.connect(self.abrir_cierre)
        self.ui.btnConsulta.clicked.connect(self.abrir_consulta)
        self.ui.btnUsuario.clicked.connect(self._al_hacer_click_usuario)
        self.ui.btnAjustes.clicked.connect(self.abrir_ajustes)

        self._marcar_activa("")

    def _conectar_atajos(self) -> None:
        atajos = (
            (Qt.Key.Key_F1, self.abrir_productos),
            (Qt.Key.Key_F2, self.abrir_movimientos),
            (Qt.Key.Key_F4, self.abrir_alertas),
            (Qt.Key.Key_F8, self.abrir_estadisticas),
            (Qt.Key.Key_F5, self.abrir_ventas),
            (Qt.Key.Key_F6, self.abrir_cierre),
            (Qt.Key.Key_F7, self.abrir_consulta),
            (Qt.Key.Key_Escape, self.mostrar_inicio),
        )
        for tecla, destino in atajos:
            QShortcut(QKeySequence(tecla), self).activated.connect(destino)

    def _armar_boton_usuario(self) -> None:
        if not self._usuario_actual:
            self.ui.btnUsuario.hide()
            return
        self.ui.btnUsuario.show()
        etiqueta = Usuario.ETIQUETAS_PERMISO.get(self._permiso, self._permiso)
        aire = " "
        nombre = f"{aire}{self._usuario_actual}"
        texto = f"{nombre}\n{aire}{etiqueta}" if etiqueta else nombre
        self.ui.btnUsuario.setText(texto)

        pad_u = 0 if self._barra_colapsada else _px(12)
        self.ui.btnUsuario.setFixedHeight(_px(46))
        self.ui.btnUsuario.setStyleSheet(
            "QPushButton { "
            f"background-color: {color('sidebar_btn_inactivo_fondo')}; "
            f"border: 1px solid {color('sidebar_btn_inactivo_borde')}; "
            f"border-radius: {_px(10)}px; "
            f"color: {color('sidebar_btn_inactivo_texto')}; "
            f"font-size: {_px(12)}px; "
            "font-weight: 600; "
            f"text-align: {'center' if self._barra_colapsada else 'left'}; "
            f"padding: {_px(4)}px {pad_u}px; "
            "} "
            "QPushButton:hover { "
            f"background-color: {color('sidebar_btn_hover_fondo')}; "
            f"border-color: {color('sidebar_btn_hover_borde')}; "
            "}"
        )
        self.ui.btnUsuario.setIcon(_icono_tintado("user.png", color("sidebar_btn_inactivo_texto"), 20))
        self.ui.btnUsuario.setIconSize(QSize(_px(20), _px(20)))

    def _alternar_barra(self) -> None:
        self._barra_colapsada = not self._barra_colapsada
        self._vestir_barra()

    def _vestir_boton_menu(self) -> None:
        self._btn_menu.setVisible(escala() > ESCALA_NORMAL)
        pos = getattr(self, "_posicion_sidebar", "izquierda")
        if pos == "derecha":
            self._btn_menu.setText("«" if self._barra_colapsada else "»")
        else:
            self._btn_menu.setText("»" if self._barra_colapsada else "«")

    def _vestir_barra(self) -> None:
        self._vestir_boton_menu()
        colapsada = self._barra_colapsada

        for etiqueta in (self.ui.lblSeccionStock, self.ui.lblSeccionAnalisis, self.ui.lblSeccionCaja):
            etiqueta.setVisible(not colapsada)

        self._card_tienda.setVisible(not colapsada)
        self._divisor.setVisible(not colapsada)

        ancho_barra = round((self.ANCHO_BARRA_COLAPSADA if colapsada else self._ancho_pilar) * escala())
        self.ui.frameSidebar.setMinimumWidth(ancho_barra)
        self.ui.frameSidebar.setMaximumWidth(ancho_barra)

        ancho_btn = round(self.ANCHO_BOTON_COLAPSADO * escala())
        for nombre, titulo in self._titulos_sidebar.items():
            btn = getattr(self.ui, nombre, None)
            if btn is not None:
                if isinstance(btn, BotonSidebar):
                    btn.set_colapsado(colapsada, ancho_btn)
                else:
                    btn.setMinimumSize(ancho_btn if colapsada else round(200 * escala()), round(46 * escala()))
                    btn.setText("" if colapsada else titulo)
                    btn.setToolTip(titulo if colapsada else "")

        if colapsada:
            self.ui.btnUsuario.setText("")
            permiso = Usuario.ETIQUETAS_PERMISO.get(self._permiso, self._permiso)
            usuario = self._usuario_actual
            self.ui.btnUsuario.setToolTip(f"{usuario} · {permiso}" if permiso else usuario)
            self.ui.btnUsuario.setMinimumWidth(ancho_btn)
            self.ui.btnUsuario.setMaximumWidth(ancho_btn)
        else:
            self.ui.btnUsuario.setMinimumWidth(0)
            self.ui.btnUsuario.setMaximumWidth(16777215)
            self._armar_boton_usuario()
            self.ui.btnUsuario.setToolTip("")

    def _marcar_activa(self, nombre: str) -> None:
        for clave, btn in [
            ("estadisticas", self.ui.btnEstadisticas),
            ("ventas", self.ui.btnVentas),
            ("productos", self.ui.btnProductos),
            ("movimientos", self.ui.btnMovimientos),
            ("alertas", self.ui.btnAlertas),
            ("reportes", self.ui.btnReportes),
            ("cierre", self.ui.btnCierre),
            ("consulta", self.ui.btnConsulta),
            ("ajustes", self.ui.btnAjustes),
        ]:
            if isinstance(btn, BotonSidebar):
                btn.set_activo(clave == nombre)

    def showEvent(self, evento: QEvent) -> None:
        super().showEvent(evento)
        if not self._animada:
            self._animada = True
            self._animacion.start()
        self._aplicar_estilo_ventana()

    def _aplicar_estilo_ventana(self) -> None:
        try:
            aplicar_estilo_ventana(self)
        except Exception:
            pass

    def closeEvent(self, evento: QCloseEvent) -> None:
        super().closeEvent(evento)
        if self._cierre_controlado:
            return
        import os
        os._exit(0)

    def permitir_cierre(self) -> None:
        self._cierre_controlado = True

    def _al_hacer_click_usuario(self) -> None:
        respuesta = QMessageBox.question(
            self, "Cerrar sesión",
            f"¿Cerrar la sesión de {self._usuario_actual}?")
        if respuesta == QMessageBox.StandardButton.Yes:
            self.sesion_cerrada.emit()

    def eventFilter(self, objetivo: QObject, evento: QEvent) -> bool:
        if self._inicio is not None and objetivo is self._inicio and evento.type() == QEvent.Type.Resize:
            self._escalar_logo(objetivo.size())
        return super().eventFilter(objetivo, evento)

    def _escalar_logo(self, tamano: QtCore.QSize) -> None:
        if self._inicio is None:
            return
        pixmap = self._pixmap_logo
        if pixmap is None or pixmap.isNull() or tamano.width() <= 0 or tamano.height() <= 0:
            return
        self._inicio.setPixmap(
            pixmap.scaled(
                tamano,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
        )

    def verificar_alertas(self) -> None:
        criticos = self._gestor_stock.productos_criticos()
        if not criticos:
            if self._aviso_stock is not None:
                self._aviso_stock.hide()
            return
        desplazamiento = 0
        padre_notif = self._paginas if self._paginas is not None else self
        if criticos:
            if self._aviso_stock is None:
                self._aviso_stock = Notificacion(padre_notif)
            self._aviso_stock.mostrar(
                "Alerta de stock",
                self.armar_aviso_stock(
                    criticos, self.MAXIMO_ALERTAS_EN_MENSAJE),
                desplazamiento,
            )
            desplazamiento = self._aviso_stock.espacio_guardado()
        elif self._aviso_stock is not None:
            self._aviso_stock.hide()

    @staticmethod
    def armar_aviso_stock(criticos: list[Producto], maximo: int) -> str:
        ordenados = sorted(criticos, key=lambda p: (
            p.stock_actual > 0,
            p.stock_actual / p.stock_minimo if p.stock_minimo else 0,
            p.nombre.lower(),
        ))
        lineas = [
            f"• {p.nombre} (stock {formatear_cantidad(p.stock_actual)},"
            f" mínimo {formatear_cantidad(p.stock_minimo)})"
            for p in ordenados[:maximo]
        ]
        if len(ordenados) > maximo:
            lineas.append(f"+{len(ordenados) - maximo} más")
        return "Sin stock o en el mínimo:\n" + "\n".join(lineas)

    def mostrar_inicio(self) -> None:
        if self._paginas is not None:
            self._paginas.setUpdatesEnabled(False)
            self._paginas.setCurrentIndex(0)
            self._paginas.setUpdatesEnabled(True)
        self._marcar_activa("")
        self._dashboard.al_mostrar()

    def abrir_ajustes(self) -> None:
        if self._permiso and self._permiso != Usuario.PERMISO_ADMIN:
            self.mostrar_advertencia(
                "Acceso restringido",
                "Solo un administrador puede ingresar a Ajustes.",
            )
            return
        dialogo = VentanaConfiguracion(
            self._gestor_comercio,
            anulaciones=self._anulaciones,
            permiso=self._permiso,
            autenticacion=self._autenticacion,
        )
        if dialogo.exec():
            self._aplicar_posicion_sidebar()

    def abrir_alertas(self) -> None:
        self._mostrar("alertas", lambda: VentanaAlertas(self._gestor_stock))

    def abrir_reportes(self) -> None:
        def fabricar() -> VentanaReportes:
            pagina = VentanaReportes(
                self._gestor_stock, self._estadisticas, self._permiso)
            return pagina

        self._mostrar("reportes", fabricar)

    def abrir_estadisticas(self) -> None:
        self._mostrar(
            "estadisticas",
            lambda: VentanaEstadisticas(self._estadisticas, self._anulaciones),
        )

    def abrir_productos(self) -> None:
        self._mostrar(
            "productos",
            lambda: VentanaProductos(self._gestor_stock, self._permiso),
        )

    def abrir_movimientos(self) -> None:
        def fabricar() -> VentanaMovimientos:
            pagina = VentanaMovimientos(self._gestor_stock)
            pagina.ir_a_reportes.connect(self.abrir_reportes)
            pagina.ir_a_clientes.connect(self.abrir_clientes)
            return pagina

        self._mostrar("movimientos", fabricar)

    def abrir_ventas(self) -> None:
        def fabricar() -> VentanaVentas:
            pagina = VentanaVentas(
                self._gestor_ventas, self._gestor_comercio,
                self._usuario_actual, self._fiado)
            pagina.ir_a_clientes.connect(self.abrir_clientes)
            return pagina

        self._mostrar("ventas", fabricar)

    def abrir_clientes(self) -> None:
        if self._fiado is None:
            self.mostrar_advertencia(
                "Clientes", "El fiado no está disponible.")
            return
        self._mostrar(
            "clientes",
            lambda: VentanaClientes(self._fiado, self._usuario_actual),
        )

    def abrir_cierre(self) -> None:
        if self._cierre is None:
            self.mostrar_advertencia(
                "Cierre de caja", "El servicio de cierre no está disponible.")
            return
        self._mostrar(
            "cierre",
            lambda: VentanaCaja(
                self._cierre, self._usuario_actual, self._permiso,
                turnos=self._turnos, caja=self._caja),
        )

    def abrir_consulta(self) -> None:
        self._mostrar(
            "consulta",
            lambda: VentanaConsulta(self._gestor_stock, self._permiso),
        )

    def _mostrar(self, nombre: str, fabricar: Callable[[], QWidget]) -> None:
        """Muestra la página `nombre`, construyéndola con `fabricar` solo la
        primera vez: repetir la navegación no vuelve a instanciar la vista."""
        assert self._paginas is not None
        indice = self._indices.get(nombre)
        if indice is None:
            pagina = fabricar()
            minimo = pagina.minimumSize()
            if escala() != 1.0 and not minimo.isEmpty():
                pagina.setMinimumSize(round(minimo.width() * escala()), minimo.height())
            indice = self._paginas.addWidget(pagina)
            self._indices[nombre] = indice
        else:
            pagina = self._paginas.widget(indice)
            assert pagina is not None
        refrescar = getattr(pagina, "al_mostrar", None)
        if callable(refrescar):
            refrescar()
        self._paginas.setUpdatesEnabled(False)
        self._paginas.setCurrentIndex(indice)
        self._paginas.setUpdatesEnabled(True)
        self._marcar_activa(nombre)
        self._enfocar(nombre, pagina)

    def _enfocar(self, nombre: str, pagina: QWidget) -> None:
        if nombre == "consulta" and isinstance(pagina, VentanaConsulta):
            pagina.ui.txtBuscar.setFocus()
            pagina.ui.txtBuscar.selectAll()
        elif nombre == "ventas" and isinstance(pagina, VentanaVentas):
            pagina.ui.txtCodigoBarras.setFocus()
        elif nombre == "productos" and isinstance(pagina, VentanaProductos):
            pagina.ui.txtBuscar.setFocus()
        elif nombre == "clientes" and isinstance(pagina, VentanaClientes):
            pagina.ui.txtBuscar.setFocus()
