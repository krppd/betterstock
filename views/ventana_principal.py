from __future__ import annotations

from pathlib import Path
from typing import Callable

from PyQt6 import QtCore
from PyQt6.QtCore import (
    QEvent,
    QObject,
    QPropertyAnimation,
    QRect,
    QSize,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QBrush,
    QCloseEvent,
    QColor,
    QIcon,
    QImage,
    QKeySequence,
    QPainter,
    QPixmap,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    FluentIcon as FIF,
    FluentWindow,
    NavigationAvatarWidget,
    NavigationItemPosition,
    Theme,
    isDarkTheme,
    setTheme,
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
from services import preferencias
from services.turnos import ServicioTurnos
from ui.estilo_ventana import aplicar_estilo_ventana
from ui.estilos import (
    ESCALA_NORMAL,
    TAMANO_SMALL,
    aplicar_color_fluent,
    escala,
    fuente,
)
from ui.widgets.notificacion import Notificacion
from ui.widgets.sidebar import (
    ANCHO_COLAPSADO,
    ANCHO_EXPANDIDO,
    ANCHO_ITEM_COLAPSADO,
)
from utils.formato import formatear_cantidad
from views.ventana_alertas import VentanaAlertas
from views.ventana_base import VentanaBase
from views.ventana_caja import VentanaCaja
from views.ventana_clientes import VentanaClientes
from views.ventana_configuracion import VentanaConfiguracion
from views.ventana_consulta import VentanaConsulta
from views.ventana_dashboard import DashboardPrincipalWidget
from views.ventana_estadisticas import VentanaEstadisticas
from views.ventana_movimientos import VentanaMovimientos
from views.ventana_productos import VentanaProductos
from views.ventana_reportes import VentanaReportes
from views.ventana_ventas import VentanaVentas


class _BotonCompat(QPushButton):
    """Boton proxy para mantener compatibilidad con tests que inspeccionan self.ui.btn*."""

    def __init__(self, clave: str, texto: str, icono: str, accion: Callable[[], None], parent: QWidget | None = None) -> None:
        super().__init__(texto, parent)
        self.clave = clave
        self.accion = accion
        self.clicked.connect(accion)

    def set_activo(self, activo: bool) -> None:
        pass

    def set_colapsado(self, colapsado: bool, ancho: int) -> None:
        pass


class _UiCompat:
    """Proxy de compatibilidad para evitar roturas en código o tests que leían atributos legacy."""

    def __init__(self, ventana: VentanaPrincipal) -> None:
        self._ventana = ventana
        self.widget = QWidget()
        self.label = QLabel()
        self.horizontalLayout = QHBoxLayout()
        self.frameSidebar = QFrame()
        self.frameSidebar.setMinimumWidth(round(ANCHO_EXPANDIDO * escala()))
        self.lblSeccionStock = QLabel("STOCK")
        self.lblSeccionCaja = QLabel("VENTAS Y CAJA")
        self.lblSeccionAnalisis = QLabel("REPORTES")
        self.btnProductos = _BotonCompat("productos", "Productos (F1)", "productos.png", ventana.abrir_productos)
        self.btnMovimientos = _BotonCompat("movimientos", "Movimientos (F2)", "movimientos.png", ventana.abrir_movimientos)
        self.btnAlertas = _BotonCompat("alertas", "Alertas (F4)", "alertas.png", ventana.abrir_alertas)
        self.btnReportes = _BotonCompat("reportes", "Reportes", "estadisticas.png", ventana.abrir_reportes)
        self.btnEstadisticas = _BotonCompat("estadisticas", "Estadísticas (F8)", "estadisticas.png", ventana.abrir_estadisticas)
        self.btnVentas = _BotonCompat("ventas", "Ventas (F5)", "ventas.png", ventana.abrir_ventas)
        self.btnCierre = _BotonCompat("cierre", "Caja (F6)", "cierre.png", ventana.abrir_cierre)
        self.btnClientes = _BotonCompat("clientes", "Clientes (F7)", "user.png", ventana.abrir_clientes)
        self.btnConsulta = _BotonCompat("consulta", "Consulta precio (F7)", "consulta.png", ventana.abrir_consulta)
        self.btnAjustes = _BotonCompat("ajustes", "Ajustes", "ajustes.png", ventana.abrir_ajustes)
        self.btnUsuario = QPushButton(ventana)
        self.btnUsuario.setFixedSize(0, 0)
        self.btnUsuario.move(-100, -100)
        self.btnUsuario.clicked.connect(ventana._al_hacer_click_usuario)


class VentanaPrincipal(FluentWindow, VentanaBase):
    """Ventana principal rediseñada con PyQt-Fluent-Widgets (Fluent Design Windows 11)."""

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
        self._fiado = fiado
        self._gestor_ventas = gestor_ventas if gestor_ventas is not None else \
            GestorVentas(gestor_stock, estadisticas, fiado, cierre)
        self._anulaciones = anulaciones
        self._autenticacion = autenticacion
        self._turnos = turnos

        self._paginas = self.stackedWidget
        self._paginas_instanciadas: dict[str, QWidget] = {}
        self._indices: dict[str, int] = {}
        self._aviso_stock: Notificacion | None = None

        self.setWindowTitle("BetterStock")
        self.setWindowIcon(QIcon(str(RECURSOS_DIR / "logo_u.png")))
        self.setCustomBackgroundColor(QColor("#f8f9fa"), QColor("#181818"))
        self._aplicar_tema(preferencias.modo_oscuro())
        self.setMinimumSize(round(980 * escala()), 650)

        self._preparar_animacion()
        self._preparar_reloj()
        self._preparar_navegacion()
        self.navigationInterface.setMinimumExpandWidth(round(700 * escala()))
        self.navigationInterface.setExpandWidth(round(260 * escala()))
        self.navigationInterface.panel.expand(useAni=False)

        self.ui = _UiCompat(self)
        self._btn_menu = self.navigationInterface.panel.menuButton
        self._armar_boton_usuario()
        self._armar_menu_hamburguesa()

        self._conectar_atajos()
        QtCore.QTimer.singleShot(500, self.verificar_alertas)

    def _armar_menu_hamburguesa(self) -> None:
        panel = self.navigationInterface.panel
        try:
            panel.menuButton.clicked.disconnect()
        except (TypeError, RuntimeError):
            pass
        panel.menuButton.clicked.connect(lambda *_: self._alternar_barra())

    def _preparar_reloj(self) -> None:
        self._reloj = QLabel(self)
        self._reloj.setFont(fuente(TAMANO_SMALL, tabular=True))
        self._reloj.setStyleSheet("color: rgba(128, 128, 128, 0.85); padding-right: 8px;")
        layout = self.titleBar.layout()
        pos = max(0, layout.count() - 1)
        layout.insertWidget(pos, self._reloj)
        self._actualizar_reloj()
        temporizador = QtCore.QTimer(self)
        temporizador.setInterval(1000)
        temporizador.timeout.connect(self._actualizar_reloj)
        temporizador.start()

    def _actualizar_reloj(self) -> None:
        self._reloj.setText(QtCore.QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm"))

    def statusBar(self):
        class _StatusBarDummy:
            def __init__(self, reloj: QLabel) -> None:
                self._reloj = reloj

            def addPermanentWidget(self, w: QWidget) -> None:
                pass
        return _StatusBarDummy(self._reloj)

    def _preparar_animacion(self) -> None:
        self._animacion = QPropertyAnimation(self, b"windowOpacity")
        self._animacion.setDuration(200)
        self._animacion.setStartValue(0.0)
        self._animacion.setEndValue(1.0)
        self._animada = False

    @staticmethod
    def _crear_avatar_icono(icono: FIF | str | Path | QPixmap, color_fondo: str, tam: int = 48) -> QPixmap:
        pix = QPixmap(tam, tam)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(color_fondo)))
        p.drawEllipse(0, 0, tam, tam)
        if isinstance(icono, (str, Path)):
            img = QImage(str(icono))
        elif isinstance(icono, QPixmap):
            img = icono.toImage()
        else:
            svg_path = icono.path(Theme.DARK) if hasattr(icono, "path") else ""
            img = QImage(svg_path) if svg_path else QImage()
        m = round(tam * 0.22)
        p.drawImage(QRect(m, m, tam - 2 * m, tam - 2 * m), img)
        p.end()
        return pix

    @staticmethod
    def _crear_avatar_tienda(oscuro: bool = False, tam: int = 48) -> QPixmap:
        pix = QPixmap(tam, tam)
        pix.fill(Qt.GlobalColor.transparent)
        base = QPixmap(str(RECURSOS_DIR / "iconos" / "tienda.png"))
        if base.isNull():
            return pix
        m = round(tam * 0.15)
        icono_escalado = base.scaled(
            tam - 2 * m, tam - 2 * m, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        p = QPainter(pix)
        p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        p.drawPixmap(m, m, icono_escalado)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        color_tinte = QColor("#FFFFFF") if oscuro else QColor("#202020")
        p.fillRect(pix.rect(), color_tinte)
        p.end()
        return pix

    def _preparar_navegacion(self) -> None:
        self.navigationInterface.setReturnButtonVisible(False)

        nombre_tienda = "BetterStock"
        if self._gestor_comercio:
            try:
                com = self._gestor_comercio.comercio
                if com and getattr(com, "nombre", None):
                    nombre_tienda = str(com.nombre)
            except (AttributeError, Exception):
                pass
        avatar_tienda = self._crear_avatar_tienda(preferencias.modo_oscuro())
        self._card_tienda = NavigationAvatarWidget(nombre_tienda, avatar_tienda)
        self.navigationInterface.addWidget(
            routeKey="tienda",
            widget=self._card_tienda,
            onClick=self.mostrar_inicio,
            position=NavigationItemPosition.TOP,
        )

        self._dashboard = DashboardPrincipalWidget(
            gestor_stock=self._gestor_stock,
            estadisticas=self._estadisticas,
            fiado=self._fiado,
            usuario=self._usuario_actual or "Admin",
            parent=self,
        )
        self._dashboard.setObjectName("inicio")
        self.addSubInterface(self._dashboard, FIF.HOME, "Inicio")
        self._indices["inicio"] = 0
        self._paginas_instanciadas["inicio"] = self._dashboard

        self.navigationInterface.addSeparator(NavigationItemPosition.SCROLL)
        self.navigationInterface.addItemHeader("STOCK", NavigationItemPosition.SCROLL)
        self.navigationInterface.addItem(
            "productos", FIF.TAG, "Productos (F1)", self.abrir_productos, position=NavigationItemPosition.SCROLL
        )
        self.navigationInterface.addItem(
            "movimientos", FIF.HISTORY, "Movimientos (F2)", self.abrir_movimientos, position=NavigationItemPosition.SCROLL
        )
        self.navigationInterface.addItem(
            "alertas", FIF.RINGER, "Alertas (F4)", self.abrir_alertas, position=NavigationItemPosition.SCROLL
        )

        self.navigationInterface.addSeparator(NavigationItemPosition.SCROLL)
        self.navigationInterface.addItemHeader("VENTAS Y CAJA", NavigationItemPosition.SCROLL)
        self.navigationInterface.addItem(
            "ventas", FIF.SHOPPING_CART, "Ventas (F5)", self.abrir_ventas, position=NavigationItemPosition.SCROLL
        )
        self.navigationInterface.addItem(
            "cierre", FIF.ACCEPT_MEDIUM, "Caja (F6)", self.abrir_cierre, position=NavigationItemPosition.SCROLL
        )
        self.navigationInterface.addItem(
            "consulta", FIF.SEARCH, "Consulta precio (F7)", self.abrir_consulta, position=NavigationItemPosition.SCROLL
        )

        self.navigationInterface.addSeparator(NavigationItemPosition.SCROLL)
        self.navigationInterface.addItemHeader("REPORTES", NavigationItemPosition.SCROLL)
        self.navigationInterface.addItem(
            "estadisticas", FIF.PIE_SINGLE, "Estadísticas (F8)", self.abrir_estadisticas, position=NavigationItemPosition.SCROLL
        )

        self.navigationInterface.addItem(
            "theme",
            FIF.BRIGHTNESS,
            "Modo claro" if isDarkTheme() else "Modo oscuro",
            self._alternar_tema,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

        etiqueta = Usuario.ETIQUETAS_PERMISO.get(self._permiso, self._permiso)
        nombre_user = f"{self._usuario_actual} ({etiqueta})" if etiqueta else (self._usuario_actual or "Usuario")
        avatar_user = self._crear_avatar_icono(FIF.PEOPLE, "#2DBC66")
        self._card_usuario = NavigationAvatarWidget(nombre_user, avatar_user)
        self.navigationInterface.addWidget(
            routeKey="usuario",
            widget=self._card_usuario,
            onClick=self._al_hacer_click_usuario,
            position=NavigationItemPosition.BOTTOM,
        )

        self.navigationInterface.addItem(
            "ajustes",
            FIF.SETTING,
            "Ajustes",
            self.abrir_ajustes,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

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
        self.ui.btnUsuario.setIcon(QIcon(str(RECURSOS_DIR / "iconos" / "user.png")))

    def _conectar_atajos(self) -> None:
        atajos = (
            (Qt.Key.Key_F1, self.abrir_productos),
            (Qt.Key.Key_F2, self.abrir_movimientos),
            (Qt.Key.Key_F4, self.abrir_alertas),
            (Qt.Key.Key_F5, self.abrir_ventas),
            (Qt.Key.Key_F6, self.abrir_cierre),
            (Qt.Key.Key_F7, self.abrir_consulta),
            (Qt.Key.Key_F8, self.abrir_estadisticas),
            (Qt.Key.Key_Escape, self.mostrar_inicio),
        )
        for tecla, destino in atajos:
            QShortcut(QKeySequence(tecla), self).activated.connect(destino)

    def _alternar_barra(self, animar: bool = True) -> None:
        panel = self.navigationInterface.panel
        if panel.isCollapsed():
            panel.expand(useAni=animar)
        else:
            panel.collapse()
            if not animar:
                panel.expandAni.stop()
                panel._onExpandAniFinished()

    def _aplicar_tema(self, oscuro: bool) -> None:
        setTheme(Theme.DARK if oscuro else Theme.LIGHT)
        aplicar_color_fluent(oscuro=oscuro)
        if hasattr(self, "_card_tienda"):
            self._card_tienda.setAvatar(self._crear_avatar_tienda(oscuro))
        self._actualizar_texto_tema()

    def _actualizar_texto_tema(self) -> None:
        try:
            item = self.navigationInterface.widget("theme")
        except Exception:
            item = None
        if item is not None:
            txt = "Modo claro" if isDarkTheme() else "Modo oscuro"
            item.setText(txt)
            item.setToolTip(txt)

    def _alternar_tema(self) -> None:
        oscuro = not isDarkTheme()
        self._aplicar_tema(oscuro)
        preferencias.guardar_modo_oscuro(oscuro)

    def _marcar_activa(self, nombre: str) -> None:
        if nombre and self.navigationInterface.widget(nombre) is not None:
            self.navigationInterface.setCurrentItem(nombre)

    def _aplicar_posicion_sidebar(self, posicion: str | None = None) -> None:
        pass

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

    def verificar_alertas(self) -> None:
        criticos = self._gestor_stock.productos_criticos()
        if not criticos:
            if self._aviso_stock is not None:
                self._aviso_stock.hide()
            return
        desplazamiento = 0
        padre_notif = self.stackedWidget if hasattr(self, "stackedWidget") else self
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
        self.switchTo(self._dashboard)
        self.navigationInterface.setCurrentItem("inicio")
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
        nombre_com = ""
        if self._gestor_comercio and hasattr(self._gestor_comercio, "comercio") and self._gestor_comercio.comercio:
            nombre_com = getattr(self._gestor_comercio.comercio, "nombre", "") or ""
        self._mostrar(
            "cierre",
            lambda: VentanaCaja(
                self._cierre, self._usuario_actual, self._permiso,
                nombre_comercio=nombre_com, turnos=self._turnos, caja=self._caja),
        )

    def abrir_consulta(self) -> None:
        self._mostrar(
            "consulta",
            lambda: VentanaConsulta(self._gestor_stock, self._permiso),
        )

    def _mostrar(self, nombre: str, fabricar: Callable[[], QWidget]) -> None:
        """Muestra la página `nombre`, construyéndola con `fabricar` solo la primera vez."""
        pagina = self._paginas_instanciadas.get(nombre)
        if pagina is None:
            pagina = fabricar()
            pagina.setObjectName(nombre)
            minimo = pagina.minimumSize()
            if escala() != 1.0 and not minimo.isEmpty():
                pagina.setMinimumSize(round(minimo.width() * escala()), minimo.height())
            self._paginas.addWidget(pagina)
            indice = self._paginas.indexOf(pagina)
            self._indices[nombre] = indice
            self._paginas_instanciadas[nombre] = pagina
        else:
            indice = self._indices[nombre]

        refrescar = getattr(pagina, "al_mostrar", None)
        if callable(refrescar):
            refrescar()

        self._paginas.setUpdatesEnabled(False)
        self.switchTo(pagina)
        self._paginas.setUpdatesEnabled(True)

        if self.navigationInterface.widget(nombre) is not None:
            self.navigationInterface.setCurrentItem(nombre)

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
