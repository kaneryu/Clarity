import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Controls.Basic

import "../components" as Components
import "../components/base" as Base
import "../colobjs" as ColObjs
import "../components/text" as TextVariant
import "../js/utils.js" as Utils

Item {
    id: root
    anchors.fill: parent
    
    property bool windowTooSmall: (root.height < 300) ? true : false
    
    property var query: Backend.getCurrentQuery()
    property string albumId: query["id"] ? query["id"][0] : ""
    property QtObject album: Interactions.getAlbum(albumId)
    


    Item {
        id: albumOptionsBar
        height: 40
        anchors.top: parent.top
        width: parent.width

        RowLayout {
            anchors.fill: parent

            Layout.alignment: Qt.AlignLeft

            TextVariant.Default {
                id: _title
                text: '"' + root.album.title + '" ' + Utils.albumTypeCorrector(root.album.albumType) + " By " + root.album.artist + " • " + Utils.secondsToHMS(root.album.duration)
            }

            Components.Button {
                text: "Add all to queue"
                Layout.preferredWidth: 150
                Layout.preferredHeight: parent.height

                onClicked: {
                    Interactions.addAlbumToQueue(root.album)
                }

            }
            Components.Button {
                text: "Download all"
                Layout.preferredWidth: 150
                Layout.preferredHeight: parent.height

                onClicked: {
                    root.album.download()
                }
            }
        }
    }

    ScrollView {
        
        id: scrollView
        anchors.top: albumOptionsBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.topMargin: 10

        clip: true

        // Flickable properties

        property real contentY: songView.contentY

        ScrollBar.vertical.interactive: true

        ListView {
            id: songView

            // Rectangle {
            //     anchors.fill: parent
            //     color: Theme.surfaceVariant
            //     radius: 10
            // }

            Component.onCompleted: {
                console.log("query:", query, "albumId:", albumId)
                if (album) {
                    console.log("Album loaded:", album.title, "album id:", root.albumId, "album:", album, "albumId:", album.id)
                } else {
                    console.log("Album not loaded")
                }
                console.log("album.getSongsProxyModel():", model)
                console.log("item count:", model ? model.count : 0)
            }

            model: album.getSongsProxyModel()
            delegate: Base.Song {
                song: model.object

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        Interactions.songPress(model.id)
                    }
                }
            }

        }
    }

}