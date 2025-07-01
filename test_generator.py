#!/usr/bin/env python3
"""
Test script for the Ultimate MIDI Generator
This script demonstrates the core functionality without the GUI
"""

from MIDI import MIDIGenerator, MIDISettings
import time

def test_midi_generation():
    """Test basic MIDI generation"""
    print("🎵 Testing Ultimate MIDI Generator 🎵")
    print("=" * 50)
    
    # Create generator
    generator = MIDIGenerator()
    
    # Test 1: Basic generation with default settings
    print("\n1. Testing basic generation...")
    midi_file = generator.generate_music()
    print(f"   ✅ Generated MIDI with {len(generator.notes_data)} notes")
    
    # Save the basic test
    midi_file.save("test_basic.mid")
    print("   💾 Saved as 'test_basic.mid'")
    
    # Test 2: Jazz style
    print("\n2. Testing Jazz style...")
    generator.settings.chord_progression_style = "jazz"
    generator.settings.scale_type = "minor"
    generator.settings.tempo = 140
    generator.settings.swing_factor = 0.3
    midi_file = generator.generate_music()
    midi_file.save("test_jazz.mid")
    print(f"   ✅ Generated Jazz MIDI with {len(generator.notes_data)} notes")
    print("   💾 Saved as 'test_jazz.mid'")
    
    # Test 3: Blues style
    print("\n3. Testing Blues style...")
    generator.settings.chord_progression_style = "blues"
    generator.settings.scale_type = "blues"
    generator.settings.tempo = 100
    generator.settings.key_signature = "E"
    midi_file = generator.generate_music()
    midi_file.save("test_blues.mid")
    print(f"   ✅ Generated Blues MIDI with {len(generator.notes_data)} notes")
    print("   💾 Saved as 'test_blues.mid'")
    
    # Test 4: Classical style
    print("\n4. Testing Classical style...")
    generator.settings.chord_progression_style = "classical"
    generator.settings.scale_type = "major"
    generator.settings.tempo = 120
    generator.settings.key_signature = "D"
    generator.settings.bass_line_style = "alternating"
    midi_file = generator.generate_music()
    midi_file.save("test_classical.mid")
    print(f"   ✅ Generated Classical MIDI with {len(generator.notes_data)} notes")
    print("   💾 Saved as 'test_classical.mid'")
    
    # Test 5: Chaotic/Random style
    print("\n5. Testing Chaotic style...")
    generator.settings.chaos_factor = 0.3
    generator.settings.mutation_rate = 0.1
    generator.settings.scale_type = "chromatic"
    generator.settings.tempo = 160
    midi_file = generator.generate_music()
    midi_file.save("test_chaos.mid")
    print(f"   ✅ Generated Chaotic MIDI with {len(generator.notes_data)} notes")
    print("   💾 Saved as 'test_chaos.mid'")
    
    # Test 6: Complete randomization
    print("\n6. Testing complete randomization...")
    generator.randomize_settings()
    midi_file = generator.generate_music()
    midi_file.save("test_random.mid")
    print(f"   ✅ Generated Random MIDI with {len(generator.notes_data)} notes")
    print(f"   🎲 Random settings: {generator.settings.tempo} BPM, {generator.settings.key_signature} {generator.settings.scale_type}")
    print("   💾 Saved as 'test_random.mid'")
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed successfully!")
    print("\nGenerated files:")
    print("  • test_basic.mid - Basic generation")
    print("  • test_jazz.mid - Jazz style")
    print("  • test_blues.mid - Blues style") 
    print("  • test_classical.mid - Classical style")
    print("  • test_chaos.mid - Chaotic/experimental")
    print("  • test_random.mid - Completely randomized")
    print("\nYou can now:")
    print("  1. Open these MIDI files in any DAW or music software")
    print("  2. Play them with a MIDI player")
    print("  3. Import them into notation software")
    print("  4. Run 'python MIDI.PY' for the full GUI experience")

def test_settings_variations():
    """Test different settings combinations"""
    print("\n🔧 Testing Settings Variations...")
    generator = MIDIGenerator()
    
    # Test different scales
    scales_to_test = ["major", "minor", "dorian", "blues", "pentatonic"]
    for i, scale in enumerate(scales_to_test):
        generator.settings.scale_type = scale
        generator.settings.key_signature = ["C", "D", "E", "F", "G"][i]
        generator.generate_music()
        filename = f"test_scale_{scale}.mid"
        generator.current_midi.save(filename)
        print(f"   ✅ Generated {scale} scale in {generator.settings.key_signature}: {filename}")

if __name__ == "__main__":
    try:
        test_midi_generation()
        test_settings_variations()
        
        print("\n🚀 Ready to use the Ultimate MIDI Generator!")
        print("Run 'python MIDI.PY' to start the full GUI application.")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
