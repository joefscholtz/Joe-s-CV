pragma Singleton
import QtQuick

QtObject {
    readonly property color bg: "#282a36"
    readonly property color sidebarBg: "#21222c"
    readonly property color accent: "#bd93f9"
    readonly property color draculaGreen: "#50fa7b"
    
    readonly property int paddingLarge: 30
    readonly property int paddingSmall: 15
    
    readonly property font monoFont: Qt.font({ family: "Fira Code", pixelSize: 13 })
}
