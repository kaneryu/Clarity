import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Effects

import "../colobjs" as ColObjs
import "../components" as Components
import "../components/text" as TextVariant
import "../js/utils.js" as Utils

Item {
    id: root
    anchors.fill: parent
    
    property QtObject song: Interactions.currentSong

    ColObjs.ColRect {
        id: background
        anchors.fill: parent
        color: Theme.background
        radius: 10
    }

    ColumnLayout {
        id: mainLayout
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        // Top section - Back button and title
        RowLayout {
            id: headerSection
            Layout.fillWidth: true
            Layout.preferredHeight: 50

            Components.Button {
                id: backToMainButton
                isIcon: true
                isTransparent: true
                icon: AssetsPath + "icons/songbar/skip_previous.svg"
                
                Layout.preferredHeight: 40
                Layout.preferredWidth: 40
                
                onClicked: Backend.navigateToPage("")  // Navigate to home
            }

            TextVariant.Title {
                id: pageTitle
                text: "Now Playing"
                color: Theme.onBackground
                Layout.fillWidth: true
            }
        }

        // Main content area
        RowLayout {
            id: contentLayout
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 30

            // Left side - Album art and song info
            ColumnLayout {
                id: leftColumn
                Layout.fillHeight: true
                Layout.preferredWidth: parent.width * 0.4
                spacing: 20

                // Large album artwork
                Item {
                    id: albumArtContainer
                    Layout.fillWidth: true
                    Layout.preferredHeight: width
                    Layout.alignment: Qt.AlignCenter

                    ColObjs.ColRect {
                        id: albumBackground
                        anchors.fill: parent
                        color: Theme.surfaceContainer
                        radius: 20
                    }

                    Image {
                        id: albumArt
                        source: Interactions.currentSongCover.image
                        anchors.fill: parent
                        anchors.margins: 10
                        fillMode: Image.PreserveAspectFit
                        mipmap: true

                        onSourceChanged: {
                            console.log("Large album art changed")
                        }
                    }
                }

                // Song information
                ColumnLayout {
                    id: songInfo
                    Layout.fillWidth: true
                    spacing: 10

                    TextVariant.Header {
                        id: songTitle
                        text: root.song ? root.song.title : ""
                        color: Theme.onBackground
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                    }

                    TextVariant.SubHeader {
                        id: artistName
                        text: root.song ? root.song.artist : ""
                        color: Theme.onSurfaceVariant
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                    }
                }

                // Control buttons (larger versions)
                RowLayout {
                    id: controlButtons
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignCenter
                    spacing: 20

                    property int buttonSize: 60

                    Components.Button {
                        id: likeButtonLarge
                        isIcon: true
                        isTransparent: true
                        icon: AssetsPath + "icons/songbar/fav.svg"

                        Layout.preferredHeight: controlButtons.buttonSize
                        Layout.preferredWidth: controlButtons.buttonSize

                        onClicked: Interactions.like()
                        enabled: false
                    }

                    Components.Button {
                        id: backButtonLarge
                        isIcon: true
                        isTransparent: true
                        icon: AssetsPath + "icons/songbar/skip_previous.svg"

                        Layout.preferredHeight: controlButtons.buttonSize
                        Layout.preferredWidth: controlButtons.buttonSize
                        onClicked: Interactions.back()
                    }

                    Components.Button {
                        id: playButtonLarge
                        isIcon: true
                        icon: AssetsPath + "icons/songbar/play.svg"

                        Layout.preferredHeight: controlButtons.buttonSize + 20
                        Layout.preferredWidth: controlButtons.buttonSize + 20

                        states: [
                            State {
                                name: "playing"
                                when: Interactions.playingStatus == 0
                                PropertyChanges {
                                    target: playButtonLarge
                                    icon: AssetsPath + "icons/songbar/pause.svg"
                                }
                            },
                            State {
                                name: "paused"
                                when: Interactions.playingStatus == 1
                                PropertyChanges {
                                    target: playButtonLarge
                                    icon: AssetsPath + "icons/songbar/play.svg"
                                }
                            },
                            State {
                                name: "buffering"
                                when: Interactions.playingStatus == 2
                                PropertyChanges {
                                    target: playButtonLarge
                                    icon: AssetsPath + "icons/songbar/pending.svg"
                                }
                            },
                            State {
                                name: "stopped"
                                when: Interactions.playingStatus == 3
                                PropertyChanges {
                                    target: playButtonLarge
                                    icon: AssetsPath + "icons/songbar/close.svg"
                                }
                            },
                            State {
                                name: "error"
                                when: Interactions.playingStatus == 4
                                PropertyChanges {
                                    target: playButtonLarge
                                    icon: AssetsPath + "icons/songbar/close.svg"
                                }
                            }
                        ]

                        onClicked: Interactions.togglePlayback()
                    }

                    Components.Button {
                        id: nextButtonLarge
                        isIcon: true
                        isTransparent: true
                        icon: AssetsPath + "icons/songbar/skip_next.svg"

                        Layout.preferredHeight: controlButtons.buttonSize
                        Layout.preferredWidth: controlButtons.buttonSize
                        onClicked: Interactions.next()
                    }

                    Components.Button {
                        id: downloadButtonLarge
                        isIcon: true
                        isTransparent: true
                        icon: (root.song && root.song.downloadStatus == 2) ? AssetsPath + "icons/songbar/downloaded.svg" : 
                              (root.song && root.song.downloadStatus == 0) ? AssetsPath + "icons/songbar/download.svg" : 
                              AssetsPath + "icons/songbar/downloading.svg"

                        Layout.preferredHeight: controlButtons.buttonSize
                        Layout.preferredWidth: controlButtons.buttonSize
                        onClicked: Interactions.downloadSong(Interactions.currentSongId)

                        Components.ProgressBar {
                            id: downloadProgressLarge
                            anchors.fill: parent

                            vertical: false
                            input: false
                            fillColor: Utils.addAlpha("50", Theme.primary)
                            backgroundColor: "transparent"

                            radius: downloadButtonLarge.radius
                            percent: root.song ? root.song.downloadProgress : 0
                        }
                    }
                }

                // Progress bar and time
                ColumnLayout {
                    id: progressSection
                    Layout.fillWidth: true
                    spacing: 10

                    Components.ProgressBar {
                        id: songProgressLarge
                        Layout.fillWidth: true
                        Layout.preferredHeight: 15

                        vertical: false
                        fillColor: Theme.primary
                        backgroundColor: Theme.surfaceContainerLow

                        radius: 10
                        percent: Interactions.currentSongTime / Interactions.currentSongDuration * 100

                        onClick: (percent) => Interactions.seekPercent(percent)

                        Timer {
                            id: progressTimerLarge
                            interval: 150
                            running: true
                            repeat: true
                            onTriggered: {
                                songProgressLarge.percent = Interactions.currentSongTime / Interactions.currentSongDuration * 100
                            }
                        }
                    }

                    RowLayout {
                        id: timeDisplay
                        Layout.fillWidth: true

                        TextVariant.Default {
                            id: currentTimeLarge
                            text: Utils.secondsToHMS(Interactions.currentSongTime)
                            color: Theme.onBackground
                        }

                        Item {
                            Layout.fillWidth: true
                        }

                        TextVariant.Default {
                            id: durationTextLarge
                            text: Utils.secondsToHMS(Interactions.currentSongDuration)
                            color: Theme.onBackground
                        }
                    }
                }
            }

            // Right side - Lyrics
            ColumnLayout {
                id: rightColumn
                Layout.fillHeight: true
                Layout.fillWidth: true
                spacing: 15

                TextVariant.SectionHeader {
                    id: lyricsHeader
                    text: "Lyrics"
                    color: Theme.onBackground
                }

                ColObjs.ColRect {
                    id: lyricsContainer
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: Theme.surfaceContainer
                    radius: 15

                    ScrollView {
                        id: lyricsScrollView
                        anchors.fill: parent
                        anchors.margins: 20
                        clip: true

                        TextVariant.Default {
                            id: lyricsText
                            text: Interactions.currentLyrics
                            color: Theme.onSurface
                            wrapMode: Text.WordWrap
                            width: lyricsScrollView.width
                        }
                    }
                }
            }
        }
    }

    // Update timer for current time display
    Timer {
        id: timeTimer
        interval: 1000
        running: true
        repeat: true
        
        onTriggered: {
            currentTimeLarge.text = Utils.secondsToHMS(Interactions.currentSongTime)
            durationTextLarge.text = Utils.secondsToHMS(Interactions.currentSongDuration)
        }
    }

    // Load lyrics when song changes
    Connections {
        target: Interactions
        function onSongChanged() {
            console.log("Song changed, loading lyrics")
            Interactions.loadLyrics(Interactions.currentSongId)
        }
    }
    
    // Load lyrics on page load
    Component.onCompleted: {
        if (Interactions.currentSongId) {
            Interactions.loadLyrics(Interactions.currentSongId)
        }
    }
}