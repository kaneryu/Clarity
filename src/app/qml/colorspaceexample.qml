import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtWebChannel

import "components" as Components
import "components/pages" as Pages
import "components/base" as Base
import "colobjs" as ColObjs

ApplicationWindow {
    id: root
    visible: true
    width: 840
    height: 480
    minimumWidth: 840 / 2
    minimumHeight: 480 / 2

    title: "Clarity"

    Connections {
        target: Backend

        function onLoadComplete() {
            console.log("Loaded")
        }
    }
    ListModel {
        id: colorModel
        dynamicRoles: true
    }

    function jsonToColorModel(jsonString) {
        try {
            // Parse the JSON string
            const data = JSON.parse(jsonString);
    
            // Check if the parsed data is an array
            if (Array.isArray(data)) {
                // Create the model
                const model = data.map(item => ({
                    name: item.name,
                    value: item.value
                }));
                colorModel.clear();
                for (let i = 0; i < model.length; i++) {
                    colorModel.append(model[i]);
                }
                console.log("Model created with count:", model.length);
                console.log("Model:", model);
                return colorModel;
            } else {
                console.error("Parsed JSON is not an array:", data);
                return [];
            }
        } catch (e) {
            console.error("Invalid JSON string:", e);
            return [];
        }
    }

    Component {
        id: colorDelegate

        Item {
            Rectangle {
                width: 50
                height: 50

                color: value
                Text {
                    text: name
                    anchors.centerIn: parent
                }
                Component.onCompleted: {
                    console.log("Rectangle created with name:", name, "and value:", value)
                }
            }
        }

    }

    Item {
        id: cse
        /* This will create a grid of all colors contained in theme*/
        /* This returns a model with each item having name, value*/

        ListView {
            id: colorList
            model: Theme.getAllColorsAsModel()
            delegate: colorDelegate
            anchors.fill: parent
            clip: true
            spacing: 5
            orientation: ListView.Horizontal
            Component.onCompleted: {
                console.log("ListView model count:", model.count)
            }
        }

        Connections {
            target: Theme
        }
    }

    background: ColObjs.ColRect {
        id: background
        color: Theme.background
    }

    function onClosing(event) {
        event.accepted = false
    }
}