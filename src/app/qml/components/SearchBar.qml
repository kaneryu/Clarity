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
    height: 35
    visible: true
    property bool settingsButton: true

    ColObjs.ColRect {
        id: searchbarBackground
        width: parent.width
        height: parent.height
        color: Theme.primaryContainer
        radius: 35
    }

    Item {
        id: searchbarIcon
        width: 20
        height: 20
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: 10

        ColObjs.ColImg {
            id: searchIcon
            source: "../../assets/icons/searchbar/search.svg"
            anchors.fill: parent
            fillMode: Image.PreserveAspectFit
            color: Theme.onPrimaryContainer
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
                if (searchbarField.text.length == 0) {
                    searchbarField.placeholderIndex++
                    if (searchbarField.placeholderIndex >= searchbarField.placeholders.length) {
                        searchbarField.placeholderIndex = 0
                    }
                    searchbarField.pholder = searchbarField.placeholders[searchbarField.placeholderIndex]
                }
            }
        }
    }

    Rectangle {
        id: settingsButton
        height: 24
        width: 24
        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        anchors.rightMargin: 10
        color: "transparent"

        ColObjs.ColImg {
            id: settingsIcon
            source: "../../assets/icons/searchbar/settings.svg"

            fillMode: Image.PreserveAspectFit
            anchors.fill: parent

            color: Theme.onPrimaryContainer
            signal clicked

            opacity: (searchbarField.text.length > 15) ? 0 : 1
            Behavior on opacity {
                NumberAnimation {
                    duration: 500 // Duration of the animation in milliseconds
                    easing.type: Easing.InOutQuad // Easing type for the animation
                }
            }
        }
    }
}