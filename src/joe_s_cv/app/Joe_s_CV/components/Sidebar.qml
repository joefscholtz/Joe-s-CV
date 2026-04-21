import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Joe_s_CV

Rectangle {
    id: root
    color: Config.sidebarBg

    // Signals to communicate with Main
    property bool collapsed: false
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 15

        // Header & Toggle
        RowLayout {
            Layout.fillWidth: true
            Text {
                text: "JOE_CV"
                color: Config.accent
                font.bold: true
                visible: !root.collapsed
            }
            Item { Layout.fillWidth: true }
            Button {
                text: root.collapsed ? "󰍜" : "󰍛"
                width: root.collapsed ? 10 : 200
                flat: true
                onClicked: root.collapsed = !root.collapsed
                palette.buttonText: "white"
            }
        }

        Rectangle { 
            Layout.fillWidth: true; 
            height: 1; 
            color: "#44475a"; 
            visible: !root.collapsed 
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 10

            Button {
                text: root.collapsed ? "󰐕" : "󰐕 New Job"
                Layout.fillWidth: true
                onClicked: Backend.createNewJob()
            }
            
            Repeater {
                model: ["󰄛 Processing", " Database", "⚙ Settings"]
                Button {
                    Layout.fillWidth: true
                    flat: true
                    contentItem: Text {
                        text: root.collapsed ? modelData[0] : modelData
                        color: "white"
                        font.pixelSize: 14
                        horizontalAlignment: root.collapsed ? Text.AlignHCenter : Text.AlignLeft
                    }
                }
            }
        }

        Item { Layout.fillHeight: true } // Bottom Spacer
    }
}
