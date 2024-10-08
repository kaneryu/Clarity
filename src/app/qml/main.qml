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

    Components.SearchBar {
        id: searchbar
        width: parent.width
        visible: true
    }

    function onClosing(event) {
        event.accepted = false
    }
}