import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform

Item {
    property string text: ""
    property string spacing: "      "
    property string combined: text + spacing
    property string display: combined.substring(step) + combined.substring(0, step)
    property int step: 0

    property bool marquee: false
    property bool alwaysMarquee: false
    property bool _marquee: false
    property bool selectable: false
    property alias color: textItem.color
    property alias font: textItem.font
    
    width: textItem.width
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

    Timer {
        interval: 200
        running: parent._marquee 
        repeat: true
        onTriggered: parent.step = (parent.step + 1) % parent.combined.length
    }

    Text {
        id: textItem
        text: (parent._marquee) ? parent.display : parent.text
        color: Theme.onSurface
        font.pixelSize: 10
        
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