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
        source: "image://SongCover/" + song.id + "/350"
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
        }

        RowLayout {
            id: songArtistLength
            spacing: 0
            TextVariant.Default {
                id: songArtistText
                text: root.songArtist
                color: root.textColor
                marquee: true
            }

            TextVariant.Default {
                id: spacer
                text: " • "
                color: root.textColor
            }

            TextVariant.Default {
                id: songLengthText
                text: root.songLength
                color: root.textColor
            }
        }
    }
}