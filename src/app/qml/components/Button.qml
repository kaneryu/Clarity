import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform

Item {
    id: root

    property string text: "Button"
    property bool enabled: true

    signal clicked

    property real radius: 10

    property color bgcolor: baseColor
    property color textcolor: baseTextColor

    /*define hover, pressed, disabled, and base colors*/
    property color hoverColor: Theme.primaryFixedDim
    property color pressedColor: Theme.primaryFixed
    property color disabledColor: Theme.primaryContainer
    property color baseColor: Theme.primaryContainer

    property color hoverTextColor: Theme.onPrimaryFixed
    property color pressedTextColor: Theme.onPrimaryFixed
    property color disabledTextColor: Theme.onPrimaryContainer
    property color baseTextColor: Theme.onPrimaryContainer


    property real hoverRadius: 10
    property real pressedRadius: 0
    property real disabledRadius: 0
    property real baseRadius: 5

    Behavior on bgcolor {
        ColorAnimation {
            id: bgColorAnimation
            duration: 100
        }
    }

    Behavior on textcolor {
        ColorAnimation {
            id: textColorAnimation
            duration: 100
        }
    }

    Behavior on radius {
        NumberAnimation {
            id: radiusAnimation
            duration: 100
        }
    }

    
    onEnabledChanged: {
        if (!enabled) {
            bgcolor = disabledColor
            textcolor = disabledTextColor
            radius = disabledRadius
        }
    }
    Rectangle {
        id: buttonBackground
        width: parent.width
        height: parent.height
        color: root.bgcolor
        radius: root.radius
        border.color: root.bordercolor
    }

    Text {
        id: buttonText
        text: root.text
        color: root.textcolor
        font.pixelSize: 16
        anchors.centerIn: parent
    }

    MouseArea {
        id: buttonMouseArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: {
            if (root.enabled) {
                root.clicked()
            }
        }

        onPressed: {
            if (root.enabled) {
                root.bgcolor = root.pressedColor
                root.textcolor = root.pressedTextColor
                root.radius = root.pressedRadius
            }
        }
        
        onReleased: {
            if (root.enabled) {
                root.bgcolor = root.hoverColor
                root.textcolor = root.hoverTextColor
                root.radius = root.hoverRadius
            }
        }

        onEntered: {
            if (root.enabled) {
                root.bgcolor = root.hoverColor
                root.textcolor = root.hoverTextColor
                root.radius = root.hoverRadius
            }
        }

        onExited: {
            if (root.enabled) {
                root.bgcolor = root.baseColor
                root.textcolor = root.baseTextColor
                root.radius = root.baseRadius
            } else {
                root.bgcolor = root.disabledColor
                root.textcolor = root.disabledTextColor
                root.radius = root.disabledRadius
            }
        }
    }
}