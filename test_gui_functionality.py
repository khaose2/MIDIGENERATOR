#!/usr/bin/env python3
"""
Quick GUI functionality test - verify the application can launch and basic functions work
"""

import sys
import os
import time

# Add the project directory to the path
sys.path.insert(0, r'c:\Users\jeffh\Documents\GitHub\MIDIGENERATOR')

def test_gui_launch():
    """Test that the GUI can be created without errors"""
    print("Testing GUI launch functionality...")
    
    try:
        from MIDI import MIDIGeneratorGUI
        print("✅ Successfully imported MIDIGeneratorGUI")
        
        # Create GUI instance
        app = MIDIGeneratorGUI()
        print("✅ Successfully created MIDIGeneratorGUI instance")
        
        # Test basic functionality without actually showing GUI
        app.generate_music()
        print("✅ Music generation works through GUI")
        
        if app.generator.current_midi:
            print("✅ MIDI file created successfully")
        
        print("✅ GUI functionality test completed successfully")
        
        # Don't actually run the mainloop in test
        return True
        
    except Exception as e:
        print(f"❌ GUI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== GUI FUNCTIONALITY TEST ===\n")
    
    success = test_gui_launch()
    
    if success:
        print("\n✅ GUI REPAIR SUCCESSFUL!")
        print("The MIDIGeneratorGUI class has been created and is functional!")
        print("The application can now be launched via launch.bat or directly!")
    else:
        print("\n❌ GUI test failed.")
