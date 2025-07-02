"""
Advanced Software Synthesizer for Real-time MIDI Playback
Supports multiple waveforms, effects, and multi-channel audio synthesis
"""

import pygame
import numpy as np
import threading
import time
import mido
from typing import Dict, List, Optional

class SoftwareSynthesizer:
    """Advanced software synthesizer for real-time MIDI playback"""
    
    def __init__(self, sample_rate=44100, buffer_size=1024):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.active_notes = {}  # Dictionary of currently playing notes
        self.note_frequencies = {}  # MIDI note to frequency mapping
        self.is_playing = False
        self.playback_thread = None
        
        # Audio settings
        self.master_volume = 0.7
        self.filter_cutoff = 20000
        self.stereo_width = 0.5
        
        # Initialize pygame mixer
        pygame.mixer.pre_init(frequency=sample_rate, size=-16, channels=2, buffer=buffer_size)
        pygame.mixer.init()
        
        # Initialize note frequencies (MIDI note 69 = A4 = 440 Hz)
        for note in range(128):
            frequency = 440.0 * (2.0 ** ((note - 69) / 12.0))
            self.note_frequencies[note] = frequency
        
        # Channel instrument assignments
        self.channel_instruments = {
            0: 'piano',      # Melody
            1: 'sawtooth',   # Bass
            9: 'drums',      # Drums
            2: 'sine',       # Pad
            3: 'triangle'    # Lead
        }
        
        print("✅ Advanced Software Synthesizer initialized")
    
    def _generate_sine_wave(self, frequency, duration, velocity):
        """Generate a sine wave with ADSR envelope"""
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples, False)
        amplitude = (velocity / 127.0) * 0.3
        
        # Generate sine wave with harmonics for richer sound
        wave = amplitude * (
            1.0 * np.sin(2 * np.pi * frequency * t) +
            0.3 * np.sin(2 * np.pi * frequency * 2 * t) +
            0.1 * np.sin(2 * np.pi * frequency * 3 * t)
        )
        
        # Apply ADSR envelope
        wave = self._apply_envelope(wave, 'sine')
        return wave
    
    def _generate_sawtooth_wave(self, frequency, duration, velocity):
        """Generate a band-limited sawtooth wave"""
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples, False)
        amplitude = (velocity / 127.0) * 0.25
        
        # Generate band-limited sawtooth using additive synthesis
        wave = np.zeros(samples)
        max_harmonics = min(50, int(self.sample_rate / (2 * frequency)))
        
        for n in range(1, max_harmonics + 1):
            wave += ((-1)**(n+1)) * np.sin(2 * np.pi * frequency * n * t) / n
        
        wave = amplitude * wave * (2/np.pi)
        wave = self._apply_envelope(wave, 'sawtooth')
        return wave
    
    def _generate_square_wave(self, frequency, duration, velocity):
        """Generate a band-limited square wave"""
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples, False)
        amplitude = (velocity / 127.0) * 0.2
        
        # Generate band-limited square wave using additive synthesis
        wave = np.zeros(samples)
        max_harmonics = min(50, int(self.sample_rate / (2 * frequency)))
        
        for n in range(1, max_harmonics + 1, 2):  # Only odd harmonics
            wave += np.sin(2 * np.pi * frequency * n * t) / n
        
        wave = amplitude * wave * (4/np.pi)
        wave = self._apply_envelope(wave, 'square')
        return wave
    
    def _generate_triangle_wave(self, frequency, duration, velocity):
        """Generate a triangle wave"""
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples, False)
        amplitude = (velocity / 127.0) * 0.3
        
        # Generate triangle wave using additive synthesis
        wave = np.zeros(samples)
        max_harmonics = min(30, int(self.sample_rate / (2 * frequency)))
        
        for n in range(1, max_harmonics + 1, 2):  # Only odd harmonics
            wave += ((-1)**((n-1)//2)) * np.sin(2 * np.pi * frequency * n * t) / (n*n)
        
        wave = amplitude * wave * (8/(np.pi*np.pi))
        wave = self._apply_envelope(wave, 'triangle')
        return wave
    
    def _generate_piano_wave(self, frequency, duration, velocity):
        """Generate piano-like sound with complex harmonics"""
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples, False)
        amplitude = (velocity / 127.0) * 0.4
        
        # Piano has strong fundamental with decreasing harmonics
        wave = amplitude * (
            1.0 * np.sin(2 * np.pi * frequency * t) +
            0.6 * np.sin(2 * np.pi * frequency * 2 * t) +
            0.4 * np.sin(2 * np.pi * frequency * 3 * t) +
            0.3 * np.sin(2 * np.pi * frequency * 4 * t) +
            0.2 * np.sin(2 * np.pi * frequency * 5 * t) +
            0.1 * np.sin(2 * np.pi * frequency * 6 * t)
        )
        
        # Piano-style envelope with quick attack and gradual decay
        wave = self._apply_piano_envelope(wave)
        return wave
    
    def _generate_drum_sound(self, note, duration, velocity):
        """Generate drum sounds based on MIDI note"""
        samples = int(duration * self.sample_rate)
        amplitude = (velocity / 127.0) * 0.5
        
        if note == 36:  # Kick drum
            # Low frequency sine with pitch bend down
            t = np.linspace(0, duration, samples, False)
            pitch_bend = np.exp(-t * 8)  # Exponential decay
            wave = amplitude * np.sin(2 * np.pi * 60 * pitch_bend * t)
            
        elif note == 38:  # Snare drum
            # Noise + tone
            t = np.linspace(0, duration, samples, False)
            noise = np.random.normal(0, 1, samples) * 0.7
            tone = np.sin(2 * np.pi * 200 * t) * 0.3
            wave = amplitude * (noise + tone)
            
        else:  # Hi-hat and other percussion
            # Filtered noise
            noise = np.random.normal(0, 1, samples)
            wave = amplitude * noise * 0.3
        
        # Apply drum envelope (quick attack, fast decay)
        wave = self._apply_drum_envelope(wave)
        return wave
    
    def _apply_envelope(self, wave, waveform_type):
        """Apply ADSR envelope based on waveform type"""
        length = len(wave)
        
        if waveform_type == 'piano':
            return self._apply_piano_envelope(wave)
        
        # Standard ADSR envelope
        attack_samples = int(0.01 * self.sample_rate)  # 10ms attack
        decay_samples = int(0.1 * self.sample_rate)    # 100ms decay
        release_samples = int(0.2 * self.sample_rate)  # 200ms release
        
        envelope = np.ones(length)
        
        # Attack
        if length > attack_samples:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Decay
        if length > attack_samples + decay_samples:
            envelope[attack_samples:attack_samples + decay_samples] = np.linspace(1, 0.7, decay_samples)
        
        # Release
        if length > release_samples:
            envelope[-release_samples:] *= np.linspace(1, 0, release_samples)
        
        return wave * envelope
    
    def _apply_piano_envelope(self, wave):
        """Apply piano-style envelope"""
        length = len(wave)
        attack_samples = int(0.005 * self.sample_rate)  # Very quick attack
        decay_samples = length - attack_samples    # Long decay
        
        envelope = np.ones(length)
        
        # Quick attack
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Exponential decay
        if decay_samples > 0:
            decay_curve = np.exp(-np.linspace(0, 3, decay_samples))
            envelope[attack_samples:] = decay_curve
        
        return wave * envelope
    
    def _apply_drum_envelope(self, wave):
        """Apply drum-style envelope"""
        length = len(wave)
        attack_samples = int(0.002 * self.sample_rate)  # Very quick attack
        decay_samples = length - attack_samples    # Quick decay
        
        envelope = np.ones(length)
        
        # Instant attack
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Quick exponential decay
        if decay_samples > 0:
            decay_curve = np.exp(-np.linspace(0, 8, decay_samples))
            envelope[attack_samples:] = decay_curve
        
        return wave * envelope
    
    def _apply_lowpass_filter(self, wave):
        """Apply simple lowpass filter"""
        if self.filter_cutoff >= self.sample_rate / 2:
            return wave
        
        # Simple one-pole lowpass filter
        cutoff_normalized = self.filter_cutoff / (self.sample_rate / 2)
        b = 2.0 * np.pi * cutoff_normalized
        a = b / (1.0 + b)
        
        filtered = np.zeros_like(wave)
        y = 0
        for i in range(len(wave)):
            y = a * wave[i] + (1 - a) * y
            filtered[i] = y
        
        return filtered
    
    def _apply_stereo_effects(self, wave):
        """Apply stereo width and create stereo output"""
        if self.stereo_width <= 0:
            return wave, wave
        
        # Create stereo width using Haas effect
        delay_samples = int(self.stereo_width * 0.02 * self.sample_rate)  # Max 20ms delay
        left = wave.copy()
        right = np.zeros_like(wave)
        
        if delay_samples > 0 and delay_samples < len(wave):
            right[delay_samples:] = wave[:-delay_samples]
        else:
            right = wave.copy()
        
        return left, right
    
    def note_on(self, channel, note, velocity):
        """Start playing a note"""
        if note not in self.note_frequencies:
            return
        
        frequency = self.note_frequencies[note]
        instrument = self.channel_instruments.get(channel, 'sine')
        
        # Generate appropriate waveform
        duration = 2.0  # Default duration
        
        if instrument == 'sine':
            wave_data = self._generate_sine_wave(frequency, duration, velocity)
        elif instrument == 'sawtooth':
            wave_data = self._generate_sawtooth_wave(frequency, duration, velocity)
        elif instrument == 'square':
            wave_data = self._generate_square_wave(frequency, duration, velocity)
        elif instrument == 'triangle':
            wave_data = self._generate_triangle_wave(frequency, duration, velocity)
        elif instrument == 'piano':
            wave_data = self._generate_piano_wave(frequency, duration, velocity)
        elif instrument == 'drums':
            wave_data = self._generate_drum_sound(note, duration, velocity)
        else:
            wave_data = self._generate_sine_wave(frequency, duration, velocity)
        
        # Apply effects
        wave_data = self._apply_lowpass_filter(wave_data)
        
        # Apply master volume
        wave_data = wave_data * self.master_volume
        
        # Store the note data
        self.active_notes[(channel, note)] = {
            "wave_data": wave_data,
            "start_time": time.time(),
            "velocity": velocity
        }
        
        # Play the sound immediately
        self._play_wave_data(wave_data)
    
    def note_off(self, channel, note):
        """Stop playing a note"""
        if (channel, note) in self.active_notes:
            del self.active_notes[(channel, note)]
    
    def _play_wave_data(self, wave_data):
        """Play wave data using pygame"""
        try:
            # Apply stereo effects
            left, right = self._apply_stereo_effects(wave_data)
            
            # Interleave stereo channels
            stereo_data = np.zeros(len(left) * 2)
            stereo_data[0::2] = left
            stereo_data[1::2] = right
            
            # Convert to int16 and scale
            stereo_data = np.clip(stereo_data * 32767, -32768, 32767).astype(np.int16)
            
            # Create pygame sound and play
            sound = pygame.sndarray.make_sound(stereo_data.reshape(-1, 2))
            sound.play()
            
        except Exception as e:
            print(f"Audio playback error: {e}")
    
    def play_midi_file(self, midi_file, generator=None):
        """Play a MIDI file using the software synthesizer"""
        if self.is_playing:
            self.stop_playback()
        
        self.is_playing = True
        
        def playback_worker():
            try:
                # Parse MIDI file for timing
                ticks_per_beat = midi_file.ticks_per_beat
                tempo = 500000  # Default microseconds per beat (120 BPM)
                
                # Collect all events with absolute timing
                events = []
                for track in midi_file.tracks:
                    current_time = 0
                    for msg in track:
                        current_time += msg.time
                        if hasattr(msg, 'tempo'):
                            tempo = msg.tempo
                        elif hasattr(msg, 'type') and msg.type in ['note_on', 'note_off']:
                            events.append((current_time, msg))
                
                # Sort events by time
                events.sort(key=lambda x: x[0])
                
                # Play events in real-time
                start_time = time.time()
                last_event_time = 0
                
                for event_time, msg in events:
                    if not self.is_playing:
                        break
                    
                    # Calculate real time delay
                    time_diff = (event_time - last_event_time) / ticks_per_beat * (tempo / 1000000.0)
                    if time_diff > 0:
                        time.sleep(time_diff)
                    
                    # Process MIDI message
                    if msg.type == 'note_on' and msg.velocity > 0:
                        self.note_on(msg.channel, msg.note, msg.velocity)
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        self.note_off(msg.channel, msg.note)
                    
                    last_event_time = event_time
                
                print("🎵 MIDI playback complete!")
                
            except Exception as e:
                print(f"MIDI playback error: {e}")
            finally:
                self.is_playing = False
        
        self.playback_thread = threading.Thread(target=playback_worker, daemon=True)
        self.playback_thread.start()
        print("🎵 Starting MIDI playback...")
    
    def stop_playback(self):
        """Stop MIDI playback"""
        self.is_playing = False
        self.active_notes.clear()
        pygame.mixer.stop()
        
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=1.0)
        
        print("⏹️ Playback stopped")
    
    def set_master_volume(self, volume):
        """Set master volume (0.0 to 1.0)"""
        self.master_volume = max(0.0, min(1.0, volume))
    
    def set_filter_cutoff(self, cutoff):
        """Set lowpass filter cutoff frequency"""
        self.filter_cutoff = max(100, min(cutoff, self.sample_rate // 2))
    
    def set_stereo_width(self, width):
        """Set stereo width (0.0 to 1.0)"""
        self.stereo_width = max(0.0, min(1.0, width))
    
    def set_instrument(self, channel, instrument):
        """Set instrument for a specific channel"""
        valid_instruments = ['sine', 'sawtooth', 'square', 'triangle', 'piano', 'drums']
        if instrument in valid_instruments:
            self.channel_instruments[channel] = instrument
            print(f"Channel {channel} instrument set to {instrument}")
