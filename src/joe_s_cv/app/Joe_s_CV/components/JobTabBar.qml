import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Joe_s_CV

ColumnLayout {
    Layout.fillWidth: true
    Layout.fillHeight: true
    spacing: 0

    property var tabModel: [
        {
            icon: "󰷉",
            label: "Tab 1"
        },
        {
            icon: "",
            label: "Tab 2"
        }
    ]

    RowLayout {
        Layout.fillWidth: true
        spacing: 0

        Rectangle {
            z: -1
            anchors.fill: parent
            color: Config.bg
        }

        TabBar {
            id: bar
            background: Rectangle {
                color: "transparent"
            }

            Repeater {
                model: tabModel
                TabButton {
                    width: 150
                    text: modelData.icon + "  " + modelData.label
                }
            }
        }

        MyButton {
            text: "󰐕"
            Layout.preferredWidth: 40
            Layout.preferredHeight: 35
            // onClicked: Backend.createNewJob()
        }

        Item {
            Layout.fillWidth: true
        }
    }

    StackLayout {
        currentIndex: bar.currentIndex
        Layout.fillWidth: true
        Layout.fillHeight: true

        Repeater {
            model: tabModel
            JobEditor {
                jobIndex: index
                jobData: modelData
            }
        }
    }
}
