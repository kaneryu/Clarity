import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Controls.Basic

import "../components" as Components
import "../components/base" as Base
import "../components/text" as Text
import "../colobjs" as ColObjs


Item {
    id: root
    anchors.fill: parent
    
    property bool windowTooSmall: (root.height < 300) ? true : false
    
    Components.Button {
        id: button
        text: "Click me"
        width: 100
        height: 50
        anchors.centerIn: parent
        onClicked: {
            l.sourceComponent = null
            l.sourceComponent = thingie
        }
    }

    Loader {
        id: l
        sourceComponent: thingie
        anchors.fill: parent
    }

    Component {
        id: thingie
        ColumnLayout {
            id: columnLayout
            anchors.fill: parent
            spacing: 10
            Text.Small {
                text: "Minor Information"
            }
            Text.Default {
                text: "Song Title"
            }
            Text.SectionHeader {
                text: "Section Header"
            }
            Text.Header {
                text: "Page Header"
            }
            Text.SubHeader {
                text: "Subheader"
            }
            Text.Title {
                text: "Important Title"
            }
        }
    }
}