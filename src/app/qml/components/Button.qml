import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Effects

Item {
    id: root

    property string text: "Button"
    property bool enabled: true

    signal clicked

    property real radius: (state == "base") ? 5 : (state == "hover") ? 10 : (state == "pressed") ? 0 : 0

    property string colortype: "primary"
    property string state: "base" // base, hover, pressed, disabled

    property color bgcolor: (colortype === "primary") ? (state == "base" ? Theme.primaryContainer : (state == "hover" ? Theme.primaryContainer : (state == "pressed" ? Theme.primaryContainer : Theme.surfaceVariant)))
    :(colortype === "secondary") ? (state == "base" ? Theme.secondaryContainer : (state == "hover" ? Theme.secondaryContainer : (state == "pressed" ? Theme.secondaryContainer : Theme.surfaceVariant))) : Theme.primaryContainer

    property color textcolor: (colortype === "primary") ? (state == "base" ? Theme.onPrimaryContainer : (state == "hover" ? Theme.onPrimaryContainer : (state == "pressed" ? Theme.onPrimaryContainer : Theme.onSurface)))
    :(colortype === "secondary") ? (state == "base" ? Theme.onSecondaryContainer : (state == "hover" ? Theme.onSecondaryContainer : (state == "pressed" ? Theme.onSecondaryContainer : Theme.onSurface))) : Theme.onPrimaryContainer


    onStateChanged: {
        console.log("State changed to: " + state)
    }
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
        id: buttonBackground
        width: parent.width
        height: parent.height
        color: root.bgcolor
        radius: root.radius
        border.color: root.bordercolor

    }

    MultiEffect {
        id: dropShadow
        source: buttonBackground

        anchors.fill: buttonBackground

        shadowScale: 0
        shadowHorizontalOffset: 0
        shadowVerticalOffset: 5
        shadowBlur: 0.7

        shadowEnabled: (shadowScale > 0) ? true : false


        shadowColor: "#71000000"

        onShadowColorChanged: {
            console.log(Theme.shadow)
        }

        onShadowEnabledChanged: {
            console.log("Shadow enabled: " + shadowEnabled)
            
        }

        states: [
            State {
                name: "hover"
                when: root.state == "hover"
                PropertyChanges {
                    target: dropShadow
                    shadowColor: "#71000000"
                }
            },
            State {
                name: "base"
                when: root.state == "base" || root.state == "pressed"
                PropertyChanges {
                    target: dropShadow
                    // shadowEnabled: false
                }
            }
        ]

        transitions: [
            Transition {
                from: "*"
                to: "hover"
                NumberAnimation {
                    target: dropShadow
                    property: "shadowScale"
                    duration: 100
                    from: 0
                    to: 1
                }
            },
            Transition {
                from: "hover"
                to: "base"
                NumberAnimation {
                    target: dropShadow
                    property: "shadowScale"
                    duration: 100
                    from: 1
                    to: 0
                }
            }
        ]


        // SequentialAnimation on shadowEnabled {
        //     NumberAnimation {
        //         duration: 100
        //         target: dropShadow.shadowScale
        //         from: 0
        //         to: 1
        //     }
        // }
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
                root.state = "pressed"
            }
        }
        
        onReleased: {
            if (root.enabled) {
                if (buttonMouseArea.containsMouse) {
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