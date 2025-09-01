import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Controls.Basic

import "." as Components
import "./base" as Base
import "../colobjs" as ColObjs
import "./text" as TextVariant

Item {
    id: root

    ListView {
        id: listView
        anchors.fill: parent
        model: Backend.notifyingLogHistoryModel
        delegate: Item {
            width: listView.width
            height: label.height + 50
            
            Rectangle {
                anchors.fill: parent
                color: Theme.surfaceContainerHigh
                radius: 8
            }

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    // Backend.dismissNotification(id)
                    console.log("Notification clicked:", id)
                }
            }

            Text {
                id: label
                width: parent.width
                height: contentHeight
                text: name != "" ? name + ": " + message : message
                color: level === "ERROR" ? Theme.error : Theme.onSurface
                font.pixelSize: 16
                anchors.left: parent.left
                anchors.leftMargin: 10
                anchors.verticalCenter: parent.verticalCenter
                
                wrapMode: Text.Wrap

                Behavior on color {
                    ColorAnimation { easing.type: Easing.InOutQuad; duration: 200 }
                }
            }
        }
        
        clip: true
        spacing: 2

        

        add: Transition {
            NumberAnimation { property: "opacity"; from: 0; to: 1.0; duration: 400 }
            NumberAnimation { property: "x"; from: 1000; duration: 400; easing.type: Easing.InOutQuad }
        }
        addDisplaced: Transition {
            NumberAnimation { property: "x,y"; duration: 400 }
        }
        
        remove: Transition {
            NumberAnimation { properties: "x"; to: 1000; duration: 400; easing.type: Easing.InOutQuad }
        }
        removeDisplaced: Transition {
            NumberAnimation { properties: "x"; to: 1000; duration: 400; easing.type: Easing.InOutQuad }
            NumberAnimation { property: "y"; duration: 400 }
        }
    }
}