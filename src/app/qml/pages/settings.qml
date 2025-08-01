import QtWebView
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Effects

import "../colobjs" as ColObjs
import "../components/text" as TextVariant
import "../components" as Components

Item {
    id: root
    anchors.fill: parent

    Component {
        id: treeViewDelegate

        Item {
            id: treeViewItem

            implicitWidth: padding + label.x + label.implicitWidth + padding
            implicitHeight: label.implicitHeight * 1.5

            readonly property real indentation: 20
            readonly property real padding: 5

            // Assigned to by TreeView:
            required property TreeView treeView
            required property bool isTreeNode
            required property bool expanded
            required property bool hasChildren
            required property int depth
            required property int row
            required property int column
            required property bool current

            // Rotate indicator when expanded by the user
            // (requires TreeView to have a selectionModel)
            property Animation indicatorAnimation: NumberAnimation {
                target: indicator
                property: "rotation"
                from: treeViewItem.expanded ? 0 : 90
                to: treeViewItem.expanded ? 90 : 0
                duration: 100
                easing.type: Easing.OutQuart
            }
            TableView.onPooled: indicatorAnimation.complete()
            TableView.onReused: if (current) indicatorAnimation.start()
            onExpandedChanged: indicator.rotation = expanded ? 90 : 0

            // ColObjs.ColRect {
            //     id: background
            //     anchors.fill: parent
            //     color: Theme.surfaceContainerHighest
            // }

            Label {
                id: indicator
                x: padding + (treeViewItem.depth * treeViewItem.indentation)
                anchors.verticalCenter: parent.verticalCenter
                visible: treeViewItem.isTreeNode && treeViewItem.hasChildren
                text: "▶"
                
                color: Theme.onSurface

                TapHandler {
                    onSingleTapped: {
                        let index = treeViewItem.treeView.index(treeViewItem.row, treeViewItem.column)
                        treeViewItem.treeView.toggleExpanded(treeViewItem.row)
                    }
                }
            }

            Label {
                id: label
                x: padding + (isTreeNode ? (depth + 1) * indentation : 0)
                anchors.verticalCenter: parent.verticalCenter
                clip: true
                text: model.display

                color: Theme.onSurface
            }

            Item {
                id: configItem
                anchors.left: label.right
                anchors.leftMargin: 10
                anchors.right: parent.right

                anchors.top: parent.top
                anchors.bottom: parent.bottom
                Connections{
                    target: Backend
                    function onSettingChanged() {
                        // Reload the control when the model data changes
                        console.log("Setting changed for", model.display);
                        controlLoader.modelValue = model.value;
                    }
                }
                Loader {
                    id: controlLoader
                    // Set properties on the loader that will be passed to the loaded item
                    property var modelValue: value
                    property var model_: model

                    anchors.fill: parent

                    function setData(value) {
                        console.log("Setting data for", model.display, "to", value);
                        model.value = value
                    }

                    function getComponentType() {
                        switch (model.type) {
                            case "bool":
                                return switchComponent;
                            case "int":
                            case "float":
                                return sliderComponent;
                            case "str":
                            case "password":
                                return textComponent;
                        }
                        return null;
                    }

                    function reload() {
                        controlLoader.sourceComponent = null;
                        controlLoader.sourceComponent = getComponentType();
                    }

                    sourceComponent: getComponentType()
                }
            }
        }
    }

    Component {
        id: switchComponent
        Components.Checkbox {
            anchors.fill: parent
            // Two-way binding with the Loader's property
            checked: modelValue
            onClicked: {
                setData(checked);
            }
        }
    }

    Component {
        id: sliderComponent
        Slider {
            from: model_.min || 0
            to: model_.max || 100
            stepSize: model_.step || 1
            // Two-way binding with the Loader's property
            value: parent.modelValue
            onValueChanged: {
                if (value !== parent.modelValue) {
                    setData(value);
                }
            }
        }
    }

    Component {
        id: textComponent
        TextField {
            selectByMouse: true
            text: modelValue
            onTextChanged: {
                console.log("Text changed for", model_.display, "to", text);
            }
            onAccepted: {
                if (text !== parent.modelValue) {
                    setData(text);
                }
            }
        }
    }
    
    Component {
        id: treeViewGroupDelegate

        Item {
            id: treeViewItem

            implicitWidth: treeView.width
            implicitHeight: label.implicitHeight * 1.5

            readonly property real indentation: 20
            readonly property real padding: 5

            // Assigned to by TreeView:
            required property TreeView treeView
            required property bool isTreeNode
            required property bool expanded
            required property bool hasChildren
            required property int depth
            required property int row
            required property int column
            required property bool current

            // Rotate indicator when expanded by the user
            // (requires TreeView to have a selectionModel)
            property Animation indicatorAnimation: NumberAnimation {
                target: indicator
                property: "rotation"
                from: treeViewItem.expanded ? 0 : 90
                to: treeViewItem.expanded ? 90 : 0
                duration: 1000
                easing.type: Easing.OutQuart
            }
            TableView.onPooled: indicatorAnimation.complete()
            TableView.onReused: if (current) indicatorAnimation.start()
            onExpandedChanged: indicator.rotation = expanded ? 90 : 0

            // ColObjs.ColRect {
            //     id: background
            //     anchors.fill: parent
            //     color: Theme.primary
            // }

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    let index = treeViewItem.treeView.index(treeViewItem.row, treeViewItem.column)
                    treeViewItem.treeView.toggleExpanded(treeViewItem.row)
                }
            }
            Label {
                id: indicator
                x: padding + (treeViewItem.depth * treeViewItem.indentation)
                anchors.verticalCenter: parent.verticalCenter
                visible: treeViewItem.isTreeNode && treeViewItem.hasChildren
                text: "▶"
                color: Theme.onSurface
            }


            TextVariant.Default {
                id: label
                color: Theme.onSurface
                x: padding + (isTreeNode ? (depth + 1) * indentation : 0)
                anchors.verticalCenter: parent.verticalCenter
                clip: true
                text: model.display.replace("_group", "")
            }

            Rectangle {
                anchors.left: label.right
                anchors.leftMargin: -15
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                
                height: 10
                radius: 5

                color: Theme.onSurface
                
            }

        }
    }

    TreeView {
        id: treeView
        anchors.fill: parent
        model: Backend.settingsModel

        reuseItems: false

        delegate: chooser
        
        WheelHandler {
            onWheel: {
                parent.contentY -= wheel.angleDelta / 10
                wheel.accepted = true
            }
        }
        DelegateChooser {
            id: chooser
            role: "isGroup"
            DelegateChoice { roleValue: true; delegate: treeViewGroupDelegate }
            DelegateChoice { roleValue: false; delegate: treeViewDelegate }
        }
    }
}