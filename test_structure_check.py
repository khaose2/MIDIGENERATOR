#!/usr/bin/env python3
"""
Test script to verify the structure of MP3ToMIDIConverter class
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from mp3_to_midi_converter import MP3ToMIDIConverter
    
    print("✅ Successfully imported MP3ToMIDIConverter")
    
    # Create an instance
    converter = MP3ToMIDIConverter()
    print("✅ Successfully created converter instance")
    
    # Check for generative methods
    generative_methods = [
        'generate_inspired_melody',
        'generate_harmony', 
        'create_variations',
        '_detect_key_signature',
        '_get_scale_notes',
        '_generate_similar_note',
        '_generate_jazz_note',
        '_generate_classical_note',
        '_generate_ambient_note',
        '_generate_creative_note',
        '_generate_chord_progression',
        '_apply_rhythmic_variation',
        '_apply_melodic_variation',
        '_apply_dynamic_variation'
    ]
    
    print("\n🔍 Checking for generative methods:")
    missing_methods = []
    
    for method_name in generative_methods:
        if hasattr(converter, method_name):
            print(f"  ✅ {method_name}")
        else:
            print(f"  ❌ {method_name}")
            missing_methods.append(method_name)
    
    if missing_methods:
        print(f"\n❌ Missing methods: {missing_methods}")
    else:
        print("\n✅ All generative methods found!")
    
    # Test a simple generative method call
    try:
        # Create dummy analysis data
        dummy_analysis = {
            'tempo': 120,
            'chroma_complexity': 0.1,
            'harmonic_ratio': 0.7,
            'onset_density': 2.0
        }
        
        print("\n🎵 Testing melody generation...")
        melody = converter.generate_inspired_melody(dummy_analysis, duration=5.0, style='similar')
        print(f"✅ Generated melody with {len(melody)} notes")
        
        print("\n🎵 Testing harmony generation...")
        harmony = converter.generate_harmony(melody[:5], dummy_analysis)  # Use first 5 notes
        print(f"✅ Generated harmony with {len(harmony)} notes")
        
        print("\n🎵 Testing variations...")
        variations = converter.create_variations(melody[:3], num_variations=2)  # Use first 3 notes
        print(f"✅ Generated {len(variations)} variations")
        
        print("\n🎉 All generative features working correctly!")
        
    except Exception as e:
        print(f"\n❌ Error testing generative methods: {str(e)}")
        import traceback
        traceback.print_exc()

except ImportError as e:
    print(f"❌ Failed to import MP3ToMIDIConverter: {str(e)}")
except Exception as e:
    print(f"❌ Unexpected error: {str(e)}")
    import traceback
    traceback.print_exc()
