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
            implicitHeight: descriptionLabel.contentHeight * 1.15 + configItem.height + padding * 2

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

            // Let the view know how tall this row needs to be (for description lines)
            // function updateRowHeight() {
            //     var base = Math.max(label.implicitHeight, indicator.implicitHeight)
            //     var extra = 40 * descriptionLabel.lineCount + padding
            //     console.log("Row", row, "base:", base, "extra:", extra)
            //     var h = Math.ceil(base + extra + padding)
            //     // Update the map immutably so bindings react
            //     var map = treeView.rowHeights || {}
            //     var next = {}
            //     for (var k in map) next[k] = map[k]
            //     next[row] = h
            //     treeView.rowHeights = next
            // }

            // Component.onCompleted: updateRowHeight()
            // onImplicitHeightChanged: updateRowHeight()

            Item {
                id: startx
                width: 5
                x: padding + (isTreeNode ? (depth + 1) * indentation : 0)
            }

            Label {
                id: label

                anchors.left: startx.right
                anchors.verticalCenter: configItem.verticalCenter

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
                height: 30

                // Keep the control inline with the setting title; description sits below
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
                        case "switch":
                            return switchComponent;
                        case "dropdown":
                            return dropdownComponent;
                        case "textEdit":
                        default:
                            return textComponent;
                        }
                    }

                    function reload() {
                        controlLoader.sourceComponent = null;
                        controlLoader.sourceComponent = getComponentType();
                    }

                    sourceComponent: getComponentType()
                }
            }

            // Setting description, shown under the control row
            Text {
                id: descriptionLabel
                text: model.description || ""
                visible: text && text.length > 0
                wrapMode: Text.WordWrap
                color: Theme.onSurface
                opacity: 0.75
                
                anchors.top: label.bottom
                anchors.left: startx.right
                anchors.right: parent.right
                anchors.leftMargin: padding + 15
                anchors.topMargin: 10

                font.pixelSize: Math.max(11, label.font.pixelSize - 2)

                height: contentHeight
            }
        }
    }

    Component {
        id: switchComponent
        Components.Checkbox {
            anchors.fill: parent
            checked: modelValue
            onClicked: setData(checked)
        }
    }

    Component {
        id: textComponent
        TextField {
            selectByMouse: true
            text: modelValue
            echoMode: model_.secure ? TextInput.Password : TextInput.Normal
            onAccepted: {
                if (text !== parent.modelValue) {
                    setData(text);
                }
            }
        }
    }

    Component {
        id: dropdownComponent
        ComboBox {
            anchors.fill: parent
            // Actual values and their visual labels
            property var options: model_.dropdownOptions || []
            property var visualOptions: model_.visualDropdownOptions || options
            model: visualOptions
            // Keep selection by matching actual value index
            currentIndex: Math.max(0, options.indexOf(parent.modelValue))
            // Write back the actual value corresponding to the selected label
            onActivated: setData(options[currentIndex])
        }
    }

    Component {
        id: treeViewGroupDelegate

        Item {
            id: groupTreeViewItem

            implicitWidth: treeView.width - scrollView.effectiveScrollBarWidth
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
                from: groupTreeViewItem.expanded ? 0 : 90
                to: groupTreeViewItem.expanded ? 90 : 0
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
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.right: parent.right

                anchors.rightMargin: (scrollView.effectiveScrollBarWidth > 0 ? 30 : 0)
                onClicked: {
                    let index = groupTreeViewItem.treeView.index(groupTreeViewItem.row, groupTreeViewItem.column)
                    groupTreeViewItem.treeView.toggleExpanded(groupTreeViewItem.row)
                }

                // Rectangle {
                //     anchors.fill: parent
                //     color: "green"
                //     border.color: "red"
                // }
            }
            Label {
                id: indicator
                x: padding + (groupTreeViewItem.depth * groupTreeViewItem.indentation)
                anchors.verticalCenter: parent.verticalCenter
                visible: groupTreeViewItem.isTreeNode && groupTreeViewItem.hasChildren
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


    
    ScrollView {
        id: scrollView
        anchors.fill: parent
        clip: true

        // Flickable properties

        property real contentY: treeView.contentY

        ScrollBar.vertical.interactive: true

        TreeView {
            id: treeView
            anchors.fill: parent
            model: Backend.settingsModel

            reuseItems: false

            delegate: chooser

            DelegateChooser {
                id: chooser
                role: "isGroup"
                DelegateChoice { roleValue: true; delegate: treeViewGroupDelegate }
                DelegateChoice { roleValue: false; delegate: treeViewDelegate }
            }
        }
    }
}