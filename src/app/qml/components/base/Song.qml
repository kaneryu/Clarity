import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Effects

import "../../colobjs" as ColObjs
import "../text" as TextVariant
import "../../components" as Components
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

    property color textColor: Theme.onSurface

    // enum SongType { Local, Remote }
    // property int songSourceType: SongType.Local

    // enum SongStatus { Playing, Paused, Stopped }
    // property int songPlayStatus: SongStatus.Stopped

    // enum LibraryStatus { NotInLibrary, InLibrary }
    // property int songLibraryStatus: LibraryStatus.NotInLibrary

    // enum LikeStatus { NotLiked, Liked }
    // property int songLikeStatus: LikeStatus.NotLiked

    // property bool songIsSelected: false

    /*
    Image | Song title
    Image | Song artist | Song length
    Image | Download status | libary status | like status
    */

    width: 330
    height: 80
    

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
            visible: songImage.status === Image.Loading
        }
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

            Rectangle {
                id: debugt
                color: "green"
                anchors.fill: songTitleText
                z: -1
            }
        }

        TextVariant.Default {
            id: artistLengthText
            text: root.songArtist + " • " + root.songLength
            color: root.textColor
            width: parent.width
            marquee: true

            Rectangle {
                id: debuga
                color: "green"
                anchors.fill: artistLengthText
                z: -1
            }
        }
        
    }

    Rectangle {
        id: debugr
        color: "red"
        anchors.fill: parent
        z: -2
    }
}