import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Effects

Item {
    id: root
    property string source: ""
    property real radius: 0

    property alias image: sourceItem
    property alias mask: maskRect
    layer.samples: 8

    Image {
        id: sourceItem
        anchors.left: parent.left
        source: imageUrl
        anchors.fill: parent
        visible: false
        layer.smooth: true
    }

    MultiEffect {
        source: sourceItem
        anchors.fill: sourceItem
        maskEnabled: true
        layer.smooth: true
        maskSource: mask
    }

    Item {
        id: mask
        width: sourceItem.width
        height: sourceItem.height
        layer.enabled: true
        layer.samples: 8
        layer.smooth: true
        visible: false

        antialiasing: true
        Rectangle {
            id: maskRect
            layer.smooth: true
            antialiasing: true
            width: sourceItem.width
            height: sourceItem.height
            radius: root.radius
            color: "black"
        }
    }
}