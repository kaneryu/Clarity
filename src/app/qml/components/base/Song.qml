import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Effects

import "../../colobjs" as ColObjs
import "../../components" as Components

Item {
    id: root

    property QtObject song: null

    /* debug */
    property string songTitle: "testing"
    property string songArtist: "the tester"
    property string songLength: "2:04"
    property string imageUrl: "https://img.youtube.com/vi/tI7e34KfwB4/maxresdefault.jpg"
    enum DownloadStatus { NotDownloaded, Downloading, Downloaded }
    property int songDownloadStatus: DownloadStatus.NotDownloaded

    enum SongType { Local, Remote }
    property int songSourceType: SongType.Local

    enum SongStatus { Playing, Paused, Stopped }
    property int songPlayStatus: SongStatus.Stopped

    enum LibraryStatus { NotInLibrary, InLibrary }
    property int songLibraryStatus: LibraryStatus.NotInLibrary

    enum LikeStatus { NotLiked, Liked }
    property int songLikeStatus: LikeStatus.NotLiked

    property bool songIsSelected: false

    /*
    Image | Song title
    Image | Song artist | Song length
    Image | Download status | libary status | like status
    */

    width: 330
    height: 80
    Components.RoundedImage {
        id: songImage
        source: imageUrl
        radius: 20
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
            text: songTitle

            color: Theme.onSurface
        }

        RowLayout {
            id: songArtistLength
            spacing: 0
            ColObjs.ColText {
                id: songArtistText
                text: songArtist
                color: Theme.onSurface
            }

            ColObjs.ColText {
                id: spacer
                text: " • "
                color: Theme.onSurface
            }

            ColObjs.ColText {
                id: songLengthText
                text: songLength
                color: Theme.onSurface
            }
        }
    }
}