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

    title: "Clarity"

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

        Image {
            id: logo
            anchors.left: parent.left
            anchors.leftMargin: 5
            anchors.verticalCenter: parent.verticalCenter

            source: AssetsPath + "clarityLogo.png"
            mipmap: true
            fillMode: Image.PreserveAspectFit
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

            onSettingsClick: {
                Backend.setUrl("page/settings")
            }
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

        MouseArea {
            id: clickblocker
            anchors.fill: parent
            z: 0
            onClicked: {
                mouse.accepted = false
            }
            onWheel: {
                // wheel.accepted = false
            }
        }

        Rectangle {
            id: queueBackground
            anchors.fill: parent
            color: Utils.addAlpha("80", Theme.surfaceContainerHighest)
            radius: 15

        }

        Rectangle {
            id: topshade
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 35
            topLeftRadius: 15; topRightRadius: 15
            z: 2

            gradient: Gradient {
                GradientStop {
                    position: 1
                    color: Utils.addAlpha("00", Theme.surfaceContainerLowest)
                }
                GradientStop {
                    position: 0
                    color: Utils.addAlpha("FF", Theme.surfaceContainerLowest)
                }
            }
            state: (!queueList.atYBeginning) ? "visible" : "hidden"
            
            states: [
                State {
                    name: "visible"
                    PropertyChanges {
                        target: topshade
                        visible: true
                        opacity: 1
                    }
                },
                State {
                    name: "hidden"
                    PropertyChanges {
                        target: topshade
                        visible: false
                        opacity: 0
                    }
                }
            ]
            transitions: [
                Transition {
                    from: "visible"
                    to: "hidden"
                    SequentialAnimation {
                        NumberAnimation {
                            properties: "opacity"
                            duration: 200
                        }
                        PropertyAction {
                            target: topshade
                            property: "visible"
                            value: false
                        }
                    }
                },
                Transition {
                    from: "hidden"
                    to: "visible"
                    SequentialAnimation {
                        PropertyAction {
                            target: topshade
                            property: "visible"
                            value: true
                        }
                        NumberAnimation {
                            properties: "opacity"
                            duration: 200
                        }
                    }
                }
            ]
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
            anchors.leftMargin: 5
            anchors.rightMargin: 5
            anchors.topMargin: 5
            anchors.bottomMargin: 5
            z: 1
            spacing: 5
            
            model: Backend.getqueueModel()
            clip: true

            delegate: Base.Song {
                required property var qobject
                required property var index
                required property var id
                width: queueList.width
                height: 80
                song: Interactions.getSong(id)

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        Interactions.setQueueIndex(index)
                    }
                }
            }
        }
    }


    function onClosing(event) {
        event.accepted = false
    }
}