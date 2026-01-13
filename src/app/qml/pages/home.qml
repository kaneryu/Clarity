import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Controls.Basic

import "../components" as Components
import "../components/base" as Base
import "../colobjs" as ColObjs
import "../components/text" as TextVariant

Item {
    id: root
    anchors.fill: parent
    
    property bool windowTooSmall: (root.height < 300) ? true : false
    
    // Components.Button {
    //     anchors.left: parent.left
    //     anchors.leftMargin: 52
    //     id: button
    //     text: "Go to auto-generated playlists page"
    //     anchors.top: parent.bottom
    //     width: 411
    //     enabled: true
    //     height: 39
    //     onClicked: {
    //         Backend.queueCall("next")
    //     }
    // }

    // Text {
    //     id: title
    //     text: "\uF673"
    //     font.family: "Material Symbols Rounded"
    //     font.variableAxes: {
    //         "fill": 0,
    //         "grad": 200,
    //         "opsz": 48,
    //         "wght": 700
    //     }
    //     font.pixelSize: 48
    // }

    // Base.Song {
    //     id: r76AWibyDDQ
    // }
    
    TextVariant.Default {
        id: _title
        text: "fff"
    }
    TextVariant.Default {
        id: _subtitle
        text: Interactions.currentSong.playbackReady ? "Playback is ready" : "Playback is not ready"
        anchors.top: _title.bottom
    }

    GridView {
        id: gridView
        anchors.top: _subtitle.bottom
        anchors.topMargin: 16
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 16
        cellWidth: 330
        cellHeight: 80
        
        model: Backend.downloadedSongsModel

        delegate: Base.Song {
            required property var object
            required property var id

            radius: 230

            width: gridView.cellWidth - 5
            height: gridView.cellHeight - 5

            song: object

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    Interactions.songPress(id)
                }
            }
        }


    }
}