import QtWebView
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.platform
import QtQuick.Effects

import "../components/text" as TextVariant

Item {
    id: root
    anchors.fill: parent
    Connections{
        target: Backend

        onLoginRedirect: {
            webView.stop()
            webView.url = "https://music.youtube.com/library"
        }

        onLoginComplete: {
            completeText.visible = true
            webView.visible = false
            webView.stop()
            
        }
    }
    WebView {
        id: webView
        visible: true
        anchors.fill: parent
        url: "https://accounts.google.com/v3/signin/identifier?continue=https%3A%2F%2Fwww.youtube.com%2Fsignin%3Faction_handle_signin%3Dtrue%26app%3Ddesktop%26hl%3Den%26next%3Dhttps%253A%252F%252Fmusic.youtube.com%252Flibrary%26feature%3D__FEATURE__&hl=en&ifkv=ASSHykoIoNWrBJA_60xXvbvK8CES7tKrSjxPtapDxo0uSDlsPifPymeU1q-hiq6is2MTEclqMyd6&ltmpl=music&passive=true&service=youtube&uilel=3&flowName=GlifWebSignIn&flowEntry=ServiceLogin&dsh=S-79958273%3A1741527185220824&ddm=1"
        /* I don't see a token or anything that would make this URL expire, but if login breaks check here first lol */
    }
    TextVariant.Header {
        id: completeText
        visible: false
        text: "Login Complete, Restart application to apply changes"
        anchors.centerIn: parent
        BusyIndicator {
            running: true
            anchors.top: completeText.bottom
            width: 50
            height: 50
        }
    }
}