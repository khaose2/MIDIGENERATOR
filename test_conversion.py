#!/usr/bin/env python3
"""
Test script for MP3 to MIDI conversion functionality
"""

import os
import sys

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from mp3_to_midi_converter import MP3ToMIDIConverter, convert_mp3_to_midi_simple
        print("✅ MP3ToMIDIConverter imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import MP3ToMIDIConverter: {e}")
        return False
    
    try:
        from MIDI import MIDIGeneratorGUI, MIDIGenerator
        print("✅ MIDI classes imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import MIDI classes: {e}")
        return False
    
    return True

def test_converter_creation():
    """Test if converter can be created"""
    print("\n🧪 Testing converter creation...")
    
    try:
        from mp3_to_midi_converter import MP3ToMIDIConverter
        
        def dummy_callback(progress, message):
            print(f"Progress: {progress:.1%} - {message}")
        
        converter = MP3ToMIDIConverter(dummy_callback)
        print("✅ MP3ToMIDIConverter created successfully")
        
        # Test settings
        converter.sensitivity = 0.5
        converter.min_duration = 0.1
        print("✅ Converter settings applied successfully")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create converter: {e}")
        return False

def test_midi_generator():
    """Test if MIDI generator works"""
    print("\n🧪 Testing MIDI generator...")
    
    try:
        from MIDI import MIDIGenerator
        
        generator = MIDIGenerator()
        print("✅ MIDIGenerator created successfully")
        
        # Test creating some demo notes
        demo_notes = [
            {'note': 60, 'start': 0.0, 'duration': 0.5, 'velocity': 80, 'channel': 0},
            {'note': 64, 'start': 0.5, 'duration': 0.5, 'velocity': 80, 'channel': 0},
            {'note': 67, 'start': 1.0, 'duration': 0.5, 'velocity': 80, 'channel': 0},
        ]
        
        generator.notes_data = demo_notes
        midi_file = generator.create_midi_file(demo_notes)
        
        if midi_file:
            print("✅ MIDI file creation successful")
            return True
        else:
            print("❌ MIDI file creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test MIDI generator: {e}")
        return False

def main():
    """Run all tests"""
    print("🎵 MP3 to MIDI Converter Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_converter_creation,
        test_midi_generator,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your MP3 to MIDI converter is ready to use!")
        print("\n💡 To use the converter:")
        print("1. Run 'python MIDI.PY' to start the GUI")
        print("2. Go to the 'Creative' tab")
        print("3. Click 'Load MP3 File' to convert an audio file")
        return True
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
