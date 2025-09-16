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
        visible: true

        Rectangle {
            id: busyIndicatiorRect
            anchors.centerIn: parent
            width: 100
            height: 1000
            color: Theme.primary
            radius: 3600

            SequentialAnimation {
                running: true
                loops: Animation.Infinite
                OpacityAnimator {
                    target: busyIndicatiorRect
                    duration: 200
                    easing.type: Easing.InQuad
                    from: 0; to: 1;
                }
                OpacityAnimator {
                    target: busyIndicatiorRect
                    duration: 200
                    easing.type: Easing.OutQuad
                    from: 1; to: 0;
                }
            }

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
                Item {
                    id: songContainer
                    required property string ytid

                    width: searchListViewTest.width
                    height: 87

                    Base.Song {
                        id: song


                        song: Interactions.getSong(songContainer.ytid)

                        textColor: Theme.onSurface

                        anchors.fill: parent
                        anchors.margins: 5

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                Interactions.songSearchPress(songContainer.ytid)
                            }
                        }
                    }
                }
            }
            DelegateChoice {
                roleValue: "album"
                Item {
                    id: albumContainer
                    required property string ytid

                    width: searchListViewTest.width
                    height: 100

                    Base.Album {
                        id: album

                        anchors.fill: parent
                        anchors.margins: 5

                        album: Interactions.getAlbum(albumContainer.ytid)

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                Interactions.albumSearchPress(albumContainer.ytid)
                            }
                        }
                    }
                }
            }
        }
        delegate: delegateChooser
    }
}