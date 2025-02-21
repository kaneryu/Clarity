import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform

Text {
    property bool marquee: false
    property bool selectable: false
    property string text: "some text"
    property string spacing: "      "
    property string combined: text + spacing
    property string display: combined.substring(step) + combined.substring(0, step)
    property int step: 0

    Timer {
      interval: 200
      running: true
      repeat: true
      onTriggered: parent.step = (parent.step + 1) % parent.combined.length
    }

    color: Theme.onSurface
    font.pixelSize: 16
    Behavior on color {
        ColorAnimation {
            easing.type: Easing.InOutQuad
            duration: 200
        }
    }

    TextMetrics {
        id: textMetrics
        text: text
        font: font
    }

}