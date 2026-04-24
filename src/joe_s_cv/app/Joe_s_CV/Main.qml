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
                NumberAnimation {
                    duration: 200
                    easing.type: Easing.InOutQuad
                }
            }
        }

        JobTabBar {}
    }
}
