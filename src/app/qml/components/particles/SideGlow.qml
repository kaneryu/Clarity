import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Effects
import QtQuick.Particles
import QtQuick.Shapes

Item {
    id: root
    anchors.fill: parent

    property bool running: true

    // Particles start on the bottom left corner, emitting towards the top right
    ParticleSystem {
        id: particles
        
        anchors.bottom: parent.bottom
        anchors.left: parent.left

        height: parent.height
        width: 500
    
        clip: false

        Item {
            id: topRightTarget

            anchors.top: parent.top
            anchors.right: parent.right
        }


        // Rectangle {
        //     anchors.fill: parent
        //     color: "red"
        //     opacity: 0.1
        // }
        
        ImageParticle {
            groups: ["center"]
            source: "qrc:///particleresources/star.png"
        }

        // ItemParticle {
        //     groups: ["center","edge"]
        //     anchors.fill: parent
        //     delegate: Rectangle {
        //         width: 15
        //         height: 15
        //         radius: 230
        //         color: "white"
        //         opacity: 0.8
        //     }
        // }

        Emitter {
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            width: 2
            height: parent.height / 1.5
            group: "center"
            emitRate: 20
            lifeSpan: 2000
            size: 20
            sizeVariation: 16
            endSize: 5

            enabled: root.running

            //! [0]
            velocity: TargetDirection {
                targetItem: topRightTarget
                targetVariation: 50
                proportionalMagnitude: true
                magnitude: 0.2
            }

            //! [0]
        }

        Emitter {
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            width: parent.width / 4
            height: 2
            group: "center"
            emitRate: 20
            lifeSpan: 2000
            size: 20
            sizeVariation: 16
            endSize: 5

            enabled: root.running

            //! [0]
            velocity: TargetDirection {
                targetItem: topRightTarget
                targetVariation: 50
                proportionalMagnitude: true
                magnitude: 0.2
            }

            //! [0]
        }
    }
}