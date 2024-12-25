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

        mipmap: true
        width: 30
        height: width

        anchors.left: parent.left
        anchors.leftMargin: leftGlow.width / 10
        anchors.verticalCenter: parent.verticalCenter

        onSourceChanged: {
            console.log("Song image changed")
        }
    }

    Text {
        id: songTitle
        text: Interactions.currentSongTitle + " - " + Interactions.currentSongChannel
        font.pixelSize: 20
        color: Theme.onSurface
        anchors.left: songImage.right
        anchors.leftMargin: 10
        anchors.verticalCenter: parent.verticalCenter
    }

    // ProgressBar {
    //     id: songProgress
    //     width: parent.width / 2
    //     height: 5
    //     anchors.right: parent.right
    //     anchors.rightMargin: 10

    //     anchors.verticalCenter: parent.verticalCenter

    //     property int timerRuns: 0

    //     value: Interactions.currentSongTime
    //     to: Interactions.currentSongDuration
    //     visible: true

    //     Timer {
    //         id: progressTimer
    //         interval: 1000
    //         running: true
    //         repeat: true
    //         onTriggered: {
    //             songProgress.timerRuns += 1

    //             if (songProgress.timerRuns % 3 == 0) { // Every three seconds, confirm we have the right time
    //                 songProgress.value = Interactions.currentSongTime
    //                 return
    //             }

    //             songProgress.value += 1 // Increment the progress bar by one every second
    //         }
    //     }
    // }
}