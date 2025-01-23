import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Effects

import QtQuick.Controls.Basic


import "components" as Components
import "components/base" as Base
import "colobjs" as ColObjs
import "js/utils.js" as Utils
import "components/text" as TextVariant

ApplicationWindow {
    id: root
    visible: true
    width: 840
    height: 480
    minimumWidth: 840 / 2
    minimumHeight: 480 / 2

    // title: "InnerTuneDesktop"

    Connections {
        target: Backend
        function onLoadComplete() {
            console.log("Loaded")
        }
    }

    Connections {
        target: Theme
    }

    background: ColObjs.ColRect {
        id: background
        color: Theme.background
    }

    
    ColObjs.ColRect {
        id: header

        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right

        anchors.topMargin: 5
        anchors.leftMargin: 5
        anchors.rightMargin: 5

        property bool windowTooSmall: (root.height < 300) ? true : false
        height: windowTooSmall ? 0 : 44
        opacity: windowTooSmall ? 0 : 1

        radius: 5

        color: Theme.surfaceContainerLow

        Components.Logo {
            id: logo
            anchors.left: parent.left
            anchors.leftMargin: 5
            anchors.verticalCenter: parent.verticalCenter
            width: 35
            height: 35
        }

        Components.SearchBar {
            id: searchbar
            anchors.left: logo.right
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: 10
            anchors.rightMargin: 5
            visible: true
        }

        
        Behavior on opacity {
            NumberAnimation {
                duration: 200
            }
        }

        Behavior on height {
            NumberAnimation {
                duration: 200
            }
        }
    }
    // Button {
    //     id: reloadButton
    //     text: "Reload"
    //     anchors.top: parent.top
    //     anchors.right: parent.right
    //     onClicked: webview.reload()
    //     z: 999
    // }
    ColObjs.ColRect {
        id: content
        anchors.top: header.bottom
        anchors.bottom: footer.top
        anchors.left: parent.left
        anchors.right: parent.right

        color: Theme.surfaceContainerLow
        radius: root.windowTooSmall ? 0 : 10

        property bool windowTooSmall: (root.height < 300) ? true : false

        anchors.topMargin: windowTooSmall ? 0 : 5
        anchors.leftMargin: windowTooSmall ? 0 : 5
        anchors.rightMargin: windowTooSmall ? 0 : 5
        anchors.bottomMargin: windowTooSmall ? 0 : 5

        Loader {
            id: pageLoader
            anchors.fill: parent
            source: Backend.getCurrentPageFilePath
        }
    }

    ColObjs.ColRect {
        id: footer

        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right

        anchors.bottomMargin: 5
        anchors.leftMargin: 5
        anchors.rightMargin: 5

        property bool windowTooSmall: (root.height < 300) ? true : false

        height: windowTooSmall ? 0 : 44
        visible: windowTooSmall ? false : true

        radius: 5
        color: Theme.surfaceContainerLow

        Components.SongBar {
            id: songbar
            anchors.fill: parent
            visible: parent.visible
            
            anchors.margins: 3

        }

        Behavior on opacity {
            NumberAnimation {
                duration: 200
            }
        }

        Behavior on height {
            NumberAnimation {
                duration: 200
            }
        }
    }

    Item {
        id: queueView
        // A floating view that shows the current queue
        property int visibleYpos: parent.height - (height + footer.height + 5)

        anchors.right: parent.right
        y: visibleYpos
        height: parent.height / 2
        width: parent.width / 3
        z: 999

        // MultiEffect {
        //     anchors.fill: queueView
        //     source: effectSource
        //     blurEnabled: true
        //     blur: 1
        //     blurMax: 32
        //     blurMultiplier: 1

        //     // shadowEnabled: true
        //     // shadowScale: 0
        //     // shadowHorizontalOffset: 0
        //     // shadowVerticalOffset: 5
        //     // shadowBlur: 0.7
        //     // shadowColor: "#71000000"
        // }
        // ShaderEffectSource {
        //     id: effectSource

        //     sourceItem: content
        //     anchors.fill: parent
        //     x: parent.x
        //     y: parent.y
        //     sourceRect: Qt.rect(x,y, width, height)
        // }

        Rectangle {
            id: queueBackground
            anchors.fill: parent
            color: Utils.addAlpha("80", Theme.surfaceContainerHighest)
            radius: 10

        }

        state: (Backend.queueVisible == true) ? "visible" : "hidden"
        visible: true

        Behavior on y {
            NumberAnimation {
                duration: 200
            }
        }

        states: [
            State {
                name: "hidden"
                PropertyChanges{
                    target: queueView
                    y: root.width + width
                }
                PropertyChanges {
                    target: queueView
                    visible: false
                }
            },
            State {
                name: "visible"
                PropertyChanges {
                    target: queueView
                    y: queueView.visibleYpos
                }
                PropertyChanges {
                    target: queueView
                    visible: true
                }
            }
        ]

        ListView {
            id: queueList
            anchors.fill: parent
            model: Backend.getqueueModel()
            clip: true

            delegate: Rectangle {
                id: delegateItem
                width: parent.width
                height: 50
                color: "transparent"

                TextVariant.Small {
                    id: songTitle
                    text: model.title + " - " + model.artist
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        Interactions.setQueueIndex(model.index)
                    }
                }
            }
        }
    }


    function onClosing(event) {
        event.accepted = false
    }
}