import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Shapes
import QtQuick.Effects

import "../colobjs" as ColObjs

Item {
    id: searchbar
    width: parent.width
    height: 40
    visible: true

    ColObjs.ColRect {
        id: searchbarBackground
        width: parent.width
        height: parent.height
        color: Theme.primaryContainer
        radius: 31
    }

    Item {
        id: searchbarIcon
        width: 24
        height: 24
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: 10

        Image {
            id: searchIcon
            source: "../../assets/icons/searchbar/search.svg"
            anchors.fill: parent
            fillMode: Image.PreserveAspectFit
        }

        MultiEffect {
            anchors.fill: searchIcon
            source: searchIcon
            colorizationColor: Theme.onPrimaryContainer

            Behavior on colorizationColor {
                ColorAnimation {
                    easing.type: Easing.InOutQuad
                    duration: 200
                }
            }
        }


    }

    TextField {
        property string searchField: ""
        property list<string> placeholders: [
            "Search for your favorite song",
            "Search for that one album",
            "Search for the best podcast",
            "Search for a new artist",
            "Search for a mood",
            "Search for your friend's playlist",
            "Search for anything"
        ]
        property int placeholderIndex: 0

        id: searchbarField
        // height: parent.height - 20
        anchors.left: searchbarIcon.left
        anchors.right: parent.right
        anchors.rightMargin: 10
        anchors.leftMargin: 24
        anchors.verticalCenter: parent.verticalCenter
        property string pholder: "Search for your favorite song"
        placeholderText: "Search for your favorite song"
        color: Theme.onPrimaryContainer
        font.pixelSize: 15
        focus: true
        background: Rectangle {
            color: "transparent"
        }


        Behavior on pholder {
            SequentialAnimation {
                NumberAnimation {
                    target: searchbarField
                    property: "opacity"
                    from: 1
                    to: 0
                    duration: 100
                }
                ScriptAction {
                    script: {
                        searchbarField.placeholderText = searchbarField.placeholders[searchbarField.placeholderIndex]
                    }
                }
                NumberAnimation {
                    target: searchbarField
                    property: "opacity"
                    from: 0
                    to: 1
                    duration: 100
                }
            }
        }

        Timer {
            id: placeholderTimer
            interval: 10000
            running: true
            repeat: true
            onTriggered: {
                searchbarField.placeholderIndex++
                if (searchbarField.placeholderIndex >= searchbarField.placeholders.length) {
                    searchbarField.placeholderIndex = 0
                }
                searchbarField.pholder = searchbarField.placeholders[searchbarField.placeholderIndex]
            }
        }
    }
}