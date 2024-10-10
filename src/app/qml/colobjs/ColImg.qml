import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform

ColorImage {
    Behavior on color {
        ColorAnimation {
            easing.type: Easing.InOutQuad
            duration: 200
        }
    }
}