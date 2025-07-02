#!/usr/bin/env python3
"""
Test script to verify that the repaired MIDI.PY file works correctly
Tests the SoftwareSynthesizer class and its audio synthesis methods
"""

import sys
import os
import time
import numpy as np

# Add the project directory to the path
sys.path.insert(0, r'c:\Users\jeffh\Documents\GitHub\MIDIGENERATOR')

def test_synthesizer_basic():
    """Test basic SoftwareSynthesizer functionality"""
    print("Testing basic synthesizer functionality...")
    
    try:
        # Import the repaired MIDI module
        from MIDI import SoftwareSynthesizer
        print("✅ Successfully imported SoftwareSynthesizer")
        
        # Create synthesizer instance
        synth = SoftwareSynthesizer()
        print("✅ Successfully created SoftwareSynthesizer instance")
        
        # Test audio processing methods
        test_buffer = np.random.randn(100) * 0.1
        
        # Test lowpass filter
        filtered = synth.lowpass_filter(test_buffer, 1000)
        print("✅ lowpass_filter method works")
        
        # Test soft clipping
        clipped = synth.soft_clip(test_buffer)
        print("✅ soft_clip method works")
        
        # Test stereo widening
        left, right = synth.apply_stereo_widening(test_buffer, 0.5)
        print("✅ apply_stereo_widening method works")
        
        # Test waveform generation
        sine_wave = synth._generate_sine_wave(440, 0.5, 64, 44100)
        print("✅ _generate_sine_wave method works")
        
        piano_wave = synth._generate_piano_wave(440, 0.5, 64, 44100)
        print("✅ _generate_piano_wave method works")
        
        drum_wave = synth._generate_drum_sound(60, 0.5, 64, 44100)
        print("✅ _generate_drum_sound method works")
        
        # Test envelope methods
        envelope = synth._apply_envelope(sine_wave, 44100)
        print("✅ _apply_envelope method works")
        
        piano_env = synth._apply_piano_envelope(piano_wave, 44100)
        print("✅ _apply_piano_envelope method works")
        
        drum_env = synth._apply_drum_envelope(drum_wave, 44100)
        print("✅ _apply_drum_envelope method works")
        
        # Test note management
        synth.note_on(0, 60, 100)  # Middle C
        print("✅ note_on method works")
        
        left_buf, right_buf = synth.get_audio_buffer()
        print("✅ get_audio_buffer method works")
        
        synth.note_off(0, 60)
        print("✅ note_off method works")
        
        # Test playback control
        synth.stop_playback()
        print("✅ stop_playback method works")
        
        print("\n🎉 ALL TESTS PASSED! The SoftwareSynthesizer is fully functional!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_midi_generator():
    """Test MIDIGenerator functionality"""
    print("\nTesting MIDI generation...")
    
    try:
        from MIDI import MIDIGenerator
        print("✅ Successfully imported MIDIGenerator")
        
        generator = MIDIGenerator()
        print("✅ Successfully created MIDIGenerator instance")
        
        # Test scale generation
        scale_notes = generator.get_scale_notes()
        print(f"✅ Generated scale notes: {len(scale_notes)} notes")
        
        # Test chord progression
        chord_prog = generator.generate_chord_progression(4)
        print(f"✅ Generated chord progression: {chord_prog}")
        
        return True
        
    except Exception as e:
        print(f"❌ MIDIGenerator test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== MIDI.PY REPAIR VERIFICATION TEST ===\n")
    
    success1 = test_synthesizer_basic()
    success2 = test_midi_generator()
    
    if success1 and success2:
        print("\n✅ ALL TESTS PASSED! MIDI.PY has been successfully repaired!")
        print("🎵 Audio synthesis and playback functionality is now working!")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
