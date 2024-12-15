import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Effects

// ColorImage {
//     Behavior on color {
//         ColorAnimation {
//             easing.type: Easing.InOutQuad
//             duration: 200
//         }
//     }
// }

Image {
    id: root
    property alias color: mfe.colorizationColor
    property alias colorization: mfe.colorization
    antialiasing: true
    MultiEffect {
        id: mfe
        source: root
        anchors.fill: root
        colorization: 1.0
    }  
}