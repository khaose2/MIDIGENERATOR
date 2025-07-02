#!/usr/bin/env python3
"""
Test the digital keyboard integration
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_digital_keyboard():
    """Test the digital keyboard integration"""
    print("🎹 Testing Digital Keyboard Integration...")
    
    try:
        # Test importing the modules
        from software_synthesizer import SoftwareSynthesizer
        print("✅ SoftwareSynthesizer imported successfully")
        
        from digital_keyboard import DigitalKeyboard, DigitalKeyboardWindow
        print("✅ DigitalKeyboard imported successfully")
        
        # Create a test window
        root = tk.Tk()
        root.title("Digital Keyboard Test")
        root.geometry("900x600")
        
        # Create synthesizer
        synthesizer = SoftwareSynthesizer()
        print("✅ SoftwareSynthesizer initialized")
        
        # Create digital keyboard
        keyboard = DigitalKeyboard(root, synthesizer)
        print("✅ DigitalKeyboard initialized")
        
        # Add instructions
        info_frame = tk.Frame(root, bg="#e8f4f8")
        info_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(info_frame, text="🎹 Digital Keyboard Test", 
                font=("Arial", 14, "bold"), bg="#e8f4f8").pack()
        
        tk.Label(info_frame, 
                text="Use computer keyboard keys (a,s,d,f,g,h,j,k for white keys, w,e,t,y,u for black keys)\n"
                     "Or click piano keys with mouse. Test the controls below!",
                font=("Arial", 10), bg="#e8f4f8", justify="center").pack(pady=5)
        
        # Test passed
        print("✅ All tests passed! Digital Keyboard is ready.")
        
        # Run the test
        root.mainloop()
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        messagebox.showerror("Import Error", f"Failed to import required modules:\n{e}")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        messagebox.showerror("Error", f"Digital Keyboard test failed:\n{e}")
        return False
    
    return True

def test_standalone_keyboard():
    """Test the standalone keyboard window"""
    print("🎹 Testing Standalone Digital Keyboard...")
    
    try:
        from digital_keyboard import DigitalKeyboardWindow
        
        # Create standalone keyboard
        app = DigitalKeyboardWindow()
        print("✅ Standalone Digital Keyboard created")
        
        # Run it
        app.run()
        
    except Exception as e:
        print(f"❌ Standalone keyboard error: {e}")
        messagebox.showerror("Error", f"Standalone keyboard failed:\n{e}")

if __name__ == "__main__":
    print("🎵 Digital Keyboard Integration Test")
    print("=" * 50)
    
    # Check which test to run
    if len(sys.argv) > 1 and sys.argv[1] == "standalone":
        test_standalone_keyboard()
    else:
        test_digital_keyboard()
