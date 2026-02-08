import QtWebView
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Effects

import "../colobjs" as ColObjs
import "text" as TextVariant
import "." as Components


Components.ReactiveItem {
    id: root
    
    implicitHeight: parent.height
    implicitWidth: height

    signal clicked()


    property bool checkState: false
    colortype: (root.checkState) ? "primary" : "secondary"
    property alias checked: root.checkState
    property string uncheckedText: "Unchecked"
    property string checkedText: "Checked"
    property string text: "_unused$disabled$checkbox_"

    property var internalClickedFunction: function() {
        root.checkState = !root.checkState;
        root.clicked();
    }

    property string icon: ""
    property bool isIcon: (root.icon !== "")

    TextVariant.Default {
        id: label

        visible: !root.isIcon

        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: height + 8
        text: (root.text === "_unused$disabled$checkbox_") ? (root.checkState ? root.checkedText : root.uncheckedText) : root.text
        font.pixelSize: height * 0.5
        color: root.textcolor
    }

    ColObjs.ColImg {
        id: checkboxIcon
        source: root.icon

        anchors.centerIn: parent
        visible: root.isIcon

        width: parent.width
        height: parent.height
        sourceSize: Qt.size(Math.max(width, height) * 1.2, Math.max(width, height) * 1.2)

        fillMode: Image.PreserveAspectFit

        color: root.textcolor
    }

    // onCheckStateChanged: {
    //     if (root.checkState) {
    //         root.colortype = "primary"
    //     } else {
    //         root.colortype = "secondary"
    //     }
    // }

    onInternalClicked: {
        internalClickedFunction();
    }
}