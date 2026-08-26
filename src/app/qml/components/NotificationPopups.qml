import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Controls.Basic

import "." as Components
import "./base" as Base
import "../colobjs" as ColObjs
import "./text" as TextVariant

pragma ComponentBehavior: Bound

Item {
    id: root

    ListView {
        id: listView
        anchors.fill: parent

        // Toasts are not a scrollable surface. Without this the ListView is a
        // Flickable covering the whole column and swallows drags aimed at the
        // window underneath it.
        interactive: false

        model: Backend.notifyingLogHistoryModel

        delegate: Item {
            id: delegateRoot

            // Snapshot the model row at creation. During a remove transition the
            // delegate outlives its row, and context-property bindings would
            // re-evaluate against data that no longer exists — blanking the text
            // and flipping the colour mid-flight.
            required property int index
            required property string name
            required property string message
            required property string level

            width: listView.width
            height: label.implicitHeight + 50

            Rectangle {
                anchors.fill: parent
                color: Theme.surfaceContainerHigh
                radius: 8
            }

            MouseArea {
                anchors.fill: parent
                onClicked: Backend.notifyingLogHistoryModel.dismiss(delegateRoot.index)
            }

            Text {
                id: label

                anchors.left: parent.left
                anchors.right: parent.right
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                anchors.verticalCenter: parent.verticalCenter
                height: contentHeight

                text: delegateRoot.name !== "" ? delegateRoot.name + ": " + delegateRoot.message : delegateRoot.message
                color: delegateRoot.level === "ERROR" ? Theme.error : Theme.onSurface
                font.pixelSize: 16

                wrapMode: Text.Wrap

                Behavior on color {
                    ColorAnimation { easing.type: Easing.InOutQuad; duration: 200 }
                }
            }
        }

        clip: true
        spacing: 2

        // Slide in from just off the right edge. `listView.width` rather than a
        // literal, so the whole travel is inside the clip rect and visible.
        add: Transition {
            NumberAnimation { property: "opacity"; from: 0; to: 1.0; duration: 400; easing.type: Easing.OutQuad }
            NumberAnimation { property: "x"; from: listView.width; duration: 400; easing.type: Easing.OutQuad }
        }

        remove: Transition {
            NumberAnimation { property: "opacity"; to: 0; duration: 400; easing.type: Easing.InQuad }
            NumberAnimation { property: "x"; to: listView.width; duration: 400; easing.type: Easing.InQuad }
        }

        // Applies to the rows that stay put and have to shift into the gap.
        // No `to:` — the view supplies each item's destination, and setting one
        // here overrides it and sends the survivors somewhere else entirely.
        displaced: Transition {
            NumberAnimation { properties: "x,y"; duration: 400; easing.type: Easing.InOutQuad }
        }
    }
}
