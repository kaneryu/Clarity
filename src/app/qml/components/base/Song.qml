import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Effects

import "../../colobjs" as ColObjs
import "../text" as TextVariant
import "../../components" as Components
import "../../components/particles" as Particles

import "../../js/utils.js" as Utils

Item {
    id: root

    property string id
    property QtObject song: Interactions.currentSong

    property string songTitle: song.title
    property string songArtist: song.artist
    property string songLength: Utils.secondsToHMS(song.duration)

    property real radius: 350

    /*
    NOT_DOWNLOADED = 0
    DOWNLOADING = 1
    DOWNLOADED = 2
    */
    property int songDownloadStatus: song.downloadStatus
    property int songPlayingStatus: song.playingStatus
    property color textColor: Theme.onSurface

    // property bool songIsSelected: false

    /*
    Image | Song title
    Image | Song artist | Song length
    Image | Download status | library status | like status
    */

    width: 330
    height: 80
    
    Connections {
        target: song
        function onInfoChanged(newStatus) {
            songImage.source = ""
            songImage.source = "image://SongCover/" + song.id + "/" + root.radius // Force refresh
        }
    }

    Image {
        id: songImage
        source: "image://SongCover/" + song.id + "/" + root.radius
        mipmap: true
        width: 80
        height: 80
        
        BusyIndicator {
            id: imageLoader
            anchors.fill: parent
            running: true
            visible: (songImage.status === Image.Loading) | (song.dataStatus <= 1) // Loading or not started loading yet
        }

        Behavior on opacity {
            NumberAnimation { duration: 300;}
        }
        z: 2
    }

    Particles.SideGlow {
        anchors.fill: parent
        running: root.songPlayingStatus === 0
        opacity: 0.5
    }

    ColumnLayout {
        id: songInfo
        anchors.left: songImage.right
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        anchors.leftMargin: 5

        Layout.alignment: Qt.AlignTop | Qt.AlignLeft

        TextVariant.Default {
            id: songTitleText
            text: root.songTitle
            width: parent.width
            color: root.textColor
            marquee: true

            // Rectangle {
            //     id: debugt
            //     color: "green"
            //     anchors.fill: songTitleText
            //     z: -1
            // }
        }

        TextVariant.Default {
            id: artistLengthText
            text: root.songArtist + " • " + root.songLength + " • " + (root.songDownloadStatus === 0 ? "Not downloaded" : root.songDownloadStatus === 1 ? "Downloading" : "Downloaded")
            color: root.textColor
            width: parent.width
            marquee: true

            // Rectangle {
            //     id: debuga
            //     color: "green"
            //     anchors.fill: artistLengthText
            //     z: -1
            // }
        }
        
    }

    // Rectangle {
    //     id: background
    //     color: theme.onSurface
    //     anchors.fill: parent
    //     z: -2

    //     visible: root.songPlayingStatus === 0
    // }

    // Rectangle {
    //     id: debugr
    //     color: "red"
    //     anchors.fill: parent
    //     z: -2
    // }
}