#!/usr/bin/env python3
"""
Test script for audio playback fixes
"""

import numpy as np
import pygame
import time
import threading

class SimpleSynthesizer:
    """Simple test synthesizer to verify audio fixes"""
    
    def __init__(self, sample_rate=44100, buffer_size=512):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.active_notes = {}
        self.is_playing = False
        self.playback_thread = None
        self.sound_objects = []  # Keep references to prevent garbage collection
        
        # Initialize pygame mixer
        pygame.mixer.pre_init(frequency=sample_rate, size=-16, channels=2, buffer=buffer_size)
        pygame.mixer.init()
        
        # Initialize note frequencies (MIDI note 69 = A4 = 440 Hz)
        self.note_frequencies = {}
        for note in range(128):
            frequency = 440.0 * (2.0 ** ((note - 69) / 12.0))
            self.note_frequencies[note] = frequency
    
    def generate_sine_wave(self, frequency, duration, velocity):
        """Generate a simple sine wave"""
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples, False)
        amplitude = velocity / 127.0 * 0.3
        
        wave = amplitude * np.sin(2 * np.pi * frequency * t)
        
        # Simple envelope
        attack_samples = int(0.01 * self.sample_rate)
        release_samples = int(0.2 * self.sample_rate)
        
        if len(wave) > attack_samples:
            wave[:attack_samples] *= np.linspace(0, 1, attack_samples)
        if len(wave) > release_samples:
            wave[-release_samples:] *= np.linspace(1, 0, release_samples)
            
        return wave
    
    def note_on(self, channel, note, velocity):
        """Start playing a note"""
        if note in self.note_frequencies:
            frequency = self.note_frequencies[note]
            duration = 2.0  # 2 seconds
            wave_data = self.generate_sine_wave(frequency, duration, velocity)
            
            self.active_notes[(channel, note)] = {
                'wave_data': wave_data,
                'position': 0,
                'velocity': velocity,
                'start_time': time.time()
            }
    
    def note_off(self, channel, note):
        """Stop playing a note"""
        if (channel, note) in self.active_notes:
            del self.active_notes[(channel, note)]
    
    def get_audio_buffer(self):
        """Generate stereo audio buffer"""
        left = np.zeros(self.buffer_size, dtype=np.float32)
        right = np.zeros(self.buffer_size, dtype=np.float32)
        notes_to_remove = []
        
        for note_key, note_data in self.active_notes.items():
            wave_data = note_data['wave_data']
            position = note_data['position']
            
            samples_to_add = min(self.buffer_size, len(wave_data) - position)
            if samples_to_add > 0:
                left[:samples_to_add] += wave_data[position:position + samples_to_add] * 0.7
                right[:samples_to_add] += wave_data[position:position + samples_to_add] * 0.7
                note_data['position'] += samples_to_add
            
            if position >= len(wave_data) or time.time() - note_data['start_time'] > 3.0:
                notes_to_remove.append(note_key)
        
        for note_key in notes_to_remove:
            if note_key in self.active_notes:
                del self.active_notes[note_key]
        
        # Normalize
        max_val = max(np.max(np.abs(left)), np.max(np.abs(right)), 1.0)
        left = left / max_val * 0.9
        right = right / max_val * 0.9
        
        return left, right
    
    def play_test_sequence(self):
        """Play a test sequence to verify audio works"""
        self.is_playing = True
        
        def playback_worker():
            notes = [60, 64, 67, 72]  # C major chord
            
            for i, note in enumerate(notes):
                if not self.is_playing:
                    break
                    
                print(f"Playing note {note}")
                self.note_on(0, note, 80)
                
                # Play for 1 second
                for _ in range(int(1.0 / (self.buffer_size / self.sample_rate))):
                    if not self.is_playing:
                        break
                        
                    try:
                        left_channel, right_channel = self.get_audio_buffer()
                        left_int = (left_channel * 32767).astype(np.int16)
                        right_int = (right_channel * 32767).astype(np.int16)
                        stereo_buffer = np.zeros((len(left_int), 2), dtype=np.int16)
                        stereo_buffer[:, 0] = left_int
                        stereo_buffer[:, 1] = right_int
                        
                        sound = pygame.sndarray.make_sound(stereo_buffer)
                        sound.play()
                        
                        # Store reference to prevent garbage collection
                        self.sound_objects.append(sound)
                        if len(self.sound_objects) > 10:
                            self.sound_objects.pop(0)
                        
                        time.sleep(self.buffer_size / self.sample_rate)
                        
                    except Exception as e:
                        print(f"Audio playback error: {e}")
                        time.sleep(0.01)
                
                self.note_off(0, note)
                time.sleep(0.2)
            
            self.is_playing = False
            print("Test sequence complete!")
        
        self.playback_thread = threading.Thread(target=playback_worker)
        self.playback_thread.daemon = True
        self.playback_thread.start()
    
    def stop_playback(self):
        """Stop playback"""
        self.is_playing = False
        self.active_notes.clear()
        pygame.mixer.stop()
        
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=1.0)

if __name__ == "__main__":
    print("Testing audio playback fixes...")
    
    synth = SimpleSynthesizer()
    print("Synthesizer created successfully!")
    
    print("Testing audio buffer generation...")
    left, right = synth.get_audio_buffer()
    print(f"Empty buffer generated: left={len(left)}, right={len(right)}")
    
    print("Testing note generation...")
    synth.note_on(0, 60, 64)  # Middle C
    left, right = synth.get_audio_buffer()
    print(f"Buffer with note: max left={max(abs(left)):.4f}, max right={max(abs(right)):.4f}")
    synth.note_off(0, 60)
    
    print("Playing test sequence (4 notes)...")
    synth.play_test_sequence()
    
    # Wait for playback to complete
    while synth.is_playing:
        time.sleep(0.1)
    
    print("Audio system test completed successfully!")
