"""
Test script for MP3 to MIDI conversion functionality
"""

import os
import sys
import numpy as np
import pygame
import soundfile as sf
from mp3_to_midi_converter import MP3ToMIDIConverter

def generate_test_audio():
    """Generate a simple test audio file with known notes"""
    print("🎵 Generating test audio file...")
    
    sample_rate = 22050
    duration = 5.0  # 5 seconds
    
    # Generate a simple melody: C4, E4, G4, C5
    notes = [261.63, 329.63, 392.00, 523.25]  # Frequencies in Hz
    note_duration = duration / len(notes)
    
    audio = []
    
    for i, freq in enumerate(notes):
        t = np.linspace(0, note_duration, int(sample_rate * note_duration), False)
        
        # Generate a more complex waveform (piano-like)
        note_audio = (
            0.6 * np.sin(2 * np.pi * freq * t) +           # Fundamental
            0.3 * np.sin(2 * np.pi * freq * 2 * t) +       # 2nd harmonic
            0.2 * np.sin(2 * np.pi * freq * 3 * t) +       # 3rd harmonic
            0.1 * np.sin(2 * np.pi * freq * 4 * t)         # 4th harmonic
        )
        
        # Apply envelope (attack, decay, sustain, release)
        envelope = np.ones_like(note_audio)
        attack_samples = int(0.1 * sample_rate)
        release_samples = int(0.2 * sample_rate)
        
        # Attack
        if len(envelope) > attack_samples:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Release
        if len(envelope) > release_samples:
            envelope[-release_samples:] = np.linspace(1, 0, release_samples)
        
        note_audio *= envelope
        audio.extend(note_audio)
    
    # Convert to numpy array and normalize
    audio = np.array(audio)
    audio = audio / np.max(np.abs(audio)) * 0.7  # Normalize to 70% of max
    
    # Save as WAV file (easier than MP3 for testing)
    test_file = "test_melody.wav"
    sf.write(test_file, audio, sample_rate)
    
    print(f"✅ Test audio generated: {test_file}")
    print(f"   Duration: {duration:.1f}s, Sample Rate: {sample_rate}Hz")
    print(f"   Notes: C4, E4, G4, C5")
    
    return test_file

def test_conversion_algorithms():
    """Test all conversion algorithms"""
    print("\n🧪 Testing MP3 to MIDI Conversion Algorithms")
    print("=" * 50)
    
    # Generate test audio
    test_file = generate_test_audio()
    
    if not os.path.exists(test_file):
        print("❌ Failed to generate test audio file")
        return
    
    # Test each algorithm
    algorithms = ['chroma', 'cqt', 'onset']
    results = {}
    
    for algorithm in algorithms:
        print(f"\n🔬 Testing {algorithm.upper()} algorithm...")
        
        try:
            # Create converter with progress callback
            def progress_callback(progress, message):
                print(f"   Progress: {progress*100:.1f}% - {message}")
            
            converter = MP3ToMIDIConverter(progress_callback)
            
            # Convert
            output_file = f"test_output_{algorithm}.mid"
            success = converter.convert_mp3_to_midi(
                test_file, output_file, algorithm, tempo=120
            )
            
            if success and os.path.exists(output_file):
                # Analyze the output
                import mido
                midi_file = mido.MidiFile(output_file)
                
                note_count = 0
                for track in midi_file.tracks:
                    for msg in track:
                        if msg.type == 'note_on' and msg.velocity > 0:
                            note_count += 1
                
                results[algorithm] = {
                    'success': True,
                    'note_count': note_count,
                    'file_size': os.path.getsize(output_file)
                }
                
                print(f"   ✅ SUCCESS: Generated {note_count} notes")
                print(f"   📁 Output: {output_file} ({results[algorithm]['file_size']} bytes)")
                
            else:
                results[algorithm] = {'success': False, 'error': 'No output generated'}
                print(f"   ❌ FAILED: No output generated")
                
        except Exception as e:
            results[algorithm] = {'success': False, 'error': str(e)}
            print(f"   ❌ ERROR: {str(e)}")
    
    # Summary
    print(f"\n📊 CONVERSION TEST SUMMARY")
    print("=" * 50)
    
    for algorithm, result in results.items():
        if result['success']:
            print(f"✅ {algorithm.upper()}: {result['note_count']} notes generated")
        else:
            print(f"❌ {algorithm.upper()}: Failed - {result.get('error', 'Unknown error')}")
    
    # Cleanup
    cleanup_files = [test_file] + [f"test_output_{algo}.mid" for algo in algorithms]
    for file in cleanup_files:
        try:
            if os.path.exists(file):
                os.remove(file)
        except:
            pass
    
    print(f"\n🧹 Cleaned up test files")
    
    return results

def test_gui_integration():
    """Test GUI integration (import test)"""
    print("\n🖥️ Testing GUI Integration")
    print("=" * 30)
    
    try:
        from MIDI import MIDIGeneratorGUI, MP3_CONVERSION_AVAILABLE
        
        if MP3_CONVERSION_AVAILABLE:
            print("✅ MP3 conversion available in GUI")
            print("✅ All required libraries imported successfully")
            
            # Test creating converter instance
            converter = MP3ToMIDIConverter()
            print("✅ MP3ToMIDIConverter instance created successfully")
            
            return True
        else:
            print("⚠️ MP3 conversion not available - missing dependencies")
            return False
            
    except Exception as e:
        print(f"❌ GUI integration test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🎼 MP3 to MIDI Converter Test Suite")
    print("=" * 40)
    
    # Check dependencies
    print("📦 Checking dependencies...")
    
    try:
        import librosa
        print("✅ librosa available")
    except ImportError:
        print("❌ librosa not available - install with: pip install librosa")
        return
    
    try:
        import soundfile
        print("✅ soundfile available")
    except ImportError:
        print("❌ soundfile not available - install with: pip install soundfile")
        return
    
    print("✅ All dependencies available")
    
    # Test conversion algorithms
    conversion_results = test_conversion_algorithms()
    
    # Test GUI integration
    gui_success = test_gui_integration()
    
    # Final summary
    print(f"\n🎯 FINAL TEST RESULTS")
    print("=" * 40)
    
    successful_algorithms = sum(1 for result in conversion_results.values() if result['success'])
    total_algorithms = len(conversion_results)
    
    print(f"Conversion algorithms: {successful_algorithms}/{total_algorithms} working")
    print(f"GUI integration: {'✅ Working' if gui_success else '❌ Failed'}")
    
    if successful_algorithms == total_algorithms and gui_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("MP3 to MIDI conversion is fully operational!")
    else:
        print("\n⚠️ Some tests failed - check output above for details")

if __name__ == "__main__":
    main()
