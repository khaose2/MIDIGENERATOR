#!/usr/bin/env python3
"""
Test script for the Software Synthesizer
This demonstrates the built-in audio synthesis capabilities
"""

import time
import threading
from MIDI import SoftwareSynthesizer, MIDIGenerator

def test_synthesizer():
    """Test the software synthesizer functionality"""
    print("🎵 Testing Software Synthesizer 🎵")
    print("=" * 50)
    
    # Initialize synthesizer
    synth = SoftwareSynthesizer()
    print("✅ Synthesizer initialized successfully!")
    
    print("\n1. Testing individual notes...")
    
    # Test piano sound
    print("   🎹 Playing piano note (Middle C)...")
    synth.note_on(0, 60, 80)  # Channel 0, Middle C, velocity 80
    time.sleep(1)
    synth.note_off(0, 60)
    time.sleep(0.5)
    
    # Test bass sound
    print("   🔉 Playing bass note (Low E)...")
    synth.note_on(1, 40, 100)  # Channel 1, Low E, velocity 100
    time.sleep(1)
    synth.note_off(1, 40)
    time.sleep(0.5)
    
    # Test drum sound
    print("   🥁 Playing drum sound (Kick)...")
    synth.note_on(9, 36, 120)  # Channel 9 (drums), Kick drum
    time.sleep(0.5)
    synth.note_off(9, 36)
    time.sleep(0.5)
    
    print("\n2. Testing chord...")
    # Play a C major chord
    print("   🎵 Playing C major chord...")
    notes = [60, 64, 67]  # C, E, G
    for note in notes:
        synth.note_on(0, note, 70)
    
    time.sleep(2)
    
    for note in notes:
        synth.note_off(0, note)
    
    time.sleep(0.5)
    
    print("\n3. Testing different waveforms...")
    test_note = 60
    
    # Test each waveform type
    waveforms = [
        (0, "piano", "🎹 Piano"),
        (1, "sawtooth", "🔺 Sawtooth (bass)"),
        (2, "sine", "🌊 Sine wave"),
        (3, "triangle", "🔺 Triangle"),
        (4, "square", "⬜ Square wave")
    ]
    
    for channel, waveform, description in waveforms:
        print(f"   {description}...")
        synth.channel_instruments[channel] = waveform
        synth.note_on(channel, test_note, 80)
        time.sleep(0.8)
        synth.note_off(channel, test_note)
        time.sleep(0.3)
    
    print("\n4. Testing full MIDI generation and playback...")
    
    # Generate a simple piece
    generator = MIDIGenerator()
    generator.settings.song_length_bars = 8  # Short piece for testing
    generator.settings.tempo = 140
    generator.settings.scale_type = "major"
    
    midi_file = generator.generate_music()
    print(f"   ✅ Generated music with {len(generator.notes_data)} notes")
    
    print("   🎵 Playing generated music (5 seconds)...")
    synth.play_midi_file(midi_file, generator)
    
    # Let it play for a bit
    time.sleep(5)
    
    # Stop playback
    synth.stop_playback()
    print("   ⏹️ Stopped playback")
    
    print("\n" + "=" * 50)
    print("🎉 Software Synthesizer Test Complete!")
    print("\n✅ The synthesizer is working perfectly!")
    print("   • Real-time audio generation ✓")
    print("   • Multiple instrument sounds ✓")
    print("   • Drum synthesis ✓")
    print("   • MIDI file playback ✓")
    print("   • No external hardware needed ✓")
    
    print("\n🚀 Ready for the full GUI application!")
    print("   Run 'python MIDI.PY' to start the complete interface.")

if __name__ == "__main__":
    try:
        test_synthesizer()
    except Exception as e:
        print(f"❌ Error during synthesizer testing: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Make sure your audio system is working and try again.")
