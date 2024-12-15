import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Effects

Item {
    id: root
    property string source: ""
    property real radius: 100

    property alias image: sourceItem

    onRadiusChanged: {
        sourceItem.source = Backend.roundImage(root.source, root.radius)
    }

    function onSourceChanged() {
        if (sourceItem != "") {
            sourceItem.source = Backend.roundImage(root.source, root.radius)
        }
    }

    Image {
        id: sourceItem
        anchors.left: parent.left
        source: Backend.roundImage(root.source, root.radius)
        anchors.fill: parent
    }
}