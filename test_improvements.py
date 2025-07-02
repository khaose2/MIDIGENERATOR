#!/usr/bin/env python3
"""
Test script for MP3 to MIDI converter improvements
"""

import sys
import os
import numpy as np
import librosa
from mp3_to_midi_converter import MP3ToMIDIConverter

def create_test_audio():
    """Create a simple test audio signal"""
    print("🎵 Creating test audio signal...")
    
    # Create a simple melody with multiple notes
    sr = 22050
    duration = 5.0  # 5 seconds
    t = np.linspace(0, duration, int(sr * duration))
    
    # Notes: C4, E4, G4, C5 (major chord arpeggio)
    freqs = [261.63, 329.63, 392.00, 523.25]  # C4, E4, G4, C5
    
    # Create melody with each note lasting 1 second
    y = np.zeros_like(t)
    
    for i, freq in enumerate(freqs):
        start_time = i * 1.0
        end_time = (i + 1) * 1.0
        
        # Create indices for this note's duration
        start_idx = int(start_time * sr)
        end_idx = int(end_time * sr)
        
        if end_idx <= len(t):
            # Generate sine wave for this note
            note_t = t[start_idx:end_idx]
            note_signal = 0.5 * np.sin(2 * np.pi * freq * note_t)
            
            # Add envelope to avoid clicks
            envelope = np.ones_like(note_signal)
            fade_samples = int(0.05 * sr)  # 50ms fade
            envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
            envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
            
            y[start_idx:end_idx] = note_signal * envelope
    
    # Add some harmonics for more realistic sound
    for harmonic in [2, 3]:
        y_harmonic = np.zeros_like(t)
        for i, freq in enumerate(freqs):
            start_time = i * 1.0
            end_time = (i + 1) * 1.0
            start_idx = int(start_time * sr)
            end_idx = int(end_time * sr)
            
            if end_idx <= len(t):
                note_t = t[start_idx:end_idx]
                harmonic_signal = 0.2 * np.sin(2 * np.pi * freq * harmonic * note_t)
                envelope = np.ones_like(harmonic_signal)
                fade_samples = int(0.05 * sr)
                envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
                envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
                y_harmonic[start_idx:end_idx] = harmonic_signal * envelope
        
        y += y_harmonic
    
    # Normalize
    y = y / np.max(np.abs(y))
    
    return y, sr

def test_algorithm(converter, algorithm_name, y, sr):
    """Test a specific algorithm"""
    print(f"\n🔍 Testing {algorithm_name} algorithm...")
    
    try:
        # Store audio for onset detection
        converter.y = y
        converter.sr = sr
        
        if algorithm_name == 'chroma':
            chroma, times = converter.extract_pitch_chroma(y, sr)
            notes = converter.chroma_to_midi_notes(chroma, times)
        elif algorithm_name == 'cqt':
            cqt, times = converter.extract_pitch_cqt(y, sr)
            notes = converter.cqt_to_midi_notes(cqt, times)
        elif algorithm_name == 'onset':
            onset_times, f0_times, f0, voiced_flag = converter.extract_pitch_onset(y, sr)
            notes = converter.onset_to_midi_notes(onset_times, f0_times, f0, voiced_flag)
        else:
            print(f"❌ Unknown algorithm: {algorithm_name}")
            return False
        
        # Post-process notes
        notes = converter.post_process_notes(notes)
        
        print(f"✅ {algorithm_name} algorithm: {len(notes)} notes detected")
        
        if notes:
            # Show first few notes
            print(f"   First 3 notes:")
            for i, note in enumerate(notes[:3]):
                midi_note = note['note']
                note_name = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][midi_note % 12]
                octave = midi_note // 12 - 1
                print(f"   Note {i+1}: {note_name}{octave} (MIDI {midi_note}) at {note['start']:.2f}s, dur={note['duration']:.2f}s, vel={note['velocity']}")
            
            # Create MIDI file
            midi_file = converter.create_midi_file(notes)
            output_path = f"test_output_{algorithm_name}.mid"
            midi_file.save(output_path)
            print(f"   💾 MIDI saved to: {output_path}")
            
            return True
        else:
            print(f"❌ {algorithm_name} algorithm: No notes detected")
            return False
            
    except Exception as e:
        print(f"❌ {algorithm_name} algorithm failed: {str(e)}")
        return False

def test_fallback_generation(converter, y, sr):
    """Test fallback note generation"""
    print(f"\n🆘 Testing fallback note generation...")
    
    try:
        notes = converter._generate_fallback_notes(y, sr)
        print(f"✅ Fallback generation: {len(notes)} notes created")
        
        if notes:
            # Show first few notes
            print(f"   First 3 notes:")
            for i, note in enumerate(notes[:3]):
                midi_note = note['note']
                note_name = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][midi_note % 12]
                octave = midi_note // 12 - 1
                print(f"   Note {i+1}: {note_name}{octave} (MIDI {midi_note}) at {note['start']:.2f}s, dur={note['duration']:.2f}s, vel={note['velocity']}")
            
            # Create MIDI file
            midi_file = converter.create_midi_file(notes)
            output_path = f"test_output_fallback.mid"
            midi_file.save(output_path)
            print(f"   💾 MIDI saved to: {output_path}")
            
            return True
        else:
            print(f"❌ Fallback generation: No notes created")
            return False
            
    except Exception as e:
        print(f"❌ Fallback generation failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🎼 MP3 to MIDI Converter - Improvement Testing")
    print("=" * 50)
    
    # Create test audio
    y, sr = create_test_audio()
    print(f"✅ Test audio created: {len(y)/sr:.1f}s duration, {sr}Hz sample rate")
    
    # Initialize converter with higher sensitivity
    def progress_callback(progress, message):
        print(f"   Progress: {progress*100:.0f}% - {message}")
    
    converter = MP3ToMIDIConverter(progress_callback=progress_callback)
    converter.sensitivity = 0.8  # High sensitivity for testing
    converter.max_polyphony = 6  # Allow more notes
    
    # Test each algorithm
    algorithms = ['chroma', 'cqt', 'onset']
    results = {}
    
    for algorithm in algorithms:
        results[algorithm] = test_algorithm(converter, algorithm, y, sr)
    
    # Test fallback generation
    results['fallback'] = test_fallback_generation(converter, y, sr)
    
    # Test full conversion with auto-selection
    print(f"\n🤖 Testing full conversion with auto algorithm selection...")
    
    # Save test audio as WAV for full conversion test
    import soundfile as sf
    test_wav_path = "test_audio.wav"
    sf.write(test_wav_path, y, sr)
    print(f"   Test audio saved to: {test_wav_path}")
    
    # Try full conversion
    try:
        success = converter.convert_mp3_to_midi(test_wav_path, "test_output_full.mid", "auto")
        if success:
            print(f"✅ Full conversion successful!")
            results['full_conversion'] = True
        else:
            print(f"❌ Full conversion failed")
            results['full_conversion'] = False
    except Exception as e:
        print(f"❌ Full conversion error: {str(e)}")
        results['full_conversion'] = False
    
    # Summary
    print(f"\n📊 Test Results Summary:")
    print("=" * 30)
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:15} : {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.0f}%)")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! The improvements are working correctly.")
    elif passed_tests > 0:
        print("⚠️  Some tests passed. The improvements are partially working.")
    else:
        print("🚨 No tests passed. There may be issues with the improvements.")
    
    # Cleanup
    try:
        os.remove(test_wav_path)
        print(f"\n🧹 Cleaned up test file: {test_wav_path}")
    except:
        pass

if __name__ == "__main__":
    main()
