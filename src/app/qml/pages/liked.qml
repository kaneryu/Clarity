import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Controls.Basic

import "../components" as Components
import "../components/base" as Base
import "../colobjs" as ColObjs
import "../components/text" as TextVariant

Item {
    id: root
    anchors.fill: parent
    
    property bool windowTooSmall: (root.height < 300) ? true : false
    

    GridView {
        id: gridView
        anchors.top: parent.top
        anchors.topMargin: 16
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 16
        cellWidth: 330
        cellHeight: 80
        clip: true
        
        model: Backend.likedSongsModel

        delegate: Base.Song {
            required property var object
            required property var id

            radius: 230

            width: gridView.cellWidth - 5
            height: gridView.cellHeight - 5

            song: object
        }
    }
}