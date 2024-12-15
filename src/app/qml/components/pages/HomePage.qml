import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform

import ".." as Components
import "../../colobjs" as ColObjs


Item {
    id: root
    // this element is assumed to be inserted inside of the main.qml file's main StackView
    // therefore, the styling may look wrong when viewed in isolation

    anchors.leftMargin: 5
    anchors.rightMargin: 5
    anchors.topMargin: 5
    anchors.bottomMargin: 5


    ColObjs.ColRect {
        id: background
        radius: 20
        anchors.fill: parent
        color: Theme.primary
    }
}