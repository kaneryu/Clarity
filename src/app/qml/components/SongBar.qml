import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Shapes
import QtQuick.Effects

import "../colobjs" as ColObjs
import "." as Components
import "./text" as TextVariant
import "../js/utils.js" as Utils



Item {
    id: root
    width: parent.width
    height: parent.height
    visible: true
    property bool settingsButton: true
    property QtObject song: Interactions.currentSong

    ColObjs.ColRect {
        id: songbarBackground
        width: parent.width
        height: parent.height
        color: Theme.surfaceContainer
        radius: 10
    }

    MouseArea {
        id: mouseBlocker
        anchors.fill: parent
        acceptedButtons: Qt.NoButton
    }

    Rectangle {
        id: leftGlow
        // This will be a gradient from theme.primary to transparent
        width: parent.width / 10
        height: parent.height
        radius: 10, 0, 0, 10
        anchors.left: root.left
        
        gradient: Gradient {
            GradientStop { position: 0; color: Utils.addAlpha("20", Theme.primary);}
            GradientStop { position: 1; color: Utils.addAlpha("00", Theme.primary);}
            orientation: Qt.Horizontal
        }

    }
    RowLayout {
        id: leftPanel
        
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        
        anchors.leftMargin: 5

        Image {
            id: songImage
            source: "image://SongCover/" + song.id + "/300"

            mipmap: true
            Layout.preferredHeight: 30
            Layout.preferredWidth: 30
            
            BusyIndicator {
                id: imageLoader
                anchors.fill: parent
                running: true
                visible: songImage.status === Image.Loading
            }

        }

        TextVariant.Small {
            id: songTitle
            text: root.song.title + " - " + root.song.artist

            color: Theme.onSurface
        }
    }

    RowLayout {
        id: centerPanel

        anchors.centerIn: parent
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        property int iconHeight: 35

        // Components.Button {
        //     id: likeButton
        //     isIcon: true
        //     isTransparent: true
        //     icon: AssetsPath + "icons/songbar/fav.svg"

        //     Layout.preferredHeight: centerPanel.iconHeight
        //     Layout.preferredWidth: height

        //     onClicked: Interactions.like()
        // }
        Components.Checkbox {
            id: likeCheckbox
            checked: root.song.likedStatus

            onClicked: {
                Interactions.like(likeCheckbox.checked);
            }

            Layout.preferredHeight: centerPanel.iconHeight
            Layout.preferredWidth: height
        }

        Components.Button {
            id: backButton
            isIcon: true
            isTransparent: true
            icon: AssetsPath + "icons/songbar/skip_previous.svg"

            Layout.preferredHeight: centerPanel.iconHeight
            Layout.preferredWidth: height
            onClicked: Interactions.back()

            textcolor: Theme.onSurface
        }

        Components.Button {
            id: playButton
            isIcon: true
            // icon: (Interactions.isPlaying) ? AssetsPath + "icons/songbar/pause.svg" : AssetsPath + "icons/songbar/play.svg"
            // 0 = playing, 1 = paused, 2 = buffering, 3 = stopped, 4 = error
                
            icon: AssetsPath + "icons/songbar/play.svg"

            states: [
                State {
                    name: "notReady"
                    when: Interactions.playingStatus == -1
                    PropertyChanges {
                        target: playButton
                        icon: AssetsPath + "icons/songbar/close.svg"
                    }
                },
                State {
                    name: "playing"
                    when: Interactions.playingStatus == 0
                    PropertyChanges {
                        target: playButton
                        icon: AssetsPath + "icons/songbar/pause.svg"
                    }
                },
                State {
                    name: "paused"
                    when: Interactions.playingStatus == 1
                    PropertyChanges {
                        target: playButton
                        icon: AssetsPath + "icons/songbar/play.svg"
                    }
                },
                State {
                    name: "buffering"
                    when: Interactions.playingStatus == 2
                    PropertyChanges {
                        target: playButton
                        icon: AssetsPath + "icons/songbar/pending.svg"
                    }
                },
                State {
                    // Local buffering should not interrupt playback UX
                    name: "bufferingLocal"
                    when: Interactions.playingStatus == 6
                    PropertyChanges {
                        // Keep showing pause to indicate playback should continue
                        playButton.icon: AssetsPath + "icons/songbar/pause.svg"
                    }
                },
                State {
                    name: "stopped"
                    when: Interactions.playingStatus == 3
                    PropertyChanges {
                        target: playButton
                        icon: AssetsPath + "icons/songbar/close.svg"
                    }
                },
                State {
                    name: "error"
                    when: Interactions.playingStatus == 4
                    PropertyChanges {
                        target: playButton
                        icon: AssetsPath + "icons/songbar/close.svg"
                    }
                }
            ]
            Connections {
                target: Interactions
            }

            Layout.preferredHeight: centerPanel.iconHeight
            Layout.preferredWidth: height
            onClicked: Interactions.togglePlayback()
        }

        Components.Button {
            id: nextButton
            isIcon: true
            isTransparent: true
            icon: AssetsPath + "icons/songbar/skip_next.svg"

            Layout.preferredHeight: centerPanel.iconHeight
            Layout.preferredWidth: height
            onClicked: Interactions.next()
            textcolor: Theme.onSurface

        }

        Components.Button {
            id: downloadButton
            isIcon: true
            isTransparent: true
            icon: (root.song.downloadState == 2) ? AssetsPath + "icons/songbar/downloaded.svg" : (root.song.downloadState == 0) ? AssetsPath + "icons/songbar/download.svg" : AssetsPath + "icons/songbar/downloading.svg"

            Layout.preferredHeight: centerPanel.iconHeight
            Layout.preferredWidth: height
            onClicked: Interactions.downloadSong(Interactions.currentSongId)
            textcolor: Theme.onSurface

            Components.ProgressBar {
                id: downloadProgress
                anchors.fill: parent

                vertical: false
                input: false
                fillColor: Utils.addAlpha("50", Theme.primary)
                backgroundColor: "transparent"

                radius: downloadButton.radius
                percent: root.song.downloadProgress
            }

        }
    }
    
    RowLayout {
        id: rightPanel

        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        width: parent.width / 4

        anchors.rightMargin: 10

        Components.Button {
            id: queueButton
            isIcon: true
            isTransparent: true
            icon: AssetsPath + "icons/songbar/queue_music.svg"
            textcolor: (Backend.queueVisible) ? Theme.secondary : Theme.primary

            Layout.preferredHeight: centerPanel.iconHeight
            Layout.preferredWidth: height
            onClicked: Backend.queueVisible = !Backend.queueVisible
        }


        TextVariant.Default {
            id: currentTime
            Layout.maximumWidth: 45
            text: Utils.secondsToHMS(Interactions.currentSongTime)
        }

        Components.ProgressBar {
            id: songProgress

            Layout.preferredHeight: 10
            Layout.preferredWidth: 100
            Layout.fillWidth: true

            vertical: false
            fillColor: Theme.primary
            backgroundColor: Theme.surfaceContainerLow

            radius: 10
            percent: Interactions.currentSongTime / Interactions.currentSongDuration * 100

            onClick: (percent) => Interactions.seekPercent(percent)

            Timer {
                id: progressTimer
                interval: 150
                running: true
                repeat: true
                onTriggered: {
                    songProgress.percent = Interactions.currentSongTime / Interactions.currentSongDuration * 100
                }
            }
        }

        TextVariant.Default {
            id: durationText
            Layout.maximumWidth: 45

            text: Utils.secondsToHMS(Interactions.currentSongDuration)
        }
        
        Timer {
            id: timeTimer
            interval: 200
            running: true
            repeat: true
            
            onTriggered: {
                if (Interactions.currentSongTime > currentTime.text) {
                    playButton.state = "playing"
                }
                currentTime.text = Utils.secondsToHMS(Interactions.currentSongTime)
                durationText.text = Utils.secondsToHMS(Interactions.currentSongDuration)
            }
        }   
    }
}