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
}