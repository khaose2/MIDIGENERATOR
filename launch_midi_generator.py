#!/usr/bin/env python3
"""
Launch script for the Ultimate MIDI Generator
Run this file to start the full application
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Launch the MIDI Generator application"""
    try:
        print("🎵 Starting Ultimate MIDI Generator - Professional Edition")
        print("Please wait while the application loads...")
        
        # Import and create the application
        import MIDI
        app = MIDI.MIDIGeneratorGUI()
        
        print("✅ Application loaded successfully!")
        print("🎹 Ready to generate music!")
        
        # Start the GUI event loop
        if hasattr(app, 'root') and app.root:
            app.root.mainloop()
        else:
            print("❌ Error: GUI initialization failed - no root window found")
            raise RuntimeError("GUI initialization failed")
        
    except KeyboardInterrupt:
        print("\n👋 Application closed by user")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please make sure all dependencies are installed:")
        print("pip install pygame mido numpy matplotlib tkinter")
    except Exception as e:
        print(f"❌ Application error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
