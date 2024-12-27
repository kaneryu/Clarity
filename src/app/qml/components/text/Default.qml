import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform

Text {
    color: Theme.onSurface
    font.pixelSize: 16
    Behavior on color {
        ColorAnimation {
            easing.type: Easing.InOutQuad
            duration: 200
        }
    }
}