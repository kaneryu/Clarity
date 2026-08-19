import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Effects

Item {
    id: root
    property alias source: sourceImage.source
    property alias fillMode: sourceImage.fillMode
    property alias sourceSize: sourceImage.sourceSize
    property alias status: sourceImage.status
    property alias asynchronous: sourceImage.asynchronous
    property alias cache: sourceImage.cache
    property color color: "transparent"
    property real colorization: 1.0

    Image {
        id: sourceImage
        anchors.fill: parent
        antialiasing: true
        visible: false
        layer.enabled: true
        layer.smooth: true
    }

    MultiEffect {
        anchors.fill: sourceImage
        source: sourceImage
        colorization: root.colorization
        colorizationColor: root.color
    }
}
