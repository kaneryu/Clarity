import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Controls.Basic
import Qt.labs.qmlmodels

import "../components" as Components
import "../components/base" as Base
import "../colobjs" as ColObjs
import "../js/utils.js" as Utils
import "../components/text" as TextVariant

Item {
    id: root
    anchors.fill: parent

    property bool windowTooSmall: (root.height < 300) ? true : false

    Item {
        id: albumResultDelegate
    }

    Item {
        id: loadingIndicator
        anchors.centerIn: parent
        visible: Backend.searchModel.count === 0

        BusyIndicator {
            anchors.centerIn: parent
            running: true
        }
    }

    ListView {
        id: searchListViewTest
        anchors.top: parent.top
        anchors.left: parent.left

        width: parent.width
        height: parent.height

        clip: true
        model: Backend.searchModel

        spacing: 10

        DelegateChooser {
            id: delegateChooser
            role: "type"
            DelegateChoice {
                roleValue: "song"
                Rectangle {
                    required property string ytid
                    id: bg

                    width: 330 + 7
                    height: 80 + 7
                    color: Theme.surfaceContainer

                    radius: 20

                    Base.Song {
                        property string ytid: bg.ytid

                        id: song
                        song: Interactions.getSong(ytid)

                        textColor: Theme.onSurface

                        anchors.fill: parent
                        anchors.margins: 5

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                Interactions.searchPress(ytid)
                            }
                        }
                    }
                }
            }
            DelegateChoice {
                roleValue: "album"
                // Base.Album {
                //     required property string object
                //     id: album

                //     album: object
                //     anchors.fill: parent
                // }
            }
        }
        delegate: delegateChooser
    }
}