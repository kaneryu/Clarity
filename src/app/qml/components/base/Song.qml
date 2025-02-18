import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Effects

import "../../colobjs" as ColObjs
import "../../components" as Components
import "../../js/utils.js" as Utils

Item {
    id: root

    property string id
    property QtObject song: Interactions.currentSong

    /* debug */
    property string songTitle: song.title
    property string songArtist: song.artist
    property string songLength: Utils.secondsToHMS(song.duration)
    property QtObject cover: Interactions.getSongCover(song)

    /*
    NOT_DOWNLOADED = 0
    DOWNLOADING = 1
    DOWNLOADED = 2
    */
    property int songDownloadStatus: song.downloadStatus

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
        source: cover.image
        width: 80
        height: 80
    }

    ColumnLayout {
        id: songInfo
        anchors.left: songImage.right
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        anchors.leftMargin: 5

        Layout.alignment: Qt.AlignTop | Qt.AlignLeft

        ColObjs.ColText {
            id: songTitleText
            text: root.songTitle

            color: Theme.onSurface
        }

        RowLayout {
            id: songArtistLength
            spacing: 0
            ColObjs.ColText {
                id: songArtistText
                text: root.songArtist
                color: Theme.onSurface
            }

            ColObjs.ColText {
                id: spacer
                text: " • "
                color: Theme.onSurface
            }

            ColObjs.ColText {
                id: songLengthText
                text: root.songLength
                color: Theme.onSurface
            }
        }
    }
}