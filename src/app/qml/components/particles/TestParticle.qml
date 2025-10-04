import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Effects

import "." as Particles

Item {
    width: 500
    height: 500

    Particles.SideGlow {
        anchors.fill: parent
    }
}
