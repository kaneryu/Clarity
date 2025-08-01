import QtWebView
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Effects

import "../colobjs" as ColObjs
import "text" as TextVariant



Item {
    id: root
    
    implicitHeight: parent.height
    implicitWidth: height



    property bool checkState: false
    property alias checked: root.checkState
    signal clicked()

    Rectangle {
        id: background
        anchors.fill: parent
        color: checked ? Theme.primary : Theme.secondary
        radius: 4
    }

    MouseArea {
        anchors.fill: parent
        onClicked: {
            root.checkState = !root.checkState;
            root.clicked();
        }
    }
}