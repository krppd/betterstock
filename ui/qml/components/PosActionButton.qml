import QtQuick
import QtQuick.Layouts
import QtQuick.Effects

Rectangle {
    id: raiz
    property string texto: ""
    property string atajo: ""
    property real escala: 1.0
    property bool mostrarAtajo: true
    property real anchoTexto: metricaTexto.advanceWidth
    property real anchoEtiqueta: etiqueta.width
    property real anchoInsigniaCompleta: insignia.implicitWidth + Tema.medida("margen_insignia")
    property real anchoInsignia: raiz.mostrarAtajo ? raiz.anchoInsigniaCompleta : 0
    property real necesitaAncho: Math.ceil(anchoTexto + anchoInsigniaCompleta + 32)
    signal clicado
    implicitWidth: Math.ceil(anchoTexto + anchoInsignia + 32)
    implicitHeight: Math.round(Tema.medida("alto_boton") * raiz.escala)
    color: Tema.color("blanco")
    radius: Tema.radio("panel")
    border.width: Tema.medida("grosor_borde")
    border.color: area.containsMouse ? Tema.color("borde_destacado") : Tema.color("borde_suave")
    layer.enabled: true
    layer.effect: MultiEffect {
        shadowEnabled: true
        shadowColor: Tema.sombra("boton").color
        shadowBlur: Tema.sombra("boton").difuminado
        shadowVerticalOffset: Tema.sombra("boton").desplazamiento
    }
    TextMetrics {
        id: metricaTexto
        font: etiqueta.font
        text: raiz.texto
    }
    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: Tema.espaciado("grande")
        anchors.rightMargin: Tema.espaciado("basico")
        spacing: Tema.espaciado("basico")
        Text {
            id: etiqueta
            Layout.fillWidth: true
            text: raiz.texto
            color: Tema.color("texto_fuerte")
            font.weight: Tema.peso("medio")
            font.pointSize: Math.round(Tema.tamano("pequeno") * raiz.escala)
            elide: Text.ElideRight
        }
        Rectangle {
            visible: raiz.mostrarAtajo
            Layout.preferredHeight: Math.round(Tema.medida("alto_insignia") * raiz.escala)
            Layout.preferredWidth: raiz.anchoInsigniaCompleta
            color: Tema.color("fondo_insignia")
            radius: Tema.radio("insignia")
            border.width: Tema.medida("grosor_borde")
            border.color: Tema.color("borde_destacado")
            Text {
                id: insignia
                anchors.centerIn: parent
                text: raiz.atajo
                color: Tema.color("gris_medio")
                font.pointSize: Math.round(Tema.tamano("micro") * raiz.escala)
            }
        }
    }
    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            raiz.triggerVisualPulse()
            raiz.clicado()
        }
    }
    function triggerVisualPulse() {
        animPulso.stop()
        raiz.scale = 0.95
        animPulso.start()
    }
    NumberAnimation {
        id: animPulso
        target: raiz
        property: "scale"
        to: 1.0
        duration: 140
        easing.type: Easing.OutQuad
    }
}
