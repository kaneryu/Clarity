import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Shapes
import QtQuick.Effects

import "../colobjs" as ColObjs
import "." as Components
import "./text" as TextVariant



Item {
    id: root
    width: parent.width
    height: parent.height
    visible: true
    property bool settingsButton: true
    property QtObject song: Interactions.currentSong

    // Connections {
    //     target: Interactions
    //     function onSongChanged() {
    //         console.log("Song changed")
    //     }
    // }

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
        function addAlpha(alpha, color) {
            let c = color
            // remove the # from the color
            c = c.slice(1)
            // add the alpha value 
            c = "#" + alpha + c
            return c
        }
        
        gradient: Gradient {
            GradientStop { position: 0; color: leftGlow.addAlpha("20", Theme.primary);}
            GradientStop { position: 1; color: leftGlow.addAlpha("00", Theme.primary);}
            orientation: Qt.Horizontal
        }

    }
    RowLayout {
        id: masterLayout
        spacing: 5
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 10


        RowLayout {
            id: leftPanel

            Layout.fillHeight: true
            Layout.preferredWidth: parent.width / 3
            Layout.alignment: Qt.AlignCenter
            Image {
                id: songImage
                source: Interactions.currentSongCover.image

                mipmap: true
                Layout.preferredHeight: 30
                Layout.preferredWidth: 30

                onSourceChanged: {
                    console.log("Song image changed")
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

            // Layout.fillHeight: true
            Layout.preferredHeight: parent.height / 1.2
            Layout.preferredWidth: parent.width / 3
            Layout.alignment: Qt.AlignCenter

            Components.Button {
                id: likeButton
                isIcon: true
                isTransparent: true
                icon: AssetsPath + "icons/songbar/fav.svg"

                Layout.fillHeight: true
                Layout.preferredWidth: height

                onClicked: Interactions.like()
                enabled: false
            }

            Components.Button {
                id: nextButton
                isIcon: true
                isTransparent: true
                icon: AssetsPath + "icons/songbar/skip_next.svg"

                Layout.fillHeight: true
                Layout.preferredWidth: height
                onClicked: Interactions.next()
            }

            Components.Button {
                id: playButton
                isIcon: true
                icon: (Interactions.isPlaying) ? AssetsPath + "icons/songbar/pause.svg" : AssetsPath + "icons/songbar/play.svg"

                Layout.fillHeight: true
                Layout.preferredWidth: height
                onClicked: Interactions.togglePlayback()
            }

            Components.Button {
                id: backButton
                isIcon: true
                isTransparent: true
                icon: AssetsPath + "icons/songbar/skip_previous.svg"

                Layout.fillHeight: true
                Layout.preferredWidth: height
                onClicked: Interactions.back()
            }

            Components.Button {
                id: downloadButton
                isIcon: true
                isTransparent: true
                icon: (root.song.downloadStatus == 2) ? AssetsPath + "icons/songbar/downloaded.svg" : (root.song.downloadStatus == 0) ? AssetsPath + "icons/songbar/download.svg" : AssetsPath + "icons/songbar/downloading.svg"

                Layout.fillHeight: true
                Layout.preferredWidth: height
                onClicked: Interactions.downloadSong(Interactions.currentSongId)

                Components.ProgressBar {
                    id: downloadProgress
                    anchors.fill: parent

                    vertical: false
                    input: false
                    fillColor: leftGlow.addAlpha("50", Theme.primary)
                    backgroundColor: "transparent"

                    radius: downloadButton.radius
                    percent: root.song.downloadProgress
                }
            }
        }
        RowLayout {
            id: rightPanel

            Layout.fillHeight: true
            Layout.preferredWidth: parent.width / 3
            Layout.alignment: Qt.AlignCenter

            TextVariant.Default {
                id: currentTime
                text: Interactions.currentSongTime
                Timer {
                    id: timeTimer
                    interval: 1000
                    running: true
                    repeat: true
                    
                    onTriggered: {
                        currentTime.text = Interactions.currentSongTime
                    }
                }       
            }

            Components.ProgressBar {
                id: songProgress

                Layout.preferredHeight: 10
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
                text: Interactions.currentSongDuration
            }
        }
    }
}