import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Joe_s_CV

Rectangle {
    id: root
    color: "transparent"

    property int jobIndex: 0
    property var jobData: ({})

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Config.paddingLarge

        Text {
            // text: "Editing: " + (root.jobData.company || "New Job")
            color: "white"
            font.pixelSize: 18
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#282a36"
            border.color: "#44475a"
            radius: 8

            Text {
                anchors.centerIn: parent
                text: "Editor Content for Tab " + root.jobIndex
                color: "#6272a4"
            }
        }
    }
}
