import QtQuick
import QtQuick.Layouts

Rectangle {
    id: raiz
    color: Tema.color("transparente")
    property real escala: 1.0
    property int columnas: 4
    property real separacion: Tema.espaciado("basico")
    readonly property bool entranAtajos: desplazador.anchoBoton >= Math.max(
        btnDescuento.necesitaAncho, btnRecargo.necesitaAncho,
        btnComprobante.necesitaAncho, btnCuentas.necesitaAncho)
    signal descuentoPedido
    signal recargoPedido
    signal comprobantePedido
    signal cuentasPedido
    signal cobrarPedido
    function destellar() {
        btnCobrar.destellar()
    }
    ColumnLayout {
        anchors.fill: parent
        spacing: Tema.espaciado("basico")
        Flickable {
            id: desplazador
            objectName: "accionesScroll"
            Layout.fillWidth: true
            Layout.preferredHeight: Math.round(Tema.medida("alto_boton") * raiz.escala)
            contentWidth: Math.max(width, fila.width)
            contentHeight: Math.max(height, fila.height)
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            flickableDirection: Flickable.HorizontalFlick
            readonly property real anchoBoton: Math.max(0, (width - raiz.separacion * (raiz.columnas - 1)) / raiz.columnas)
            Row {
                id: fila
                spacing: raiz.separacion
                PosActionButton {
                    id: btnDescuento
                    objectName: "accionDescuento"
                    texto: "Desc. total"
                    atajo: "Alt+D"
                    escala: raiz.escala
                    mostrarAtajo: raiz.entranAtajos
                    height: Math.round(Tema.medida("alto_boton") * raiz.escala)
                    width: Math.max(implicitWidth, desplazador.anchoBoton)
                    onClicado: raiz.descuentoPedido()
                }
                PosActionButton {
                    id: btnRecargo
                    objectName: "accionRecargo"
                    texto: "Recargo"
                    atajo: "Alt+R"
                    escala: raiz.escala
                    mostrarAtajo: raiz.entranAtajos
                    height: Math.round(Tema.medida("alto_boton") * raiz.escala)
                    width: Math.max(implicitWidth, desplazador.anchoBoton)
                    onClicado: raiz.recargoPedido()
                }
                PosActionButton {
                    id: btnComprobante
                    objectName: "accionComprobante"
                    texto: "Último comprobante"
                    atajo: "Alt+E"
                    escala: raiz.escala
                    mostrarAtajo: raiz.entranAtajos
                    height: Math.round(Tema.medida("alto_boton") * raiz.escala)
                    width: Math.max(implicitWidth, desplazador.anchoBoton)
                    onClicado: raiz.comprobantePedido()
                }
                PosActionButton {
                    id: btnCuentas
                    objectName: "accionCuentas"
                    texto: "Cuentas"
                    atajo: "Alt+C"
                    escala: raiz.escala
                    mostrarAtajo: raiz.entranAtajos
                    height: Math.round(Tema.medida("alto_boton") * raiz.escala)
                    width: Math.max(implicitWidth, desplazador.anchoBoton)
                    onClicado: raiz.cuentasPedido()
                }
            }
        }
        PrimaryCobrarButton {
            id: btnCobrar
            objectName: "accionCobrar"
            texto: "Cobrar Venta"
            atajo: "↵ Enter"
            escala: raiz.escala
            Layout.fillWidth: true
            Layout.preferredHeight: Math.round(Tema.medida("alto_cobrar") * raiz.escala)
            onClicado: raiz.cobrarPedido()
        }
    }
}
