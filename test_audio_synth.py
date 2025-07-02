"""
Quick audio test for the new software synthesizer
Tests different instruments and plays a simple melody
"""

import time
from software_synthesizer import SoftwareSynthesizer

def test_synthesizer():
    print("🎵 Testing Advanced Software Synthesizer")
    print("=" * 50)
    
    # Initialize synthesizer
    synth = SoftwareSynthesizer()
    
    # Test different instruments
    instruments = ['piano', 'sine', 'sawtooth', 'square', 'triangle']
    notes = [60, 64, 67, 72]  # C, E, G, C octave
    
    for i, instrument in enumerate(instruments):
        print(f"\n🎼 Testing {instrument.upper()} instrument...")
        synth.set_instrument(0, instrument)
        
        # Play a simple melody
        for note in notes:
            synth.note_on(0, note, 100)
            time.sleep(0.5)  # Let each note play for 0.5 seconds
            synth.note_off(0, note)
        
        time.sleep(0.5)  # Brief pause between instruments
    
    # Test drums
    print(f"\n🥁 Testing DRUMS...")
    synth.set_instrument(9, 'drums')
    
    # Simple drum pattern
    drum_notes = [36, 38, 36, 38]  # Kick, Snare, Kick, Snare
    for note in drum_notes:
        synth.note_on(9, note, 120)
        time.sleep(0.3)
        synth.note_off(9, note)
    
    print("\n✅ Audio test complete!")
    print("If you heard different sounds for each instrument, the synthesizer is working!")

if __name__ == "__main__":
    test_synthesizer()
