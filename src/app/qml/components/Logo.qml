import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.VectorImage

import "../colobjs" as ColObjs

Item {
    id: logo
    width: 44
    height: 44

    Rectangle {
        id: logoBackground
        width: parent.width
        height: parent.height
        color: Theme.tertiaryContainer
        radius: 10 * parent.width / 44
        z: -1
    }

    ColObjs.ColImg {
        id: logoNote
        source: "../../assets/icons/logo/note.svg"
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: 9 * parent.width / 44

        width: parent.width / 1.83333333333
        height: parent.height / 1.83333333333
        fillMode: Image.PreserveAspectFit

        color: Theme.onTertiaryFixed

        z: 1
    }

    ColObjs.ColImg {
        id: logoFlourish
        source: "../../assets/icons/logo/flourish.svg"
        width: parent.width / 3.66666666667
        height: parent.height / 3.66666666667

        x: logoNote.x + logoNote.width - 8
        y: logoNote.y - 2.5

        // anchors.top: logoNote.top
        // anchors.right: logoNote.right
        // anchors.rightMargin: -5
        // anchors.topMargin: -7
        z: 0


        fillMode: Image.PreserveAspectFit
        color: Theme.tertiaryFixed
    }
}
