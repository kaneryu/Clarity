import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Controls.Basic

import "../components" as Components
import "../components/base" as Base
import "../colobjs" as ColObjs
import "../js/utils.js" as Utils
import "../components/text" as TextVariant

Item {
    id: root
    anchors.fill: parent

    property bool windowTooSmall: (root.height < 300) ? true : false

    Component{
        id: songResultDelegate
        Rectangle {
            id: songResultDelegateRect
            width: 100
            height: 100
            
            color: Theme.surfaceContainer
            radius: 5
            property string title
            property string creator
            property string duration
            property string ytid
            property var thumbnail

            TextVariant.Default {
                id: _title
                text: title
                anchors.top: parent.top
                anchors.left: image.right
                anchors.leftMargin: 10
            }

            Image {
                id: image
                source: "image://SongCover/" + parent.ytid + "/350"
                anchors.top: parent.top
                width: 100
                height: 100
                mipmap: true

                BusyIndicator {
                    id: imageLoader
                    anchors.fill: parent
                    running: true
                    visible: parent.status === Image.Loading
                }
            }

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    console.log("Clicked: ", title)
                    Interactions.searchPress(ytid)
                }
            }
        }
    }
    Item {
        id: albumResultDelegate
    }

    ListView {
        id: searchListViewTest
        anchors.top: parent.top
        anchors.left: parent.left

        width: parent.width
        height: parent.height

        clip: true
        model: Backend.searchModel
        delegate: Item {
            width: searchListViewTest.width
            height: 100
            Rectangle {
                width: parent.width
                height: 100
                color: "transparent"
                Text {
                    text: model.title + " - " + model.creator
                    anchors.top: parent.top
                    anchors.left: parent.left
                }
                Loader {
                    id: delegateLoader
                    anchors.fill: parent
                    sourceComponent: model.type === "song" ? songResultDelegate : albumResultDelegate
                    onLoaded: {
                        item.title = model.title
                        item.creator = model.creator
                        item.duration = model.duration
                        item.ytid = model.ytid
                        item.thumbnail = model.thumbnail
                        console.log("Loaded: ", item.title)
                    }
                }
            }
        }
    }
}