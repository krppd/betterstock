import QtQuick
import QtQuick.Layouts
import QtQuick.Effects

Rectangle {
    id: raiz
    property string texto: "Cobrar Venta"
    property string atajo: "↵ Enter"
    property bool habilitado: true
    property real escala: 1.0
    signal clicado
    implicitWidth: Tema.medida("ancho_boton_cobrar")
    implicitHeight: Math.round(Tema.medida("alto_boton") * raiz.escala)
    radius: Tema.radio("destacado")
    opacity: habilitado ? 1.0 : 0.45
    scale: area.pressed && habilitado ? 0.98 : 1.0
    Behavior on scale { NumberAnimation { duration: 80 } }
    gradient: Gradient {
        orientation: Gradient.Vertical
        GradientStop {
            position: 0.0
            color: !habilitado ? Tema.color("gris_apagado")
                                : (area.pressed ? Tema.color("verde_oscuro")
                                                 : (area.containsMouse ? Tema.color("verde_claro")
                                                                      : Tema.color("verde")))
        }
        GradientStop {
            position: 1.0
            color: !habilitado ? Tema.color("gris_medio")
                                : (area.pressed ? Tema.color("verde_presionado")
                                                 : (area.containsMouse ? Tema.color("verde")
                                                                      : Tema.color("verde_oscuro")))
        }
    }
    layer.enabled: true
    layer.effect: MultiEffect {
        shadowEnabled: true
        shadowColor: Tema.sombra("boton_principal").color
        shadowBlur: Tema.sombra("boton_principal").difuminado
        shadowVerticalOffset: Tema.sombra("boton_principal").desplazamiento
    }
    Rectangle {
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.leftMargin: Tema.medida("margen_boton")
        anchors.right: parent.right
        anchors.rightMargin: Tema.medida("margen_boton")
        height: Tema.medida("grosor_borde")
        color: Tema.color("brillo_linea")
    }
    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: Tema.espaciado("extra")
        anchors.rightMargin: Tema.espaciado("grande")
        spacing: Tema.espaciado("mediano")
        Text {
            Layout.fillWidth: true
            text: raiz.texto
            color: Tema.color("blanco")
            font.weight: Tema.peso("negrita")
            font.pointSize: Math.round(Tema.tamano("cuerpo") * raiz.escala)
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
        }
        Rectangle {
            Layout.preferredHeight: Math.round(Tema.medida("alto_tecla") * raiz.escala)
            Layout.preferredWidth: tecla.implicitWidth + Tema.medida("margen_insignia")
            color: Tema.color("brillo_tecla")
            radius: Tema.radio("insignia")
            Text {
                id: tecla
                anchors.centerIn: parent
                text: raiz.atajo
                color: Tema.color("blanco")
                font.pointSize: Math.round(Tema.tamano("micro") * raiz.escala)
                font.weight: Tema.peso("negrita")
            }
        }
    }
    Rectangle {
        anchors.fill: parent
        radius: Tema.radio("destacado")
        color: Tema.color("transparente")
        clip: true
        Rectangle {
            id: brillo
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: Tema.medida("ancho_brillo")
            x: -80
            rotation: 20
            opacity: 0
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: Tema.color("brillo_boton_fin") }
                GradientStop { position: 0.5; color: Tema.color("brillo_boton") }
                GradientStop { position: 1.0; color: Tema.color("brillo_boton_fin") }
            }
        }
    }
    MouseArea {
        id: area
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: raiz.clicado()
    }
    function destellar() {
        animDestello.restart()
    }
    SequentialAnimation {
        id: animDestello
        PropertyAction { target: brillo; property: "opacity"; value: 1 }
        PropertyAction { target: brillo; property: "x"; value: -80 }
        NumberAnimation { target: brillo; property: "x"; to: raiz.width + 40; duration: 250; easing.type: Easing.OutQuad }
        PropertyAction { target: brillo; property: "opacity"; value: 0 }
    }
}
