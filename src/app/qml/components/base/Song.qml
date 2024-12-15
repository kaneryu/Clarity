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
    

    Image {
        id: songImage
        property int radius: 60
        source: Backend.convertToCover(imageUrl, radius, width)
        width: 80
        height: 80
    }
    
    Timer {
        id: coverChangeTimer
        interval: 5000
        running: true
        repeat: false
        onTriggered: {
            console.log("changing cover")
            root.imageUrl = "https://images.unsplash.com/photo-1721332155637-8b339526cf4c?q=80&w=1935&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDF8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
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