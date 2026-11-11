import QtQuick
import QtQuick.Layouts
import QtQuick.Effects
import QtQuick.Shapes

Rectangle {
    id: raiz
    color: Tema.color("superficie")
    property int altoTarjetas: Tema.medida("alto_tarjeta")
    property int altoBanda: Tema.medida("alto_banda")
    property int tarjetaActiva: -1

    component Sparkline: Item {
        id: spark
        property var valores: []
        property color colorLinea: Tema.color("verde_texto")
        implicitHeight: Tema.medida("alto_sparkline")

        Canvas {
            id: lienzo
            anchors.fill: parent
            antialiasing: true
            onPaint: spark.pintar()
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
        }

        onValoresChanged: lienzo.requestPaint()
        onColorLineaChanged: lienzo.requestPaint()
        Component.onCompleted: lienzo.requestPaint()

        function colorRgba(color, alfa) {
            return "rgba(" + Math.round(color.r * 255) + "," + Math.round(color.g * 255) + ","
                    + Math.round(color.b * 255) + "," + alfa + ")";
        }

        function normalizar() {
            var numeros = [];
            var total = valores ? valores.length : 0;
            for (var i = 0; i < total; i++) {
                var numero = Number(valores[i]);
                if (!isNaN(numero))
                    numeros.push(numero);
            }
            if (numeros.length === 0)
                return [];
            var minimo = numeros[0];
            var maximo = numeros[0];
            for (i = 1; i < numeros.length; i++) {
                if (numeros[i] < minimo)
                    minimo = numeros[i];
                if (numeros[i] > maximo)
                    maximo = numeros[i];
            }
            var rango = maximo - minimo;
            if (rango <= 0)
                rango = 1;
            var margen = 3;
            var anchoZona = Math.max(0, lienzo.width - 2 * margen);
            var altoZona = Math.max(0, lienzo.height - 2 * margen);
            var cantidad = numeros.length;
            var puntos = [];
            for (i = 0; i < cantidad; i++) {
                var x = (cantidad === 1) ? margen + anchoZona / 2 : margen + anchoZona * i / (cantidad - 1);
                var y = margen + altoZona * (1 - (numeros[i] - minimo) / rango);
                puntos.push({x: x, y: y});
            }
            return puntos;
        }

        function curvaSuave(puntos) {
            var total = puntos.length;
            var tramos = [];
            for (var i = 0; i < total - 1; i++) {
                var p0 = puntos[Math.max(0, i - 1)];
                var p1 = puntos[i];
                var p2 = puntos[i + 1];
                var p3 = puntoExtremo(puntos, i + 2);
                tramos.push({
                    c1x: p1.x + (p2.x - p0.x) / 6,
                    c1y: p1.y + (p2.y - p0.y) / 6,
                    c2x: p2.x - (p3.x - p1.x) / 6,
                    c2y: p2.y - (p3.y - p1.y) / 6,
                    x: p2.x,
                    y: p2.y
                });
            }
            return tramos;
        }

        function puntoExtremo(puntos, indice) {
            return puntos[Math.min(puntos.length - 1, indice)];
        }

        function pintar() {
            var ctx = lienzo.getContext("2d");
            ctx.reset();
            var puntos = normalizar();
            if (puntos.length === 0)
                return;
            var alto = lienzo.height;
            if (puntos.length === 1) {
                ctx.fillStyle = colorRgba(colorLinea, 1);
                ctx.beginPath();
                ctx.arc(puntos[0].x, puntos[0].y, 2.5, 0, Math.PI * 2);
                ctx.fill();
                return;
            }
            var tramos = curvaSuave(puntos);
            ctx.beginPath();
            ctx.moveTo(puntos[0].x, puntos[0].y);
            for (var i = 0; i < tramos.length; i++)
                ctx.bezierCurveTo(tramos[i].c1x, tramos[i].c1y, tramos[i].c2x, tramos[i].c2y, tramos[i].x, tramos[i].y);
            ctx.lineTo(puntos[puntos.length - 1].x, alto);
            ctx.lineTo(puntos[0].x, alto);
            ctx.closePath();
            ctx.fillStyle = colorRgba(colorLinea, 30 / 255);
            ctx.fill();
            ctx.beginPath();
            ctx.moveTo(puntos[0].x, puntos[0].y);
            for (i = 0; i < tramos.length; i++)
                ctx.bezierCurveTo(tramos[i].c1x, tramos[i].c1y, tramos[i].c2x, tramos[i].c2y, tramos[i].x, tramos[i].y);
            ctx.strokeStyle = colorRgba(colorLinea, 1);
            ctx.lineWidth = 2;
            ctx.lineCap = "round";
            ctx.lineJoin = "round";
            ctx.stroke();
        }
    }

    function badgeTexto(variacion, tendencia) {
        if (tendencia === 0)
            return variacion.indexOf("Nuevo") >= 0 ? "• Nuevo período" : "• Sin cambios";
        var numero = variacion;
        if (numero.length > 1 && (numero.charAt(0) === "▲" || numero.charAt(0) === "▼"))
            numero = numero.slice(2);
        if (tendencia > 0) {
            if (numero.charAt(0) !== "+")
                numero = "+" + numero;
            return "▲ " + numero;
        }
        return "▼ " + numero;
    }

    function colorTendencia(tendencia) {
        if (tendencia > 0)
            return Tema.color("tendencia_alta");
        if (tendencia < 0)
            return Tema.color("tendencia_baja");
        return Tema.color("tendencia_neutra");
    }

    function fijarTarjeta(indice, sobre) {
        if (sobre)
            raiz.tarjetaActiva = indice;
        else if (raiz.tarjetaActiva === indice)
            raiz.tarjetaActiva = -1;
    }

    function xTarjeta(indice) {
        if (indice < 0)
            return 0;
        var ancho = (filaTarjetas.width - filaTarjetas.spacing * 3) / 4;
        return indice * (ancho + filaTarjetas.spacing);
    }

    function datosTarjeta(indice) {
        var titulo = "";
        var valor = "";
        var variacion = "";
        var tendencia = 0;
        var detalle = null;
        var periodo = "";
        if (puente) {
            periodo = puente.periodoDescripcion;
            if (indice === 0) {
                titulo = "Ventas";
                valor = puente.ventasValor;
                variacion = puente.ventasVariacion;
                tendencia = puente.ventasTendencia;
                detalle = puente.ventasDetalle;
            } else if (indice === 1) {
                titulo = "Unidades";
                valor = puente.unidadesValor;
                variacion = puente.unidadesVariacion;
                tendencia = puente.unidadesTendencia;
                detalle = puente.unidadesDetalle;
            } else if (indice === 2) {
                titulo = "Facturado";
                valor = puente.totalValor;
                variacion = puente.totalVariacion;
                tendencia = puente.totalTendencia;
                detalle = puente.totalDetalle;
            } else if (indice === 3) {
                titulo = "Ticket promedio";
                valor = puente.ticketValor;
                variacion = puente.ticketVariacion;
                tendencia = puente.ticketTendencia;
                detalle = puente.ticketDetalle;
            }
        }
        var datos = detalle ? detalle : {};
        return {
            titulo: titulo,
            valor: valor,
            variacion: badgeTexto(variacion, tendencia),
            tendencia: tendencia,
            periodo: periodo,
            maximo: datos.maximo !== undefined ? datos.maximo : "—",
            minimo: datos.minimo !== undefined ? datos.minimo : "—",
            promedio: datos.promedio !== undefined ? datos.promedio : "—",
            dias: datos.diasConVentas !== undefined ? datos.diasConVentas : 0,
            diasPeriodo: datos.diasPeriodo !== undefined ? datos.diasPeriodo : 0
        };
    }

    RowLayout {
        id: filaTarjetas
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: raiz.altoTarjetas
        spacing: Tema.espaciado("grande")

        Rectangle {
            id: tarjetaVentas
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: Tema.color("tarjeta_fondo")
            radius: Tema.radio("tarjeta")
            border.color: Tema.color("borde_tarjeta")
            border.width: Tema.medida("grosor_borde")
            layer.enabled: true
            layer.effect: MultiEffect {
                shadowEnabled: true
                shadowColor: Tema.sombra("tarjeta").color
                shadowBlur: Tema.sombra("tarjeta").difuminado
                shadowVerticalOffset: Tema.sombra("tarjeta").desplazamiento
            }
            HoverHandler {
                id: hoverVentas
                onHoveredChanged: raiz.fijarTarjeta(0, hovered)
            }
            Shape {
                anchors.fill: parent
                visible: hoverVentas.hovered
                ShapePath {
                    strokeWidth: 0
                    startX: 0
                    startY: 0
                    PathLine { x: tarjetaVentas.width; y: 0 }
                    PathLine { x: tarjetaVentas.width; y: tarjetaVentas.height }
                    PathLine { x: 0; y: tarjetaVentas.height }
                    PathLine { x: 0; y: 0 }
                    fillGradient: RadialGradient {
                        centerX: hoverVentas.point.position.x
                        centerY: hoverVentas.point.position.y
                        centerRadius: Tema.medida("radio_hover")
                        focalX: centerX
                        focalY: centerY
                        GradientStop { position: 0.0; color: Tema.color("verde_realce") }
                        GradientStop { position: 1.0; color: Tema.color("verde_realce_fin") }
                    }
                }
            }
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: Tema.medida("margen_tarjeta")
                spacing: Tema.espaciado("pico")
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Ventas"
                        font.family: Tema.familia()
                        font.pointSize: Tema.tamano("micro")
                        color: Tema.color("texto_secundario")
                    }
                    Item { Layout.fillWidth: true }
                    Rectangle {
                        Layout.preferredHeight: Tema.medida("alto_pastilla")
                        implicitWidth: txtPillVentas.implicitWidth + Tema.medida("margen_pastilla")
                        radius: Tema.radio("control")
                        color: (puente && puente.ventasTendencia > 0) ? Tema.color("pastilla_positiva") : ((puente && puente.ventasTendencia < 0) ? Tema.color("pastilla_negativa") : Tema.color("pastilla_neutra"))
                        Text {
                            id: txtPillVentas
                            anchors.centerIn: parent
                            font.family: Tema.familia()
                            font.pointSize: Tema.tamano("micro")
                            font.weight: Tema.peso("negrita")
                            color: (puente && puente.ventasTendencia > 0) ? Tema.color("verde_texto") : ((puente && puente.ventasTendencia < 0) ? Tema.color("rojo_texto") : Tema.color("texto_secundario"))
                            text: badgeTexto(puente ? puente.ventasVariacion : "", puente ? puente.ventasTendencia : 0)
                        }
                    }
                }
                Text {
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                    text: (puente ? puente.ventasValor : "")
                    font.family: Tema.familia()
                    font.pointSize: Tema.tamano("titulo")
                    font.weight: Tema.peso("negrita")
                    font.features: Tema.caracteristicas()
                    color: Tema.color("texto_valor")
                }
                Sparkline {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 24
                    valores: (puente ? puente.serieVentas : [])
                    colorLinea: Tema.color("verde_texto")
                }
            }
        }

        Rectangle {
            id: tarjetaUnidades
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: Tema.color("tarjeta_fondo")
            radius: Tema.radio("tarjeta")
            border.color: Tema.color("borde_tarjeta")
            border.width: Tema.medida("grosor_borde")
            layer.enabled: true
            layer.effect: MultiEffect {
                shadowEnabled: true
                shadowColor: Tema.sombra("tarjeta").color
                shadowBlur: Tema.sombra("tarjeta").difuminado
                shadowVerticalOffset: Tema.sombra("tarjeta").desplazamiento
            }
            HoverHandler {
                id: hoverUnidades
                onHoveredChanged: raiz.fijarTarjeta(1, hovered)
            }
            Shape {
                anchors.fill: parent
                visible: hoverUnidades.hovered
                ShapePath {
                    strokeWidth: 0
                    startX: 0
                    startY: 0
                    PathLine { x: tarjetaUnidades.width; y: 0 }
                    PathLine { x: tarjetaUnidades.width; y: tarjetaUnidades.height }
                    PathLine { x: 0; y: tarjetaUnidades.height }
                    PathLine { x: 0; y: 0 }
                    fillGradient: RadialGradient {
                        centerX: hoverUnidades.point.position.x
                        centerY: hoverUnidades.point.position.y
                        centerRadius: Tema.medida("radio_hover")
                        focalX: centerX
                        focalY: centerY
                        GradientStop { position: 0.0; color: Tema.color("verde_realce") }
                        GradientStop { position: 1.0; color: Tema.color("verde_realce_fin") }
                    }
                }
            }
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: Tema.medida("margen_tarjeta")
                spacing: Tema.espaciado("pico")
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Unidades"
                        font.family: Tema.familia()
                        font.pointSize: Tema.tamano("micro")
                        color: Tema.color("texto_secundario")
                    }
                    Item { Layout.fillWidth: true }
                    Rectangle {
                        Layout.preferredHeight: Tema.medida("alto_pastilla")
                        implicitWidth: txtPillUnidades.implicitWidth + Tema.medida("margen_pastilla")
                        radius: Tema.radio("control")
                        color: (puente && puente.unidadesTendencia > 0) ? Tema.color("pastilla_positiva") : ((puente && puente.unidadesTendencia < 0) ? Tema.color("pastilla_negativa") : Tema.color("pastilla_neutra"))
                        Text {
                            id: txtPillUnidades
                            anchors.centerIn: parent
                            font.family: Tema.familia()
                            font.pointSize: Tema.tamano("micro")
                            font.weight: Tema.peso("negrita")
                            color: (puente && puente.unidadesTendencia > 0) ? Tema.color("verde_texto") : ((puente && puente.unidadesTendencia < 0) ? Tema.color("rojo_texto") : Tema.color("texto_secundario"))
                            text: badgeTexto(puente ? puente.unidadesVariacion : "", puente ? puente.unidadesTendencia : 0)
                        }
                    }
                }
                Text {
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                    text: (puente ? puente.unidadesValor : "")
                    font.family: Tema.familia()
                    font.pointSize: Tema.tamano("titulo")
                    font.weight: Tema.peso("negrita")
                    font.features: Tema.caracteristicas()
                    color: Tema.color("texto_valor")
                }
                Sparkline {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 24
                    valores: (puente ? puente.serieUnidades : [])
                    colorLinea: Tema.color("serie_azul")
                }
            }
        }

        Rectangle {
            id: tarjetaTotal
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: Tema.color("tarjeta_fondo")
            radius: Tema.radio("tarjeta")
            border.color: Tema.color("borde_tarjeta")
            border.width: Tema.medida("grosor_borde")
            layer.enabled: true
            layer.effect: MultiEffect {
                shadowEnabled: true
                shadowColor: Tema.sombra("tarjeta").color
                shadowBlur: Tema.sombra("tarjeta").difuminado
                shadowVerticalOffset: Tema.sombra("tarjeta").desplazamiento
            }
            HoverHandler {
                id: hoverTotal
                onHoveredChanged: raiz.fijarTarjeta(2, hovered)
            }
            Shape {
                anchors.fill: parent
                visible: hoverTotal.hovered
                ShapePath {
                    strokeWidth: 0
                    startX: 0
                    startY: 0
                    PathLine { x: tarjetaTotal.width; y: 0 }
                    PathLine { x: tarjetaTotal.width; y: tarjetaTotal.height }
                    PathLine { x: 0; y: tarjetaTotal.height }
                    PathLine { x: 0; y: 0 }
                    fillGradient: RadialGradient {
                        centerX: hoverTotal.point.position.x
                        centerY: hoverTotal.point.position.y
                        centerRadius: Tema.medida("radio_hover")
                        focalX: centerX
                        focalY: centerY
                        GradientStop { position: 0.0; color: Tema.color("verde_realce") }
                        GradientStop { position: 1.0; color: Tema.color("verde_realce_fin") }
                    }
                }
            }
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: Tema.medida("margen_tarjeta")
                spacing: Tema.espaciado("pico")
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Facturado"
                        font.family: Tema.familia()
                        font.pointSize: Tema.tamano("micro")
                        color: Tema.color("texto_secundario")
                    }
                    Item { Layout.fillWidth: true }
                    Rectangle {
                        Layout.preferredHeight: Tema.medida("alto_pastilla")
                        implicitWidth: txtPillTotal.implicitWidth + Tema.medida("margen_pastilla")
                        radius: Tema.radio("control")
                        color: (puente && puente.totalTendencia > 0) ? Tema.color("pastilla_positiva") : ((puente && puente.totalTendencia < 0) ? Tema.color("pastilla_negativa") : Tema.color("pastilla_neutra"))
                        Text {
                            id: txtPillTotal
                            anchors.centerIn: parent
                            font.family: Tema.familia()
                            font.pointSize: Tema.tamano("micro")
                            font.weight: Tema.peso("negrita")
                            color: (puente && puente.totalTendencia > 0) ? Tema.color("verde_texto") : ((puente && puente.totalTendencia < 0) ? Tema.color("rojo_texto") : Tema.color("texto_secundario"))
                            text: badgeTexto(puente ? puente.totalVariacion : "", puente ? puente.totalTendencia : 0)
                        }
                    }
                }
                Text {
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                    text: (puente ? puente.totalValor : "")
                    font.family: Tema.familia()
                    font.pointSize: Tema.tamano("titulo")
                    font.weight: Tema.peso("negrita")
                    font.features: Tema.caracteristicas()
                    color: Tema.color("texto_valor")
                }
                Sparkline {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 24
                    valores: (puente ? puente.serieFacturado : [])
                    colorLinea: Tema.color("verde")
                }
            }
        }

        Rectangle {
            id: tarjetaTicket
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: Tema.color("tarjeta_fondo")
            radius: Tema.radio("tarjeta")
            border.color: Tema.color("borde_tarjeta")
            border.width: Tema.medida("grosor_borde")
            layer.enabled: true
            layer.effect: MultiEffect {
                shadowEnabled: true
                shadowColor: Tema.sombra("tarjeta").color
                shadowBlur: Tema.sombra("tarjeta").difuminado
                shadowVerticalOffset: Tema.sombra("tarjeta").desplazamiento
            }
            HoverHandler {
                id: hoverTicket
                onHoveredChanged: raiz.fijarTarjeta(3, hovered)
            }
            Shape {
                anchors.fill: parent
                visible: hoverTicket.hovered
                ShapePath {
                    strokeWidth: 0
                    startX: 0
                    startY: 0
                    PathLine { x: tarjetaTicket.width; y: 0 }
                    PathLine { x: tarjetaTicket.width; y: tarjetaTicket.height }
                    PathLine { x: 0; y: tarjetaTicket.height }
                    PathLine { x: 0; y: 0 }
                    fillGradient: RadialGradient {
                        centerX: hoverTicket.point.position.x
                        centerY: hoverTicket.point.position.y
                        centerRadius: Tema.medida("radio_hover")
                        focalX: centerX
                        focalY: centerY
                        GradientStop { position: 0.0; color: Tema.color("verde_realce") }
                        GradientStop { position: 1.0; color: Tema.color("verde_realce_fin") }
                    }
                }
            }
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: Tema.medida("margen_tarjeta")
                spacing: Tema.espaciado("pico")
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Ticket promedio"
                        font.family: Tema.familia()
                        font.pointSize: Tema.tamano("micro")
                        color: Tema.color("texto_secundario")
                    }
                    Item { Layout.fillWidth: true }
                    Rectangle {
                        Layout.preferredHeight: Tema.medida("alto_pastilla")
                        implicitWidth: txtPillTicket.implicitWidth + Tema.medida("margen_pastilla")
                        radius: Tema.radio("control")
                        color: (puente && puente.ticketTendencia > 0) ? Tema.color("pastilla_positiva") : ((puente && puente.ticketTendencia < 0) ? Tema.color("pastilla_negativa") : Tema.color("pastilla_neutra"))
                        Text {
                            id: txtPillTicket
                            anchors.centerIn: parent
                            font.family: Tema.familia()
                            font.pointSize: Tema.tamano("micro")
                            font.weight: Tema.peso("negrita")
                            color: (puente && puente.ticketTendencia > 0) ? Tema.color("verde_texto") : ((puente && puente.ticketTendencia < 0) ? Tema.color("rojo_texto") : Tema.color("texto_secundario"))
                            text: badgeTexto(puente ? puente.ticketVariacion : "", puente ? puente.ticketTendencia : 0)
                        }
                    }
                }
                Text {
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                    text: (puente ? puente.ticketValor : "")
                    font.family: Tema.familia()
                    font.pointSize: Tema.tamano("titulo")
                    font.weight: Tema.peso("negrita")
                    font.features: Tema.caracteristicas()
                    color: Tema.color("texto_valor")
                }
                Sparkline {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 24
                    valores: (puente ? puente.serieTicket : [])
                    colorLinea: Tema.color("serie_violeta")
                }
            }
        }
    }

    Item {
        id: banda
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: filaTarjetas.bottom
        height: Math.max(raiz.altoBanda, raiz.height - filaTarjetas.height)

        Rectangle {
            id: panel
            visible: raiz.tarjetaActiva >= 0
            width: Math.min(Tema.medida("ancho_panel"), Math.max(Tema.medida("ancho_panel_minimo"), banda.width - Tema.espaciado("extra")))
            height: Math.min(Tema.medida("alto_panel"), Math.max(0, banda.height - Tema.espaciado("basico")))
            x: Math.max(Tema.espaciado("basico"), Math.min(raiz.xTarjeta(raiz.tarjetaActiva), banda.width - width - Tema.espaciado("basico")))
            y: Tema.espaciado("micro")
            radius: Tema.radio("panel")
            color: Tema.oscuro() ? Tema.color("gris_boton") : Tema.color("panel_fondo")
            border.width: Tema.medida("grosor_borde")
            border.color: Tema.color("panel_borde")
            layer.enabled: true
            layer.effect: MultiEffect {
                shadowEnabled: true
                shadowColor: Tema.sombra("panel").color
                shadowBlur: Tema.sombra("panel").difuminado
                shadowVerticalOffset: Tema.sombra("panel").desplazamiento
            }

            GridLayout {
                anchors.fill: parent
                anchors.leftMargin: Tema.medida("margen_tarjeta")
                anchors.rightMargin: Tema.medida("margen_tarjeta")
                anchors.topMargin: Tema.espaciado("basico")
                anchors.bottomMargin: Tema.espaciado("basico")
                columns: 2
                columnSpacing: Tema.espaciado("seccion")
                rowSpacing: Tema.espaciado("pico")

                RowLayout {
                    Layout.columnSpan: 2
                    Layout.fillWidth: true
                    spacing: Tema.espaciado("basico")
                    Text {
                        text: raiz.datosTarjeta(raiz.tarjetaActiva).titulo.toUpperCase()
                        font.family: Tema.familia()
                        font.pointSize: Tema.tamano("micro")
                        font.weight: Tema.peso("negrita")
                        color: Tema.color("panel_tenue")
                    }
                    Text {
                        text: raiz.datosTarjeta(raiz.tarjetaActiva).valor
                        font.family: Tema.familia()
                        font.pointSize: Tema.tamano("cuerpo")
                        font.weight: Tema.peso("negrita")
                        font.features: Tema.caracteristicas()
                        color: Tema.color("blanco")
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                    Text {
                        text: raiz.datosTarjeta(raiz.tarjetaActiva).variacion
                        font.family: Tema.familia()
                        font.pointSize: Tema.tamano("compacto")
                        font.weight: Tema.peso("negrita")
                        color: raiz.colorTendencia(raiz.datosTarjeta(raiz.tarjetaActiva).tendencia)
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: "Máximo del día: " + raiz.datosTarjeta(raiz.tarjetaActiva).maximo
                    font.family: Tema.familia()
                    font.pointSize: Tema.tamano("micro")
                    font.features: Tema.caracteristicas()
                    color: Tema.color("panel_detalle")
                    elide: Text.ElideRight
                }
                Text {
                    Layout.fillWidth: true
                    text: "Mínimo del día: " + raiz.datosTarjeta(raiz.tarjetaActiva).minimo
                    font.family: Tema.familia()
                    font.pointSize: Tema.tamano("micro")
                    font.features: Tema.caracteristicas()
                    color: Tema.color("panel_detalle")
                    elide: Text.ElideRight
                }
                Text {
                    Layout.fillWidth: true
                    text: "Días con ventas: " + raiz.datosTarjeta(raiz.tarjetaActiva).dias
                          + " de " + raiz.datosTarjeta(raiz.tarjetaActiva).diasPeriodo
                    font.family: Tema.familia()
                    font.pointSize: Tema.tamano("micro")
                    font.features: Tema.caracteristicas()
                    color: Tema.color("panel_detalle")
                    elide: Text.ElideRight
                }
                Text {
                    Layout.fillWidth: true
                    text: "Promedio por día: " + raiz.datosTarjeta(raiz.tarjetaActiva).promedio
                    font.family: Tema.familia()
                    font.pointSize: Tema.tamano("micro")
                    font.features: Tema.caracteristicas()
                    color: Tema.color("panel_detalle")
                    elide: Text.ElideRight
                }
                Text {
                    Layout.columnSpan: 2
                    Layout.fillWidth: true
                    text: (raiz.datosTarjeta(raiz.tarjetaActiva).periodo !== ""
                           ? raiz.datosTarjeta(raiz.tarjetaActiva).periodo + ". " : "")
                          + "Datos agregados del período, no el detalle de cada día."
                    font.family: Tema.familia()
                    font.pointSize: Tema.tamano("nota")
                    font.italic: true
                    color: Tema.color("panel_tenue")
                    elide: Text.ElideRight
                }
            }
        }
    }
}
