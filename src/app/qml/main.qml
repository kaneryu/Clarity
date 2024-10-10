import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform

import "components" as Components
import "colobjs" as ColObjs

ApplicationWindow {
    id: root
    visible: true
    minimumWidth: 840
    minimumHeight: 480
    visibility: "FullScreen"
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
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right

        anchors.topMargin: 7
        anchors.leftMargin: 7
        anchors.rightMargin: 7
        height: 44

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
    }

    function onClosing(event) {
        event.accepted = false
    }
}