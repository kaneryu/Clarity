import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Effects

import "./text" as TextVariant
import "../colobjs" as ColObjs

Item {
    id: root

    property bool enabled: true
    signal internalClicked()

    property real radius: (state == "base") ? 5 : (state == "hover") ? 10 : (state == "pressed") ? 0 : 0

    property string colortype: "primary"
    property string state: "base" // base, hover, pressed, disabled

    property bool isTransparent: false

    property color bgcolor: (isTransparent) ? "transparent" : (colortype === "primary") ? (state == "base" ? Theme.primaryContainer : (state == "hover" ? Theme.primaryContainer : (state == "pressed" ? Theme.primaryContainer : Theme.surfaceVariant)))
    :(colortype === "secondary") ? (state == "base" ? Theme.secondaryContainer : (state == "hover" ? Theme.secondaryContainer : (state == "pressed" ? Theme.secondaryContainer : Theme.surfaceVariant))) : Theme.primaryContainer

    property color textcolor: (colortype === "primary") ? (state == "base" ? Theme.onPrimaryContainer : (state == "hover" ? Theme.onPrimaryContainer : (state == "pressed" ? Theme.onPrimaryContainer : Theme.onSurface)))
    :(colortype === "secondary") ? (state == "base" ? Theme.onSecondaryContainer : (state == "hover" ? Theme.onSecondaryContainer : (state == "pressed" ? Theme.onSecondaryContainer : Theme.onSurface))) : Theme.onPrimaryContainer

    /*define hover, pressed, disabled, and base colors*/
    property color hoverColor: Theme.primaryContainer
    property color pressedColor: Theme.primaryContainer
    property color disabledColor: Theme.surfaceVariant
    property color baseColor: Theme.primaryContainer

    property color hoverTextColor: Theme.onPrimaryContainer
    property color pressedTextColor: Theme.onPrimaryContainer
    property color disabledTextColor: Theme.onSurface
    property color baseTextColor: Theme.onPrimaryContainer


    property real hoverRadius: 10
    property real pressedRadius: 0
    property real disabledRadius: 0
    property real baseRadius: 5

    property real hoverShadow: 1
    property real pressedShadow: 0
    property real disabledShadow: 0
    property real baseShadow: 0


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
        id: background
        width: parent.width
        height: parent.height
        color: root.bgcolor
        radius: root.radius
    }

    MouseArea {
        id: mouse_
        anchors.fill: parent
        hoverEnabled: true

        onClicked: {
            if (root.enabled) {
                root.internalClicked();
            }
        }

        onPressed: {
            if (root.enabled) {
                root.state = "pressed"
            }
        }
        
        onReleased: {
            if (root.enabled) {
                if (mouse_.containsMouse) {
                    root.state = "hover"
                } else {
                    root.state = "base"
                }
            }
        }

        onEntered: {
            if (root.enabled) {
                root.state = "hover"
            } else {
                root.state = "disabled"
            }
        }

        onExited: {
            if (root.enabled) {
                root.state = "base"
            } else {
                root.state = "disabled"
            }
        }
    }
}