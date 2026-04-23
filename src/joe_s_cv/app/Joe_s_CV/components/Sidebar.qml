import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Joe_s_CV

Rectangle {
    id: root
    color: Config.darkerBg

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
                text: "Joe's CV"
                color: Config.accent
                font.bold: true
                visible: !root.collapsed
            }
            Item { 
              Layout.fillWidth: true
              visible: !root.collapsed
            }
            MyButton {
                text: "󰍜 "
                Layout.preferredWidth: 50
                Layout.fillWidth: root.collapsed ? true : false
                onClicked: root.collapsed = !root.collapsed
            }
        }

        Rectangle { 
            Layout.fillWidth: true
            height: 1
            color: Config.fg
            // visible: !root.collapsed 
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 10

            // MyButton {
            //     text: root.collapsed ? "󰐕" : "󰐕 New Job"
            //     Layout.fillWidth: true
            //     // onClicked: Backend.createNewJob()
            // }
            
            Repeater {
                model: [
                        { icon: "󰷉", label: "Processing" },
                        { icon: " ", label: "Database" },
                        // { icon: "", label: "Settings" }
                    ]
                MyButton {
                    Layout.fillWidth: true
                    text: root.collapsed ? modelData.icon : modelData.icon + "  " + modelData.label
                }
            }
        }

        Item { Layout.fillHeight: true } // Bottom Spacer

        MyButton {
            text: root.collapsed ? " " : "  Settings"
            Layout.fillWidth: true
        }

    }
}
