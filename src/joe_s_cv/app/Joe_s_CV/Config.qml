pragma Singleton
import QtQuick

QtObject {
    readonly property color bg: "#282a36"
    readonly property color fg: "#f8f8f2"
    readonly property color darkerBg: "#21222c"
    readonly property color accent: "#bd93f9"
    readonly property color draculaGreen: "#50fa7b"
    readonly property color draculaRed: "#ff5555"
    readonly property color draculaPink: "#ff79c6"
    
    readonly property int paddingLarge: 30
    readonly property int paddingSmall: 15
    
    
    readonly property font monoFont: Qt.font({ family: "JetBrainsMono Nerd Font Mono", pixelSize: 13 })
}
