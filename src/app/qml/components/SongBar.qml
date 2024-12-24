import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Shapes
import QtQuick.Effects

import "../colobjs" as ColObjs

Item {
    id: root
    width: parent.width
    height: parent.height
    visible: true
    property bool settingsButton: true

    ColObjs.ColRect {
        id: songbarBackground
        width: parent.width
        height: parent.height
        color: Theme.surfaceContainer
        radius: 10
    }

    Rectangle {
        id: leftGlow
        // This will be a gradient from theme.primary to transparent
        width: parent.width / 10
        height: parent.height
        radius: 10, 0, 0, 10
        anchors.left: root.left
        function addAlpha(alpha, color) {
            let c = color
            // remove the # from the color
            c = c.slice(1)
            // add the alpha value 
            c = "#" + alpha + c
            return c
        }
        
        gradient: Gradient {
            GradientStop { position: 0; color: leftGlow.addAlpha("40", Theme.primary);}
            GradientStop { position: 1; color: leftGlow.addAlpha("00", Theme.primary);}
            orientation: Qt.Horizontal
        }

    }

    Image {
        id: songImage
        source: Interactions.currentSongCover.image
        width: 35
        height: 35
        anchors.left: parent.left
        anchors.leftMargin: 5
        anchors.verticalCenter: parent.verticalCenter

        onSourceChanged: {
            console.log("Song image changed")
        }
    }
}