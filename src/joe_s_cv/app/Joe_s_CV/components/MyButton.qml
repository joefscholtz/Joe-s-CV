import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Joe_s_CV

Button {
    id: button
    width: 100
    Layout.preferredWidth: 100
    height: 30
    Layout.preferredHeight: 30
    flat: true
    
    contentItem: Text {
        text: button.text
        font.pixelSize: 14
        font.bold: false
        color: hoverHandler.hovered ? Config.accent : Config.fg
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    background: Rectangle {
        anchors.fill: parent 
        
        // color: hoverHandler.hovered ? Config.draculaPink : Config.bg
        color: Config.bg
        // border.color: Config.bg
        border.width: 0
        radius: 4
    }

    HoverHandler {
        id: hoverHandler
        cursorShape: Qt.PointingHandCursor
    }
}
