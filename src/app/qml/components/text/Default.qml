import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform

Item {
    id: root
    property string text: ""
    property int spacing: 30

    property bool marquee: false
    property bool alwaysMarquee: false
    property bool _marquee: false
    property bool selectable: false

    property alias color: textItem.color
    property alias font: textItem.font
    
    clip: true

    width: textItem.width + spacing
    height: textItem.height

    onTextChanged: recalcShouldDoMarquee()
    onWidthChanged: recalcShouldDoMarquee()
    onHeightChanged: recalcShouldDoMarquee()    

    onMarqueeChanged: recalcShouldDoMarquee()
    onAlwaysMarqueeChanged: recalcShouldDoMarquee()
    
    function recalcShouldDoMarquee() {
        if (!marquee) {
            return
        }
        if (alwaysMarquee) {
            _marquee = true
            return
        }
        if (textMetrics.width > width) {
            _marquee = true
        } else {
            _marquee = false
        }
    }

    on_MarqueeChanged: {
        if (!_marquee) {
            marqueAnim.stop()
            textItem.x = 0
        } else {
            marqueAnim.start()
        }
    }
    
    // Animation for seamless scrolling
    NumberAnimation {
        id: marqueAnim
        target: textItem
        property: "x"
        from: 0
        to: -textMetrics.width - root.spacing
        duration: Math.max(3000, textMetrics.width * 15) // Adjust speed based on text length
        loops: Animation.Infinite
        running: root._marquee
    }
    
    Text {
        id: textItem
        text: parent.text
        color: Theme.onSurface
        font.pixelSize: 16

        // Second copy of the text for continuous scrolling
        Text {
            id: secondText
            x: textMetrics.width + root.spacing // Position right after first text
            text: parent.text
            font: parent.font
            color: parent.color

            // Only visible when marquee is active
            visible: root._marquee

            Behavior on color {
                ColorAnimation {
                    easing.type: Easing.InOutQuad
                    duration: 200
                }
            }
        }

        Behavior on color {
            ColorAnimation {
                easing.type: Easing.InOutQuad
                duration: 200
            }
        }

        TextMetrics {
            id: textMetrics
            text: textItem.text
            font: textItem.font
        }
    }
}