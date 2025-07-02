#!/usr/bin/env python3
"""
MP3 to MIDI Conversion Demo
Test the complete conversion workflow
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_conversion():
    """Demo MP3 to MIDI conversion with file dialog"""
    print("🎵 MP3 to MIDI Conversion Demo")
    
    # Create root window (hidden)
    root = tk.Tk()
    root.withdraw()
    
    try:
        # Import the converter
        from mp3_to_midi_converter import MP3ToMIDIConverter
        
        # Ask user to select an MP3 file
        mp3_file = filedialog.askopenfilename(
            title="Select MP3 file for conversion",
            filetypes=[
                ("Audio files", "*.mp3 *.wav *.m4a *.aac"),
                ("MP3 files", "*.mp3"),
                ("All files", "*.*")
            ]
        )
        
        if not mp3_file:
            print("No file selected. Demo cancelled.")
            return
        
        print(f"Selected file: {os.path.basename(mp3_file)}")
        
        # Create output path
        output_dir = os.path.dirname(mp3_file)
        base_name = os.path.splitext(os.path.basename(mp3_file))[0]
        output_file = os.path.join(output_dir, f"{base_name}_converted.mid")
        
        # Progress callback
        def progress_callback(progress, message):
            print(f"Progress: {progress:.1%} - {message}")
        
        # Create converter
        converter = MP3ToMIDIConverter(progress_callback)
        
        # Ask for conversion settings
        print("\nConversion Settings:")
        print("1. Melodia (onset) - Best for melodies")
        print("2. Multi-pitch (chroma) - Better for chords")
        print("3. Neural (auto) - Automatic algorithm selection")
        
        choice = input("Choose algorithm (1-3, default=3): ").strip()
        
        algorithm_map = {
            '1': 'onset',
            '2': 'chroma',
            '3': 'auto'
        }
        
        algorithm = algorithm_map.get(choice, 'auto')
        
        print(f"\nStarting conversion with {algorithm} algorithm...")
        
        # Perform conversion
        if algorithm == 'auto':
            result = converter.convert_with_auto_algorithm(mp3_file, output_file)
            success = result.get('success', False)
            if success:
                print(f"✅ Auto-conversion successful using {result.get('algorithm_used')} algorithm")
                analysis = result.get('analysis', {})
                if analysis:
                    print(f"   Detected tempo: {analysis.get('tempo', 'Unknown')} BPM")
                    print(f"   Harmonic ratio: {analysis.get('harmonic_ratio', 0):.2f}")
        else:
            success = converter.convert_mp3_to_midi(mp3_file, output_file, algorithm)
        
        if success:
            print(f"✅ Conversion complete!")
            print(f"📁 MIDI file saved to: {output_file}")
            
            # Ask if user wants to test in GUI
            test_gui = input("\nWould you like to test the GUI? (y/n): ").strip().lower()
            if test_gui == 'y':
                print("Starting GUI...")
                from MIDI import MIDIGeneratorGUI
                app = MIDIGeneratorGUI()
                # Load the converted file automatically
                app.generator.load_midi_file(output_file)
                app.update_visualization()
                print("GUI started with converted MIDI loaded!")
                app.root.mainloop()
        else:
            print("❌ Conversion failed. Check the console for error messages.")
            
    except ImportError as e:
        messagebox.showerror("Missing Dependencies", 
                           f"Required libraries not found: {e}\n\n"
                           "Please install: pip install librosa soundfile numpy scipy")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        root.destroy()

if __name__ == "__main__":
    demo_conversion()
