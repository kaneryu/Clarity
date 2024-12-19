import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform

import QtQuick.Controls.Basic


import "components" as Components
import "components/pages" as Pages
import "components/base" as Base
import "colobjs" as ColObjs

ApplicationWindow {
    id: root
    visible: true
    width: 840
    height: 480
    minimumWidth: 840 / 2
    minimumHeight: 480 / 2

    title: "InnerTuneDesktop"

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

        radius: 10

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
    Item {
        id: content
        anchors.top: header.bottom
        anchors.bottom: footer.top
        anchors.left: parent.left
        anchors.right: parent.right

        property bool windowTooSmall: (root.height < 300) ? true : false

        anchors.topMargin: windowTooSmall ? 0 : 5
        anchors.leftMargin: windowTooSmall ? 0 : 5
        anchors.rightMargin: windowTooSmall ? 0 : 5
        anchors.bottomMargin: windowTooSmall ? 0 : 5

        Behavior on anchors.topMargin {
            NumberAnimation {
                duration: 200
            }
        }

        Behavior on anchors.leftMargin {
            NumberAnimation {
                duration: 200
            }
        }

        Behavior on anchors.rightMargin {
            NumberAnimation {
                duration: 200
            }
        }

        Behavior on anchors.bottomMargin {
            NumberAnimation {
                duration: 200
            }
        }

        // WebEngineView {
        //     id: webview
        //     anchors.fill: parent
        //     // get full path of the file from backend
            
        //     url: Backend.getPage("pages/home")

        //     backgroundColor: "#000"

        //     onJavaScriptConsoleMessage: {
        //         console.log("JS: " + message)
        //     }
        //     webChannel: WebChannel {
        //         id: webChannel
        //     }

        //     Component.onCompleted: {
        //         webChannel.registerObject("backend", Backend)
        //         webChannel.registerObject("theme", Theme)
        //     }

            
        // }
        ColObjs.ColRect {
            id: contentBackground
            anchors.fill: parent
            radius: content.windowTooSmall ? 0 : 10
            color: Theme.surfaceContainerLow
        }
        
        // Base.Song {
        //     id: song
        // }

        Components.Button {
            anchors.left: parent.left
            anchors.leftMargin: 52
            id: button
            text: "Go to auto-generated playlists page"
            anchors.top: parent.bottom
            width: 411
            enabled: true
            height: 39
            onClicked: {
                Backend.queueCall("next")
            }
        }

        StackLayout {
            id: stackLayout
            anchors.fill: parent
            currentIndex: 1

            Pages.HomePage {
                id: homePage
                visible: true
            }
        }
        ListView {
            id: queueListView
            anchors.fill: parent
            model: Backend.queueModel

            Component.onCompleted: {
                console.log("Queue model: ", model)
                console.log("itemAt(0): ", model[1])
            }

            delegate: Item {
                width: parent.width
                height: 50
                Text {
                    text: song
                    anchors.centerIn: parent
                }
                Component.onCompleted: {
                    console.log("Model data: ", song)
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        Backend.queueCall("setPointer", index)
                    }
                }
            }
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
        opacity: windowTooSmall ? 0 : 1

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


        radius: 10

        color: Theme.surfaceContainerLow
    }

    function onClosing(event) {
        event.accepted = false
    }
}