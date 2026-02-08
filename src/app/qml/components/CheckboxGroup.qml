import QtWebView
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Effects

import "../colobjs" as ColObjs
import "text" as TextVariant
import "." as Components


Item {
    id: root

    property alias checkboxes: checkboxColumn.children
    property var checkgroupData: ({})

    signal activeCheckboxChanged()

    property int activeCheckboxIndex: -1


    RowLayout {
        id: checkboxColumn
        anchors.fill: parent
        spacing: 16
    }

    function onCheckboxClicked(checkstate, text, identifier) {
        if (checkstate) {
            return // active checkbox was clicked, do nothing
        } else {
            for (var i = 0; i < checkboxColumn.children.length; i++) {
                var checkbox = checkboxColumn.children[i]
                if (checkbox.text === text) {
                    checkbox.checkState = true
                    root.activeCheckboxIndex = i
                } else {
                    if (checkbox.checkState === false) {
                        continue
                    }
                    checkbox.checkState = false
                    if (root.checkgroupData.hasOwnProperty(identifier)) {
                        var callback = root.checkgroupData[identifier].onDeactivate
                        if (callback !== undefined && callback !== null) {
                            callback()
                        }
                    }
                }
            }
            if (root.checkgroupData.hasOwnProperty(identifier)) {
                var callback = root.checkgroupData[identifier].onActive
                if (callback !== undefined && callback !== null) {
                    callback()
                }
            }
            root.activeCheckboxChanged()
        }
    }

    function getCheckedStates() {
        var states = []
        for (var i = 0; i < checkboxColumn.children.length; i++) {
            var checkbox = checkboxColumn.children[i]
            states.push(checkbox.checkState)
        }
        return states
    }


    function addCheckbox(text, checked, identifier, onActiveCallback) {
        var component = Qt.createComponent("Checkbox.qml")
        if (component.status === Component.Ready) {
            var checkbox = component.createObject(checkboxColumn, {
                text: text,
                checkState: checked,
                internalClickedFunction: function () {root.onCheckboxClicked(checkbox.checkState, checkbox.text, identifier)}, // Remove the default click handler
            })

            root.checkgroupData[identifier] = {
                onActive: onActiveCallback,
                text: text
            }

            if (checkbox === null) {
                console.log("Error creating checkbox")
                return null
            }
            return checkbox
        } else {
            console.log("Error loading Checkbox.qml")
            return null
        }
    }

    function addCheckboxObject(checkboxObject, identifier, onActiveCallback) {
        checkboxObject.internalClickedFunction = function () {root.onCheckboxClicked(checkboxObject.checkState, checkboxObject.text, identifier)}
        
        root.checkgroupData[identifier] = {
            onActive: onActiveCallback,
            text: checkboxObject.text
        }

        checkboxObject.parent = checkboxColumn
    }

}