// Color+Extensions.swift
import SwiftUI

extension Color {
    static var customBackground: Color {
        Color(NSColor.windowBackgroundColor)
    }
    
    static var secondaryBackground: Color {
        Color(NSColor.controlBackgroundColor)
    }
    
    static var tertiaryBackground: Color {
        Color(NSColor.textBackgroundColor)
    }
    
    static var primaryText: Color {
        Color(NSColor.labelColor)
    }
    
    static var secondaryText: Color {
        Color(NSColor.secondaryLabelColor)
    }
    
    static var tertiaryText: Color {
        Color(NSColor.tertiaryLabelColor)
    }
    
    static var accentColor: Color {
        Color.blue
    }
    
    // Add more system colors as needed
}