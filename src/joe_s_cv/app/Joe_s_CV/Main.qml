import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Joe_s_CV

ApplicationWindow {
    id: window
    visible: true
    width: 1024
    height: 768
    color: Config.bg

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Sidebar {
            id: sideNav
            Layout.fillHeight: true
            
            Layout.preferredWidth: sideNav.collapsed ? 60 : 220
            
            Behavior on Layout.preferredWidth {
                NumberAnimation { duration: 200; easing.type: Easing.InOutQuad }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            TabBar {
                id: bar
                Layout.fillWidth: true
                background: Rectangle { color: "#191a21" }

                Repeater {
                    model: Backend.activeTabs
                    TabButton {
                        width: 150
                        text: modelData.company || "Unnamed"
                    }
                }
            }

            StackLayout {
                currentIndex: bar.currentIndex
                Layout.fillWidth: true
                Layout.fillHeight: true

                Repeater {
                    model: Backend.activeTabs
                    JobEditor {
                        jobIndex: index
                        jobData: modelData
                    }
                }
            }
        }
    }
}
