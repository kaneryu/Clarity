// import QtQuick
// import QtQuick.Controls
// import QtQuick.Layouts
// import QtQuick.Shapes

// Item {
//     id: root
    
//     width: 50
//     height: 100
       
//     anchors.horizontalCenter: parent.horizontalCenter
//     anchors.verticalCenter: parent.verticalCenter
    
    
//     property real percent: 50
//     property bool vertical: true

//     property alias fillColor: fill.color
//     property alias backgroundColor: background.color

//     property alias radius: background.radius

//     property alias border: background.border
    
//     fillColor: red
//     backgroundColor: transparent
      
//     Rectangle {
//         id: background
//         clip: true
//         anchors.fill: parent
        
//         Rectangle {
//             id: fill
//             width: (root.vertical) ? parent.width : parent.width * (root.percent / 100)
//             height: (root.vertical) ? parent.height * (root.percent / 100) : parent.height
            
            
//             anchors.bottom: parent.bottom
//             color: "red"
            
//         }
//     }

//     Item {
//         anchors.centerIn: parent
//         id: radii
//         width: background.width
//         height: background.height
//         property string color: 'transparent'
//         property int rightTopCornerRadius: 5
//         property int rightBottomCornerRadius: 5
//         property int leftBottomCornerRadius: 5
//         property int leftTopCornerRadius: 5
//     }

// }

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Shapes

Item {
    id: root
    
    
    property real percent
    property bool vertical

    property alias fillColor: fill.color
    property alias backgroundColor: background.color

    property alias radius: background.radius

    property alias border: background.border

    property bool input: true

    signal click(real percent)

    Behavior on percent {
        NumberAnimation {
            duration: 100
        }
    }

    Rectangle {
        id: background
        anchors.fill: parent
        
        Rectangle {
            id: fill
            width: (root.vertical) ? parent.width : parent.width * (root.percent / 100)
            height: (root.vertical) ? parent.height * (root.percent / 100) : parent.height
            anchors.bottom: parent.bottom

            topLeftRadius: (root.vertical) ? ((root.percent > 85) ? root.radius : 0) : root.radius
            topRightRadius: (root.vertical) ? ((root.percent > 85) ? root.radius : 0) : ((root.percent > 85) ? root.radius : 0)

            bottomLeftRadius: (root.vertical) ? root.radius :  root.radius
            bottomRightRadius: (root.vertical) ? root.radius : ((root.percent > 85) ? root.radius : 0)

            // If Vertical, when >0, the top right and top left corners should be rounded
            // If Horizontal, when >0, the top right and bottom right corners should be rounded

            antialiasing: true
        }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        enabled: root.input
        onClicked: {
            console.log("ProgressBar clicked at", mouseX, mouseY)
            console.log("Parent size:", parent.width, parent.height)
            if (root.vertical) {
                root.click((mouseY / parent.height) * 100)
                console.log("Calculated vertical percent:", (mouseY / parent.height) * 100)
            } else {
                root.click((mouseX / parent.width) * 100)
                console.log("Calculated horizontal percent:", (mouseX / parent.width) * 100)
            }
        }
    }
}
