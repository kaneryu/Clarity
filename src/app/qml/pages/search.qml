import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Controls.Basic

import "../components" as Components
import "../components/base" as Base
import "../colobjs" as ColObjs


Item {
    id: root
    anchors.fill: parent

    property bool windowTooSmall: (root.height < 300) ? true : false

    ColObjs.ColRect {
        id: contentBackground
        anchors.fill: parent
        radius: root.windowTooSmall ? 0 : 10
        color: Theme.surfaceContainerLow
    }

    Component{
        id: songResultDelegate
        Rectangle {
            id: songResultDelegateRect
            width: 100
            height: 100
            
            color: "white"
            property string title
            property string creator
            property string duration
            property string ytid
            property var thumbnail

            Text {
                id: songResultDelegateTitle
                text: title
                anchors.top: parent.top
                anchors.left: parent.left
            }

            Image {
                id: songResultDelegateImage
                source: thumbnail.image
                anchors.top: parent.top
                width: 100
                height: 100

                onSourceChanged: {
                    console.log("sourceChanged")
                }
            }
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    console.log("Clicked: ", title)
                    Backend.queueFunctions.addEnd(ytid)
                }
            }

            Component.onCompleted: {
                console.log("Thumbnail: ", thumbnail)
            }
        }
    }
    Item {
        id: albumResultDelegate
    }

    ListView {
        id: searchListViewTest
        anchors.fill: parent
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