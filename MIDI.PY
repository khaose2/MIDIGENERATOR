import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import pygame
import mido
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import threading
import random
import json
import time
import colorsys
import os
import math
from dataclasses import dataclass
from typing import List, Dict, Any

# <<< NEW: Import Librosa for audio analysis >>>
import librosa
import librosa.display

# Initialize pygame mixer for audio playback
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.mixer.init()

@dataclass
class MIDISettings:
    """Data class to hold all MIDI generation settings"""
    # Basic Settings
    tempo: int = 120
    time_signature_num: int = 4
    time_signature_den: int = 4
    key_signature: str = "C"
    scale_type: str = "major"
    
    # Note Generation
    note_length_min: float = 0.25
    note_length_max: float = 2.0
    note_velocity_min: int = 60
    note_velocity_max: int = 127
    note_range_low: int = 60  # Middle C
    note_range_high: int = 84
    
    # Rhythm Settings
    swing_factor: float = 0.0
    syncopation_prob: float = 0.1
    rest_probability: float = 0.2
    triplet_probability: float = 0.1
    dotted_note_prob: float = 0.15
    
    # Harmony Settings
    chord_progression_style: str = "random"
    chord_complexity: int = 3  # 3 = triads, 4 = 7th chords, etc.
    bass_line_style: str = "root"
    voice_leading: bool = True
    parallel_motion_avoid: bool = True
    
    # Melody Settings
    melody_direction_bias: float = 0.0  # -1 = down, 0 = random, 1 = up
    interval_preference: str = "balanced"
    repetition_factor: float = 0.3
    sequence_probability: float = 0.2
    leap_probability: float = 0.1
    
    # Instruments
    lead_instrument: int = 1  # Piano
    bass_instrument: int = 33  # Electric Bass
    drum_instrument: int = 129  # Drum kit
    pad_instrument: int = 89  # Warm Pad
    
    # Structure
    song_length_bars: int = 32
    intro_bars: int = 4
    verse_bars: int = 8
    chorus_bars: int = 8
    bridge_bars: int = 4
    outro_bars: int = 4
    
    # Dynamics
    dynamic_range: float = 0.5
    crescendo_prob: float = 0.1
    accent_probability: float = 0.15
    ghost_note_prob: float = 0.05
    
    # Effects
    reverb_amount: float = 0.3
    chorus_amount: float = 0.1
    delay_amount: float = 0.0
    distortion_amount: float = 0.0
    
    # Randomization
    chaos_factor: float = 0.1
    mutation_rate: float = 0.05
    evolution_steps: int = 0
    
    # Visualization
    viz_style: str = "piano_roll"
    color_scheme: str = "rainbow"
    animation_speed: float = 1.0
    show_note_names: bool = True
    show_velocity: bool = True

class MIDIGenerator:
    """Main MIDI generation engine"""
    
    def __init__(self):
        self.settings = MIDISettings()
        self.current_midi = None
        self.is_playing = False
        self.notes_data = []
        
        # Musical scales
        self.scales = {
            "major": [0, 2, 4, 5, 7, 9, 11],
            "minor": [0, 2, 3, 5, 7, 8, 10],
            "dorian": [0, 2, 3, 5, 7, 9, 10],
            "phrygian": [0, 1, 3, 5, 7, 8, 10],
            "lydian": [0, 2, 4, 6, 7, 9, 11],
            "mixolydian": [0, 2, 4, 5, 7, 9, 10],
            "locrian": [0, 1, 3, 5, 6, 8, 10],
            "blues": [0, 3, 5, 6, 7, 10],
            "pentatonic": [0, 2, 4, 7, 9],
            "chromatic": list(range(12))
        }
        
        # Chord progressions
        self.chord_progressions = {
            "pop": [1, 5, 6, 4],
            "jazz": [1, 6, 2, 5],
            "classical": [1, 4, 5, 1],
            "blues": [1, 1, 1, 1, 4, 4, 1, 1, 5, 4, 1, 5],
            "rock": [1, 7, 4, 1],
            "random": []
        }
    
    def get_scale_notes(self, root=60):
        """Get notes in the current scale"""
        scale = self.scales.get(self.settings.scale_type, self.scales["major"])
        key_offset = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5,
                      "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
        offset = key_offset.get(self.settings.key_signature, 0)
        
        notes = []
        for octave in range(-2, 3):
            for note in scale:
                midi_note = root + note + offset + (octave * 12)
                if self.settings.note_range_low <= midi_note <= self.settings.note_range_high:
                    notes.append(midi_note)
        return sorted(notes)
    
    def generate_chord_progression(self, bars):
        """Generate a chord progression"""
        if self.settings.chord_progression_style == "random":
            progression = [random.randint(1, 7) for _ in range(bars)]
        else:
            base_prog = self.chord_progressions.get(self.settings.chord_progression_style, [1, 4, 5, 1])
            progression = (base_prog * (bars // len(base_prog) + 1))[:bars]
        return progression
    
    def generate_melody(self, bars, chord_progression):
        """Generate a melody line"""
        notes = []
        scale_notes = self.get_scale_notes()
        current_time = 0.0
        beats_per_bar = self.settings.time_signature_num
        
        for bar in range(bars):
            bar_time = 0.0
            while bar_time < beats_per_bar:
                # Skip if rest
                if random.random() < self.settings.rest_probability:
                    note_length = random.uniform(self.settings.note_length_min, self.settings.note_length_max)
                    bar_time += note_length
                    current_time += note_length
                    continue
                
                # Choose note from scale
                if not notes:
                    note = random.choice(scale_notes)
                else:
                    last_note = notes[-1]['note']
                    # Apply direction bias
                    if self.settings.melody_direction_bias > 0:
                        candidates = [n for n in scale_notes if n > last_note]
                    elif self.settings.melody_direction_bias < 0:
                        candidates = [n for n in scale_notes if n < last_note]
                    else:
                        candidates = scale_notes
                    
                    if not candidates:
                        candidates = scale_notes
                    
                    # Apply interval preferences
                    if random.random() < self.settings.leap_probability:
                        # Large interval
                        note = random.choice(candidates)
                    else:
                        # Step-wise motion
                        close_notes = [n for n in candidates if abs(n - last_note) <= 2]
                        note = random.choice(close_notes if close_notes else candidates)
                
                # Note length
                if random.random() < self.settings.triplet_probability:
                    note_length = random.uniform(0.25, 0.75)
                else:
                    note_length = random.uniform(self.settings.note_length_min, self.settings.note_length_max)
                
                if random.random() < self.settings.dotted_note_prob:
                    note_length *= 1.5
                
                # Velocity
                velocity = random.randint(self.settings.note_velocity_min, self.settings.note_velocity_max)
                if random.random() < self.settings.accent_probability:
                    velocity = min(127, velocity + 20)
                elif random.random() < self.settings.ghost_note_prob:
                    velocity = max(1, velocity - 30)
                
                notes.append({
                    'note': note,
                    'start': current_time,
                    'duration': note_length,
                    'velocity': velocity,
                    'channel': 0
                })
                
                bar_time += note_length
                current_time += note_length
        
        return notes
    
    def generate_bass_line(self, bars, chord_progression):
        """Generate a bass line"""
        notes = []
        current_time = 0.0
        beats_per_bar = self.settings.time_signature_num
        
        for bar, chord_root in enumerate(chord_progression):
            bass_note = self.settings.note_range_low - 12 + (chord_root - 1) * 2
            
            for beat in range(beats_per_bar):
                if self.settings.bass_line_style == "root":
                    note = bass_note
                elif self.settings.bass_line_style == "walking":
                    if beat == 0:
                        note = bass_note
                    else:
                        note = bass_note + random.choice([-2, -1, 0, 1, 2])
                else:  # "alternating"
                    note = bass_note if beat % 2 == 0 else bass_note + 7
                
                notes.append({
                    'note': max(20, min(60, note)),
                    'start': current_time,
                    'duration': 1.0,
                    'velocity': random.randint(70, 100),
                    'channel': 1
                })
                current_time += 1.0
        
        return notes
    
    def add_drums(self, bars):
        """Add drum pattern"""
        notes = []
        current_time = 0.0
        beats_per_bar = self.settings.time_signature_num
        
        # Drum mapping (General MIDI)
        kick = 36
        snare = 38
        hihat = 42
        
        for bar in range(bars):
            for beat in range(beats_per_bar):
                # Kick on 1 and 3
                if beat % 2 == 0:
                    notes.append({
                        'note': kick,
                        'start': current_time,
                        'duration': 0.1,
                        'velocity': random.randint(90, 120),
                        'channel': 9  # Drum channel
                    })
                
                # Snare on 2 and 4
                if beat % 2 == 1:
                    notes.append({
                        'note': snare,
                        'start': current_time,
                        'duration': 0.1,
                        'velocity': random.randint(80, 110),
                        'channel': 9
                    })
                
                # Hi-hat every beat
                notes.append({
                    'note': hihat,
                    'start': current_time,
                    'duration': 0.1,
                    'velocity': random.randint(40, 70),
                    'channel': 9
                })
                
                current_time += 1.0
        
        return notes
    
    def apply_randomization(self, notes):
        """Apply chaos and mutation to notes"""
        if self.settings.chaos_factor == 0 and self.settings.mutation_rate == 0:
            return notes
        
        modified_notes = []
        for note in notes:
            new_note = note.copy()
            
            # Chaos factor - random changes
            if random.random() < self.settings.chaos_factor:
                if random.random() < 0.3:  # Change pitch
                    new_note['note'] += random.randint(-3, 3)
                if random.random() < 0.3:  # Change timing
                    new_note['start'] += random.uniform(-0.1, 0.1)
                if random.random() < 0.3:  # Change velocity
                    new_note['velocity'] += random.randint(-20, 20)
            
            # Mutation rate - slight variations
            if random.random() < self.settings.mutation_rate:
                new_note['note'] += random.choice([-1, 0, 1])
                new_note['velocity'] += random.randint(-10, 10)
            
            # Clamp values
            new_note['note'] = max(0, min(127, new_note['note']))
            new_note['velocity'] = max(1, min(127, new_note['velocity']))
            new_note['start'] = max(0, new_note['start'])
            
            modified_notes.append(new_note)
        
        return modified_notes
    
    def generate_music(self):
        """Generate complete musical piece"""
        total_bars = self.settings.song_length_bars
        chord_progression = self.generate_chord_progression(total_bars)
        
        all_notes = []
        
        # Generate melody
        melody_notes = self.generate_melody(total_bars, chord_progression)
        all_notes.extend(melody_notes)
        
        # Generate bass
        bass_notes = self.generate_bass_line(total_bars, chord_progression)
        all_notes.extend(bass_notes)
        
        # Add drums
        drum_notes = self.add_drums(total_bars)
        all_notes.extend(drum_notes)
        
        # Apply randomization
        all_notes = self.apply_randomization(all_notes)
        
        # Store for visualization
        self.notes_data = sorted(all_notes, key=lambda x: x['start'])
        
        return self.create_midi_file(all_notes)
    
    def create_midi_file(self, notes):
        """Create MIDI file from notes"""
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        # Set tempo
        tempo = mido.bpm2tempo(self.settings.tempo)
        track.append(mido.MetaMessage('set_tempo', tempo=tempo))
        
        # Group notes by channel
        channels = {}
        for note in notes:
            channel = note['channel']
            if channel not in channels:
                channels[channel] = []
            channels[channel].append(note)
        
        # Convert to MIDI messages
        current_time = 0
        events = []
        
        for note in notes:
            start_time = int(note['start'] * 480)  # Convert to ticks
            duration = int(note['duration'] * 480)
            
            events.append((start_time, 'note_on', note))
            events.append((start_time + duration, 'note_off', note))
        
        events.sort(key=lambda x: x[0])  # Sort by time
        
        for event_time, event_type, note in events:
            delta_time = event_time - current_time
            current_time = event_time
            
            if event_type == 'note_on':
                track.append(mido.Message('note_on', 
                                          channel=note['channel'],
                                          note=note['note'], 
                                          velocity=note['velocity'], 
                                          time=delta_time))
            else:
                track.append(mido.Message('note_off', 
                                          channel=note['channel'],
                                          note=note['note'], 
                                          velocity=64, 
                                          time=delta_time))
        
        self.current_midi = mid
        return mid
    
    def randomize_settings(self):
        """Randomize various settings"""
        self.settings.tempo = random.randint(60, 180)
        self.settings.key_signature = random.choice(["C", "D", "E", "F", "G", "A", "B"])
        self.settings.scale_type = random.choice(list(self.scales.keys()))
        self.settings.note_range_low = random.randint(48, 72)
        self.settings.note_range_high = self.settings.note_range_low + random.randint(12, 36)
        self.settings.swing_factor = random.uniform(0, 0.5)
        self.settings.syncopation_prob = random.uniform(0, 0.3)
        self.settings.rest_probability = random.uniform(0, 0.4)
        self.settings.chord_progression_style = random.choice(list(self.chord_progressions.keys()))
        self.settings.melody_direction_bias = random.uniform(-1, 1)
        self.settings.chaos_factor = random.uniform(0, 0.3)

# <<< NEW: Class for handling MP3 to MIDI conversion >>>
class MP3toMIDIConverter:
    """
    A simple monophonic MP3 to MIDI converter.
    Detects the most prominent melodic line in an audio file.
    """
    def __init__(self, progress_callback=None):
        """
        Initializes the converter.
        :param progress_callback: A function to call with progress updates (0-100).
        """
        self.progress_callback = progress_callback

    def _update_progress(self, value):
        if self.progress_callback:
            self.progress_callback(value)

    def convert(self, audio_path: str):
        """
        Converts an audio file to a list of MIDI note data.
        :param audio_path: Path to the MP3 or WAV file.
        :return: A list of note dictionaries, similar to MIDIGenerator's format.
        """
        notes_data = []
        try:
            self._update_progress(5)
            # 1. Load the audio file
            y, sr = librosa.load(audio_path, sr=44100)
            self._update_progress(20)

            # 2. Get the tempo to align notes to the beat grid
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)[0]
            
            self._update_progress(40)
            
            # 3. Detect note onsets (when notes start)
            onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
            self._update_progress(60)
            
            if len(onsets) == 0:
                return []

            # 4. Estimate pitch for the whole track
            # Using pyin for robust monophonic pitch detection
            pitches, _, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
            self._update_progress(80)

            # 5. Create note events from onsets and pitches
            for i in range(len(onsets)):
                start_time = onsets[i]
                
                # Determine duration
                duration = (onsets[i+1] - start_time) if i < len(onsets) - 1 else 0.5 # Default last note duration
                
                # Find the pitch at the onset time
                frame_index = librosa.time_to_frames(start_time, sr=sr)
                pitch_freq = pitches[frame_index]
                
                # If a pitch is detected, create a note
                if pitch_freq > 0:
                    midi_note = round(librosa.hz_to_midi(pitch_freq))
                    
                    # Estimate velocity from audio power at that time
                    start_sample = librosa.time_to_samples(start_time, sr=sr)
                    end_sample = start_sample + 1024 # Analyze a small window
                    rms = librosa.feature.rms(y=y[start_sample:end_sample])[0, 0]
                    velocity = int(np.clip(rms * 250, 40, 127)) # Scale and clip velocity
                    
                    # Convert time to beats
                    start_beat = start_time * (tempo / 60.0)
                    duration_beats = duration * (tempo / 60.0)

                    notes_data.append({
                        'note': midi_note,
                        'start': start_beat,
                        'duration': max(0.1, duration_beats), # Ensure minimum duration
                        'velocity': velocity,
                        'channel': 0  # Put all converted notes on channel 0
                    })
            self._update_progress(100)
            return notes_data

        except Exception as e:
            messagebox.showerror("Conversion Error", f"Failed to process audio file: {e}")
            self._update_progress(0)
            return []


class SoftwareSynthesizer:
    """Software synthesizer for real-time MIDI playback"""
    
    def __init__(self, sample_rate=44100, buffer_size=512):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.active_notes = {}  # Dictionary of currently playing notes
        self.note_frequencies = {}  # MIDI note to frequency mapping
        self.is_playing = False
        self.playback_thread = None
        self.audio_buffer = np.zeros(buffer_size)
        
        # Initialize note frequencies (MIDI note 69 = A4 = 440 Hz)
        for note in range(128):
            frequency = 440.0 * (2.0 ** ((note - 69) / 12.0))
            self.note_frequencies[note] = frequency
        
        # Instrument waveforms
        self.waveforms = {
            'sine': self._generate_sine_wave,
            'square': self._generate_square_wave,
            'sawtooth': self._generate_sawtooth_wave,
            'triangle': self._generate_triangle_wave,
            'piano': self._generate_piano_wave,
            'drums': self._generate_drum_sound
        }
        
        # Channel instrument assignments
        self.channel_instruments = {
            0: 'piano',      # Melody
            1: 'sawtooth',   # Bass
            9: 'drums',      # Drums
            2: 'sine',       # Pad
            3: 'triangle'    # Lead
        }
    
    def _generate_sine_wave(self, frequency, duration, velocity, sample_rate):
        """Generate sine wave"""
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples, False)
        amplitude = velocity / 127.0 * 0.3
        
        # Add some harmonics for richer sound
        wave = amplitude * (
            np.sin(2 * np.pi * frequency * t) +
            0.3 * np.sin(2 * np.pi * frequency * 2 * t) +
            0.1 * np.sin(2 * np.pi * frequency * 3 * t)
        )
        
        # Apply envelope (ADSR)
        envelope = self._apply_envelope(wave, sample_rate)
        return wave * envelope
    
    def _generate_square_wave(self, frequency, duration, velocity, sample_rate):
        """Generate square wave (good for bass)"""
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples, False)
        amplitude = velocity / 127.0 * 0.2
        
        wave = amplitude * np.sign(np.sin(2 * np.pi * frequency * t))
        
        # Apply envelope
        envelope = self._apply_envelope(wave, sample_rate)
        return wave * envelope
    
    def _generate_sawtooth_wave(self, frequency, duration, velocity, sample_rate):
        """Generate sawtooth wave"""
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples, False)
        amplitude = velocity / 127.0 * 0.25
        
        wave = amplitude * (2 * (t * frequency - np.floor(t * frequency + 0.5)))
        
        # Apply envelope
        envelope = self._apply_envelope(wave, sample_rate)
        return wave * envelope
    
    def _generate_triangle_wave(self, frequency, duration, velocity, sample_rate):
        """Generate triangle wave"""
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples, False)
        amplitude = velocity / 127.0 * 0.3
        
        wave = amplitude * (2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1)
        
        # Apply envelope
        envelope = self._apply_envelope(wave, sample_rate)
        return wave * envelope
    
    def _generate_piano_wave(self, frequency, duration, velocity, sample_rate):
        """Generate piano-like sound with multiple harmonics"""
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples, False)
        amplitude = velocity / 127.0 * 0.4
        
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
        envelope = self._apply_piano_envelope(wave, sample_rate)
        return wave * envelope
    
    def _generate_drum_sound(self, frequency, duration, velocity, sample_rate):
        """Generate drum sounds based on MIDI note"""
        samples = int(duration * sample_rate)
        amplitude = velocity / 127.0 * 0.5
        
        # Different drum sounds based on MIDI note
        if frequency < 100:  # Kick drum range
            # Kick drum: low frequency sine with pitch bend down
            t = np.linspace(0, duration, samples, False)
            pitch_bend = np.exp(-t * 8)  # Exponential decay
            wave = amplitude * np.sin(2 * np.pi * 60 * pitch_bend * t)
            
        elif 100 <= frequency < 200:  # Snare range
            # Snare: noise + tone
            t = np.linspace(0, duration, samples, False)
            noise = np.random.normal(0, 1, samples) * 0.7
            tone = np.sin(2 * np.pi * 200 * t) * 0.3
            wave = amplitude * (noise + tone)
            
        else:  # Hi-hat range
            # Hi-hat: filtered noise
            noise = np.random.normal(0, 1, samples)
            # Simple high-pass filter effect
            wave = amplitude * noise * 0.3
        
        # Drum envelope - quick attack, fast decay
        envelope = self._apply_drum_envelope(wave, sample_rate)
        return wave * envelope
    
    def _apply_envelope(self, wave, sample_rate):
        """Apply ADSR envelope"""
        length = len(wave)
        attack_samples = int(0.01 * sample_rate)  # 10ms attack
        decay_samples = int(0.1 * sample_rate)    # 100ms decay
        release_samples = int(0.2 * sample_rate)  # 200ms release
        
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
        
        return envelope
    
    def _apply_piano_envelope(self, wave, sample_rate):
        """Apply piano-style envelope"""
        length = len(wave)
        attack_samples = int(0.005 * sample_rate)  # Very quick attack
        decay_samples = length - attack_samples    # Long decay
        
        envelope = np.ones(length)
        
        # Quick attack
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Exponential decay
        if decay_samples > 0:
            decay_curve = np.exp(-np.linspace(0, 3, decay_samples))
            envelope[attack_samples:] = decay_curve
        
        return envelope
    
    def _apply_drum_envelope(self, wave, sample_rate):
        """Apply drum-style envelope"""
        length = len(wave)
        attack_samples = int(0.002 * sample_rate)  # Very quick attack
        decay_samples = length - attack_samples    # Quick decay
        
        envelope = np.ones(length)
        
        # Instant attack
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Quick exponential decay
        if decay_samples > 0:
            decay_curve = np.exp(-np.linspace(0, 8, decay_samples))
            envelope[attack_samples:] = decay_curve
        
        return envelope
    
    def note_on(self, channel, note, velocity):
        """Start playing a note"""
        if note in self.note_frequencies:
            frequency = self.note_frequencies[note]
            instrument = self.channel_instruments.get(channel, 'sine')
            
            # Generate a longer sample for sustained notes
            duration = 2.0  # 2 seconds max
            waveform_generator = self.waveforms.get(instrument, self.waveforms['sine'])
            
            if instrument == 'drums':
                duration = 0.5  # Drums are shorter
                wave_data = waveform_generator(frequency, duration, velocity, self.sample_rate)
            else:
                wave_data = waveform_generator(frequency, duration, velocity, self.sample_rate)
            
            # Store the note data
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
        """Generate audio buffer from currently playing notes"""
        buffer = np.zeros(self.buffer_size, dtype=np.float32)
        
        notes_to_remove = []
        
        for note_key, note_data in self.active_notes.items():
            wave_data = note_data['wave_data']
            position = note_data['position']
            
            # Calculate how many samples to add to buffer
            samples_to_add = min(self.buffer_size, len(wave_data) - position)
            
            if samples_to_add > 0:
                # Add the wave data to the buffer
                buffer[:samples_to_add] += wave_data[position:position + samples_to_add]
                
                # Update position
                note_data['position'] += samples_to_add
            
            # Remove notes that have finished playing
            if position >= len(wave_data) or time.time() - note_data['start_time'] > 3.0:
                notes_to_remove.append(note_key)
        
        # Remove finished notes
        for note_key in notes_to_remove:
            if note_key in self.active_notes:
                del self.active_notes[note_key]
        
        # Normalize to prevent clipping
        if np.max(np.abs(buffer)) > 1.0:
            buffer = buffer / np.max(np.abs(buffer)) * 0.9
        
        return buffer
    
    def play_midi_file(self, midi_file, generator):
        """Play a MIDI file through the synthesizer"""
        if self.is_playing:
            self.stop_playback()
        
        self.is_playing = True
        
        def playback_worker():
            # Convert MIDI to our note events
            events = []
            
            for note in generator.notes_data:
                start_time_sec = note['start'] * (60.0 / generator.settings.tempo)  # Convert beats to seconds
                duration_sec = note['duration'] * (60.0 / generator.settings.tempo)
                events.append((start_time_sec, 'note_on', note))
                events.append((start_time_sec + duration_sec, 'note_off', note))
            
            # Sort events by time
            events.sort(key=lambda x: x[0])
            
            start_time = time.time()
            event_index = 0
            
            while self.is_playing and event_index < len(events):
                current_time = time.time() - start_time
                
                # Process events that should happen now
                while event_index < len(events) and events[event_index][0] <= current_time:
                    event_time, event_type, note = events[event_index]
                    
                    if event_type == 'note_on':
                        self.note_on(note['channel'], note['note'], note['velocity'])
                    else:  # note_off
                        self.note_off(note['channel'], note['note'])
                    
                    event_index += 1
                
                # Generate and play audio buffer
                audio_buffer = self.get_audio_buffer()
                
                # Convert to pygame sound format
                audio_buffer_int = (audio_buffer * 32767).astype(np.int16)
                
                # Create stereo buffer
                stereo_buffer = np.zeros((len(audio_buffer_int), 2), dtype=np.int16)
                stereo_buffer[:, 0] = audio_buffer_int  # Left channel
                stereo_buffer[:, 1] = audio_buffer_int  # Right channel
                
                # Play the buffer
                try:
                    sound = pygame.sndarray.make_sound(stereo_buffer)
                    sound.play()
                    
                    # Wait for the buffer duration
                    time.sleep(self.buffer_size / self.sample_rate)
                except:
                    # Handle pygame sound errors gracefully
                    time.sleep(0.01)
            
            self.is_playing = False
        
        self.playback_thread = threading.Thread(target=playback_worker)
        self.playback_thread.daemon = True
        self.playback_thread.start()
    
    def stop_playback(self):
        """Stop MIDI playback"""
        self.is_playing = False
        self.active_notes.clear()
        pygame.mixer.stop()
        
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=1.0)

class MIDIVisualizerWidget:
    """MIDI visualization widget"""
    
    def __init__(self, parent, generator):
        self.parent = parent
        self.generator = generator
        self.fig, self.ax = plt.subplots(figsize=(12, 6), facecolor='#3E3E3E') # Dark background
        self.ax.set_facecolor('#2B2B2B')
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.animation = None
        self.current_time = 0
        self.is_animating = False
        
    def update_visualization(self):
        """Update the visualization with current notes"""
        if not self.generator.notes_data:
            self.ax.clear()
            self.ax.set_xlabel('Time (beats)', color='white')
            self.ax.set_ylabel('MIDI Note Number', color='white')
            self.ax.set_title('MIDI Piano Roll Visualization', color='white')
            self.ax.tick_params(colors='white')
            self.ax.grid(True, alpha=0.2, color='gray')
            self.canvas.draw()
            return
            
        self.ax.clear()
        
        # Piano roll style visualization
        for note in self.generator.notes_data:
            start = note['start']
            duration = note['duration']
            pitch = note['note']
            velocity = note['velocity']
            channel = note['channel']
            
            # Color based on channel and velocity
            if channel == 9:  # Drums
                color = '#FF4136' # Red
                alpha = 0.9
            else:
                # Rainbow colors based on pitch
                hue = (pitch % 12) / 12.0
                color = colorsys.hsv_to_rgb(hue, 0.9, 1.0)
                alpha = 0.5 + (velocity / 127.0) * 0.5
            
            # Draw note rectangle
            rect = plt.Rectangle((start, pitch - 0.5), duration, 1, 
                                  facecolor=color, alpha=alpha, edgecolor='black', linewidth=0.5)
            self.ax.add_patch(rect)
        
        # Styling
        self.ax.set_xlabel('Time (beats)', color='white')
        self.ax.set_ylabel('MIDI Note Number', color='white')
        self.ax.set_title('MIDI Piano Roll Visualization', color='white')
        self.ax.tick_params(colors='white')
        self.ax.grid(True, alpha=0.2, color='gray')
        
        # Set limits
        if self.generator.notes_data:
            max_time = max(note['start'] + note['duration'] for note in self.generator.notes_data)
            min_note = min(note['note'] for note in self.generator.notes_data)
            max_note = max(note['note'] for note in self.generator.notes_data)
            
            self.ax.set_xlim(0, max_time)
            self.ax.set_ylim(min_note - 2, max_note + 2)
        
        self.canvas.draw()
    
    def start_playback_animation(self):
        """Start animated playback visualization"""
        if not self.generator.notes_data or self.is_animating:
            return
            
        self.update_visualization() # Redraw clean slate
        self.current_time = 0
        self.is_animating = True
        
        playback_line = self.ax.axvline(x=0, color='yellow', linewidth=2, alpha=0.8)
        
        start_time = time.time()
        
        def animate(i):
            if not self.is_animating:
                return [playback_line]

            elapsed = time.time() - start_time
            current_beat = elapsed * (self.generator.settings.tempo / 60.0)
            
            playback_line.set_xdata([current_beat, current_beat])

            max_beat = self.ax.get_xlim()[1]
            if current_beat > max_beat:
                self.stop_animation()

            return [playback_line]
        
        self.animation = FuncAnimation(self.fig, animate, interval=33, blit=True, repeat=False)
        self.canvas.draw()
    
    def stop_animation(self):
        """Stop the animation"""
        if self.animation:
            self.animation.event_source.stop()
            self.animation = None
        self.is_animating = False
        self.update_visualization() # Redraw to remove playback line

class MIDIGeneratorGUI:
    """Main GUI application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Ultimate MIDI Generator & Converter")
        self.root.geometry("1400x900")
        
        # Initialize generator and synthesizer
        self.generator = MIDIGenerator()
        self.synthesizer = SoftwareSynthesizer()
        
        # <<< NEW: Initialize MP3 converter >>>
        self.mp3_converter = MP3toMIDIConverter(progress_callback=self.update_progress)
        self.mp3_filepath = None
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        self.setup_ui()
        self.update_ui_from_settings()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Controls
        control_frame = ttk.Frame(main_frame, width=350)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        control_frame.pack_propagate(False)
        
        # Right panel - Visualization
        viz_frame = ttk.Frame(main_frame)
        viz_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.setup_controls(control_frame)
        self.setup_visualization(viz_frame)
        
    def setup_controls(self, parent):
        """Setup control panel"""
        # Notebook for organized tabs
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # <<< NEW: Add MP3 to MIDI Converter Tab >>>
        mp3_frame = ttk.Frame(notebook)
        notebook.add(mp3_frame, text="🎵 MP3 to MIDI")
        self.setup_mp3_converter_tab(mp3_frame)

        # Basic Settings Tab
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="Basic Gen")
        self.setup_basic_controls(basic_frame)
        
        # Rhythm Tab
        rhythm_frame = ttk.Frame(notebook)
        notebook.add(rhythm_frame, text="Rhythm")
        self.setup_rhythm_controls(rhythm_frame)
        
        # Harmony Tab
        harmony_frame = ttk.Frame(notebook)
        notebook.add(harmony_frame, text="Harmony")
        self.setup_harmony_controls(harmony_frame)
        
        # Melody Tab
        melody_frame = ttk.Frame(notebook)
        notebook.add(melody_frame, text="Melody")
        self.setup_melody_controls(melody_frame)
        
        # Effects Tab
        effects_frame = ttk.Frame(notebook)
        notebook.add(effects_frame, text="Effects")
        self.setup_effects_controls(effects_frame)
        
        # Randomizer Tab
        random_frame = ttk.Frame(notebook)
        notebook.add(random_frame, text="Random")
        self.setup_random_controls(random_frame)
        
        # Synthesizer Tab
        synth_frame = ttk.Frame(notebook)
        notebook.add(synth_frame, text="Synthesizer")
        self.setup_synthesizer_controls(synth_frame)
        
        # Action buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Generate Music", 
                   command=self.generate_music).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="▶ Play", 
                   command=self.play_music).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="■ Stop", 
                   command=self.stop_music).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Save MIDI", 
                   command=self.save_midi).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Load Settings", 
                   command=self.load_settings).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Save Settings", 
                   command=self.save_settings).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="Randomize All", 
                   command=self.randomize_all).pack(fill=tk.X, pady=2)
                   
    # <<< NEW: UI setup for the MP3 converter tab >>>
    def setup_mp3_converter_tab(self, parent):
        """Setup the MP3 to MIDI conversion tab controls"""
        main_frame = ttk.Frame(parent, padding=10)
        main_frame.pack(fill="both", expand=True)

        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="1. Select Audio File", padding=10)
        file_frame.pack(fill="x", expand=True, pady=5)
        
        ttk.Button(file_frame, text="Load MP3 or WAV File", 
                   command=self.load_mp3).pack(fill="x", pady=5)
        self.mp3_label = ttk.Label(file_frame, text="No file selected.", wraplength=280)
        self.mp3_label.pack(pady=5)
        
        # Conversion control
        convert_frame = ttk.LabelFrame(main_frame, text="2. Convert", padding=10)
        convert_frame.pack(fill="x", expand=True, pady=5)
        
        ttk.Button(convert_frame, text="✨ Convert to MIDI", 
                   command=self.run_conversion_thread).pack(fill="x", pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(convert_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=(10, 5))
        
        # Description
        info_frame = ttk.LabelFrame(main_frame, text="How it Works", padding=10)
        info_frame.pack(fill="both", expand=True, pady=5)
        
        info_text = ("This tool performs monophonic music transcription. "
                     "It analyzes an audio file to find the most prominent "
                     "melody line.\n\n• Best for: Vocals, solo instruments.\n"
                     "• Not for: Full bands, complex chords.\n\n"
                     "The result will be loaded and can be played or saved like generated music.")
        ttk.Label(info_frame, text=info_text, wraplength=280, justify="left").pack()

    def setup_basic_controls(self, parent):
        """Setup basic controls"""
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Tempo
        ttk.Label(scrollable_frame, text="Tempo (BPM):").pack(anchor=tk.W)
        self.tempo_var = tk.IntVar(value=self.generator.settings.tempo)
        ttk.Scale(scrollable_frame, from_=60, to=200, variable=self.tempo_var, 
                  orient=tk.HORIZONTAL, command=self.update_tempo).pack(fill=tk.X)
        
        # Key Signature
        ttk.Label(scrollable_frame, text="Key:").pack(anchor=tk.W)
        self.key_var = tk.StringVar(value=self.generator.settings.key_signature)
        key_combo = ttk.Combobox(scrollable_frame, textvariable=self.key_var, 
                                 values=["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])
        key_combo.bind('<<ComboboxSelected>>', self.update_key)
        key_combo.pack(fill=tk.X)
        
        # Scale Type
        ttk.Label(scrollable_frame, text="Scale:").pack(anchor=tk.W)
        self.scale_var = tk.StringVar(value=self.generator.settings.scale_type)
        scale_combo = ttk.Combobox(scrollable_frame, textvariable=self.scale_var, 
                                   values=list(self.generator.scales.keys()))
        scale_combo.bind('<<ComboboxSelected>>', self.update_scale)
        scale_combo.pack(fill=tk.X)
        
        # Note Range
        ttk.Label(scrollable_frame, text="Note Range Low:").pack(anchor=tk.W)
        self.note_low_var = tk.IntVar(value=self.generator.settings.note_range_low)
        ttk.Scale(scrollable_frame, from_=24, to=96, variable=self.note_low_var, 
                  orient=tk.HORIZONTAL, command=self.update_note_range).pack(fill=tk.X)
        
        ttk.Label(scrollable_frame, text="Note Range High:").pack(anchor=tk.W)
        self.note_high_var = tk.IntVar(value=self.generator.settings.note_range_high)
        ttk.Scale(scrollable_frame, from_=48, to=120, variable=self.note_high_var, 
                  orient=tk.HORIZONTAL, command=self.update_note_range).pack(fill=tk.X)
        
        # Song Length
        ttk.Label(scrollable_frame, text="Song Length (bars):").pack(anchor=tk.W)
        self.song_length_var = tk.IntVar(value=self.generator.settings.song_length_bars)
        ttk.Scale(scrollable_frame, from_=8, to=128, variable=self.song_length_var, 
                  orient=tk.HORIZONTAL, command=self.update_song_length).pack(fill=tk.X)
    
    def setup_rhythm_controls(self, parent):
        """Setup rhythm controls"""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Swing Factor
        ttk.Label(scrollable_frame, text="Swing Factor:").pack(anchor=tk.W)
        self.swing_var = tk.DoubleVar(value=self.generator.settings.swing_factor)
        ttk.Scale(scrollable_frame, from_=0, to=1, variable=self.swing_var, 
                  orient=tk.HORIZONTAL, command=self.update_swing).pack(fill=tk.X)
        
        # Rest Probability
        ttk.Label(scrollable_frame, text="Rest Probability:").pack(anchor=tk.W)
        self.rest_prob_var = tk.DoubleVar(value=self.generator.settings.rest_probability)
        ttk.Scale(scrollable_frame, from_=0, to=0.5, variable=self.rest_prob_var, 
                  orient=tk.HORIZONTAL, command=self.update_rest_prob).pack(fill=tk.X)
        
        # Syncopation Probability
        ttk.Label(scrollable_frame, text="Syncopation:").pack(anchor=tk.W)
        self.sync_var = tk.DoubleVar(value=self.generator.settings.syncopation_prob)
        ttk.Scale(scrollable_frame, from_=0, to=0.5, variable=self.sync_var, 
                  orient=tk.HORIZONTAL, command=self.update_syncopation).pack(fill=tk.X)
        
        # Triplet Probability
        ttk.Label(scrollable_frame, text="Triplets:").pack(anchor=tk.W)
        self.triplet_var = tk.DoubleVar(value=self.generator.settings.triplet_probability)
        ttk.Scale(scrollable_frame, from_=0, to=0.3, variable=self.triplet_var, 
                  orient=tk.HORIZONTAL, command=self.update_triplets).pack(fill=tk.X)
        
        # Dotted Notes
        ttk.Label(scrollable_frame, text="Dotted Notes:").pack(anchor=tk.W)
        self.dotted_var = tk.DoubleVar(value=self.generator.settings.dotted_note_prob)
        ttk.Scale(scrollable_frame, from_=0, to=0.3, variable=self.dotted_var, 
                  orient=tk.HORIZONTAL, command=self.update_dotted).pack(fill=tk.X)
    
    def setup_harmony_controls(self, parent):
        """Setup harmony controls"""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Chord Progression Style
        ttk.Label(scrollable_frame, text="Chord Progression:").pack(anchor=tk.W)
        self.chord_prog_var = tk.StringVar(value=self.generator.settings.chord_progression_style)
        chord_combo = ttk.Combobox(scrollable_frame, textvariable=self.chord_prog_var, 
                                   values=list(self.generator.chord_progressions.keys()))
        chord_combo.bind('<<ComboboxSelected>>', self.update_chord_prog)
        chord_combo.pack(fill=tk.X)
        
        # Bass Line Style
        ttk.Label(scrollable_frame, text="Bass Style:").pack(anchor=tk.W)
        self.bass_style_var = tk.StringVar(value=self.generator.settings.bass_line_style)
        bass_combo = ttk.Combobox(scrollable_frame, textvariable=self.bass_style_var, 
                                  values=["root", "walking", "alternating"])
        bass_combo.bind('<<ComboboxSelected>>', self.update_bass_style)
        bass_combo.pack(fill=tk.X)
        
        # Chord Complexity
        ttk.Label(scrollable_frame, text="Chord Complexity:").pack(anchor=tk.W)
        self.chord_complex_var = tk.IntVar(value=self.generator.settings.chord_complexity)
        ttk.Scale(scrollable_frame, from_=3, to=7, variable=self.chord_complex_var, 
                  orient=tk.HORIZONTAL, command=self.update_chord_complexity).pack(fill=tk.X)
    
    def setup_melody_controls(self, parent):
        """Setup melody controls"""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Melody Direction Bias
        ttk.Label(scrollable_frame, text="Direction Bias (-1=down, +1=up):").pack(anchor=tk.W)
        self.direction_var = tk.DoubleVar(value=self.generator.settings.melody_direction_bias)
        ttk.Scale(scrollable_frame, from_=-1, to=1, variable=self.direction_var, 
                  orient=tk.HORIZONTAL, command=self.update_direction).pack(fill=tk.X)
        
        # Leap Probability
        ttk.Label(scrollable_frame, text="Large Intervals:").pack(anchor=tk.W)
        self.leap_var = tk.DoubleVar(value=self.generator.settings.leap_probability)
        ttk.Scale(scrollable_frame, from_=0, to=0.5, variable=self.leap_var, 
                  orient=tk.HORIZONTAL, command=self.update_leap).pack(fill=tk.X)
        
        # Repetition Factor
        ttk.Label(scrollable_frame, text="Repetition:").pack(anchor=tk.W)
        self.repeat_var = tk.DoubleVar(value=self.generator.settings.repetition_factor)
        ttk.Scale(scrollable_frame, from_=0, to=1, variable=self.repeat_var, 
                  orient=tk.HORIZONTAL, command=self.update_repetition).pack(fill=tk.X)
        
        # Sequence Probability
        ttk.Label(scrollable_frame, text="Sequences:").pack(anchor=tk.W)
        self.sequence_var = tk.DoubleVar(value=self.generator.settings.sequence_probability)
        ttk.Scale(scrollable_frame, from_=0, to=0.5, variable=self.sequence_var, 
                  orient=tk.HORIZONTAL, command=self.update_sequence).pack(fill=tk.X)
    
    def setup_effects_controls(self, parent):
        """Setup effects controls"""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Velocity Range
        ttk.Label(scrollable_frame, text="Velocity Min:").pack(anchor=tk.W)
        self.vel_min_var = tk.IntVar(value=self.generator.settings.note_velocity_min)
        ttk.Scale(scrollable_frame, from_=1, to=100, variable=self.vel_min_var, 
                  orient=tk.HORIZONTAL, command=self.update_velocity).pack(fill=tk.X)
        
        ttk.Label(scrollable_frame, text="Velocity Max:").pack(anchor=tk.W)
        self.vel_max_var = tk.IntVar(value=self.generator.settings.note_velocity_max)
        ttk.Scale(scrollable_frame, from_=50, to=127, variable=self.vel_max_var, 
                  orient=tk.HORIZONTAL, command=self.update_velocity).pack(fill=tk.X)
        
        # Accent Probability
        ttk.Label(scrollable_frame, text="Accents:").pack(anchor=tk.W)
        self.accent_var = tk.DoubleVar(value=self.generator.settings.accent_probability)
        ttk.Scale(scrollable_frame, from_=0, to=0.5, variable=self.accent_var, 
                  orient=tk.HORIZONTAL, command=self.update_accent).pack(fill=tk.X)
        
        # Ghost Notes
        ttk.Label(scrollable_frame, text="Ghost Notes:").pack(anchor=tk.W)
        self.ghost_var = tk.DoubleVar(value=self.generator.settings.ghost_note_prob)
        ttk.Scale(scrollable_frame, from_=0, to=0.2, variable=self.ghost_var, 
                  orient=tk.HORIZONTAL, command=self.update_ghost).pack(fill=tk.X)
        
        # Dynamic Range
        ttk.Label(scrollable_frame, text="Dynamic Range:").pack(anchor=tk.W)
        self.dynamic_var = tk.DoubleVar(value=self.generator.settings.dynamic_range)
        ttk.Scale(scrollable_frame, from_=0, to=1, variable=self.dynamic_var, 
                  orient=tk.HORIZONTAL, command=self.update_dynamic).pack(fill=tk.X)
    
    def setup_random_controls(self, parent):
        """Setup randomization controls"""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Chaos Factor
        ttk.Label(scrollable_frame, text="Chaos Factor:").pack(anchor=tk.W)
        self.chaos_var = tk.DoubleVar(value=self.generator.settings.chaos_factor)
        ttk.Scale(scrollable_frame, from_=0, to=0.5, variable=self.chaos_var, 
                  orient=tk.HORIZONTAL, command=self.update_chaos).pack(fill=tk.X)
        
        # Mutation Rate
        ttk.Label(scrollable_frame, text="Mutation Rate:").pack(anchor=tk.W)
        self.mutation_var = tk.DoubleVar(value=self.generator.settings.mutation_rate)
        ttk.Scale(scrollable_frame, from_=0, to=0.2, variable=self.mutation_var, 
                  orient=tk.HORIZONTAL, command=self.update_mutation).pack(fill=tk.X)
        
        # Random buttons
        ttk.Button(scrollable_frame, text="Random Tempo", 
                   command=self.random_tempo).pack(fill=tk.X, pady=2)
        ttk.Button(scrollable_frame, text="Random Key", 
                   command=self.random_key).pack(fill=tk.X, pady=2)
        ttk.Button(scrollable_frame, text="Random Scale", 
                   command=self.random_scale).pack(fill=tk.X, pady=2)
        ttk.Button(scrollable_frame, text="Random Rhythm", 
                   command=self.random_rhythm).pack(fill=tk.X, pady=2)
        ttk.Button(scrollable_frame, text="Random Harmony", 
                   command=self.random_harmony).pack(fill=tk.X, pady=2)
        ttk.Button(scrollable_frame, text="Random Melody", 
                   command=self.random_melody).pack(fill=tk.X, pady=2)
    
    def setup_visualization(self, parent):
        """Setup visualization panel"""
        viz_label = ttk.Label(parent, text="MIDI Visualization", font=("Arial", 14, "bold"))
        viz_label.pack(pady=5)
        
        # Visualization controls
        viz_controls = ttk.Frame(parent)
        viz_controls.pack(fill=tk.X, pady=5)
        
        # Create visualizer
        self.visualizer = MIDIVisualizerWidget(parent, self.generator)
    
    def setup_synthesizer_controls(self, parent):
        """Setup synthesizer controls"""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Synthesizer info
        info_label = ttk.Label(scrollable_frame, text="🎵 Built-in Software Synthesizer 🎵", 
                               font=("Arial", 12, "bold"))
        info_label.pack(pady=10)
        
        desc_label = ttk.Label(scrollable_frame, 
                               text="No external MIDI hardware needed!\nReal-time audio synthesis with multiple instruments.",
                               justify="center")
        desc_label.pack(pady=5)
        
        # Instrument assignments
        ttk.Label(scrollable_frame, text="Instrument Assignments:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10,5))
        
        # Melody instrument
        ttk.Label(scrollable_frame, text="Melody (Channel 0):").pack(anchor=tk.W)
        self.melody_instrument_var = tk.StringVar(value="piano")
        melody_combo = ttk.Combobox(scrollable_frame, textvariable=self.melody_instrument_var,
                                      values=["piano", "sine", "triangle", "square", "sawtooth"])
        melody_combo.bind('<<ComboboxSelected>>', self.update_melody_instrument)
        melody_combo.pack(fill=tk.X, pady=2)
        
        # Bass instrument
        ttk.Label(scrollable_frame, text="Bass (Channel 1):").pack(anchor=tk.W)
        self.bass_instrument_var = tk.StringVar(value="sawtooth")
        bass_combo = ttk.Combobox(scrollable_frame, textvariable=self.bass_instrument_var,
                                      values=["sawtooth", "square", "sine", "triangle"])
        bass_combo.bind('<<ComboboxSelected>>', self.update_bass_instrument)
        bass_combo.pack(fill=tk.X, pady=2)
        
        # Pad instrument
        ttk.Label(scrollable_frame, text="Pad (Channel 2):").pack(anchor=tk.W)
        self.pad_instrument_var = tk.StringVar(value="sine")
        pad_combo = ttk.Combobox(scrollable_frame, textvariable=self.pad_instrument_var,
                                      values=["sine", "triangle", "piano", "square"])
        pad_combo.bind('<<ComboboxSelected>>', self.update_pad_instrument)
        pad_combo.pack(fill=tk.X, pady=2)
        
        # Drums info
        ttk.Label(scrollable_frame, text="Drums (Channel 9): Built-in drum sounds", 
                  font=("Arial", 10)).pack(anchor=tk.W, pady=(10,0))
        
        # Audio settings
        ttk.Label(scrollable_frame, text="Audio Settings:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(20,5))
        
        # Volume control (future enhancement)
        ttk.Label(scrollable_frame, text="Master Volume:").pack(anchor=tk.W)
        self.volume_var = tk.DoubleVar(value=0.7)
        ttk.Scale(scrollable_frame, from_=0, to=1, variable=self.volume_var,
                  orient=tk.HORIZONTAL, command=self.update_volume).pack(fill=tk.X, pady=2)
        
        # Audio info
        info_frame = ttk.LabelFrame(scrollable_frame, text="Audio Info", padding=10)
        info_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(info_frame, text="• Sample Rate: 44.1 kHz").pack(anchor=tk.W)
        ttk.Label(info_frame, text="• Buffer Size: 512 samples").pack(anchor=tk.W)
        ttk.Label(info_frame, text="• Channels: Stereo").pack(anchor=tk.W)
        ttk.Label(info_frame, text="• Real-time synthesis").pack(anchor=tk.W)
        
        # Quick test buttons
        test_frame = ttk.LabelFrame(scrollable_frame, text="Quick Tests", padding=10)
        test_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(test_frame, text="Test Piano Note", 
                   command=self.test_piano_note).pack(fill=tk.X, pady=2)
        ttk.Button(test_frame, text="Test Bass Note", 
                   command=self.test_bass_note).pack(fill=tk.X, pady=2)
        ttk.Button(test_frame, text="Test Drum Sound", 
                   command=self.test_drum_sound).pack(fill=tk.X, pady=2)
                   
    # <<< NEW: Methods for the MP3 to MIDI converter >>>
    def load_mp3(self):
        """Open a file dialog to select an MP3 or WAV file."""
        filepath = filedialog.askopenfilename(
            title="Select an Audio File",
            filetypes=[("Audio Files", "*.mp3 *.wav"), ("All files", "*.*")]
        )
        if filepath:
            self.mp3_filepath = filepath
            filename = os.path.basename(filepath)
            self.mp3_label.config(text=filename)
            messagebox.showinfo("File Selected", f"Loaded: {filename}")
    
    def run_conversion_thread(self):
        """Run the MP3 conversion in a separate thread to avoid freezing the GUI."""
        if not self.mp3_filepath:
            messagebox.showwarning("No File", "Please load an audio file first.")
            return

        # Disable button to prevent multiple clicks
        # This will require accessing the button, which we can do by assigning it to self
        # For now, we'll just rely on user behavior.
        
        thread = threading.Thread(target=self.convert_mp3_to_midi)
        thread.daemon = True
        thread.start()

    def convert_mp3_to_midi(self):
        """The core conversion logic that runs in a thread."""
        self.update_progress(0)
        
        # The convert method now returns the note data directly
        notes_data = self.mp3_converter.convert(self.mp3_filepath)

        if not notes_data:
            self.root.after(0, lambda: messagebox.showinfo("Conversion Info", "Could not detect any notes in the audio file."))
            self.update_progress(0)
            return

        # Update the main generator's data
        self.generator.notes_data = notes_data
        
        # Find the estimated tempo to set for playback
        y, sr = librosa.load(self.mp3_filepath)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)[0]
        self.generator.settings.tempo = int(tempo)

        self.generator.current_midi = self.generator.create_midi_file(notes_data)

        # Schedule the UI update to run on the main thread
        self.root.after(0, self.on_conversion_complete)
        
    def on_conversion_complete(self):
        """Actions to perform on the main GUI thread after conversion is done."""
        self.update_visualization()
        self.update_ui_from_settings() # Update tempo slider
        messagebox.showinfo("Success", "MP3 to MIDI conversion complete! The result is loaded and ready to play or save.")
        
    def update_progress(self, value):
        """Thread-safe method to update the progress bar."""
        if hasattr(self, 'progress_var'):
            self.progress_var.set(value)

    def update_melody_instrument(self, event=None):
        """Update melody instrument"""
        self.synthesizer.channel_instruments[0] = self.melody_instrument_var.get()
    
    def update_bass_instrument(self, event=None):
        """Update bass instrument"""
        self.synthesizer.channel_instruments[1] = self.bass_instrument_var.get()
    
    def update_pad_instrument(self, event=None):
        """Update pad instrument"""
        self.synthesizer.channel_instruments[2] = self.pad_instrument_var.get()
    
    def update_volume(self, value):
        """Update master volume (placeholder for future enhancement)"""
        # This could be implemented to scale all audio output
        pass
    
    def test_piano_note(self):
        """Test play a piano note"""
        try:
            self.synthesizer.note_on(0, 60, 80)  # Middle C
            threading.Timer(1.0, lambda: self.synthesizer.note_off(0, 60)).start()
        except Exception as e:
            messagebox.showerror("Test Error", f"Could not test piano: {str(e)}")
    
    def test_bass_note(self):
        """Test play a bass note"""
        try:
            self.synthesizer.note_on(1, 36, 100)  # Low C
            threading.Timer(1.0, lambda: self.synthesizer.note_off(1, 36)).start()
        except Exception as e:
            messagebox.showerror("Test Error", f"Could not test bass: {str(e)}")
    
    def test_drum_sound(self):
        """Test play a drum sound"""
        try:
            self.synthesizer.note_on(9, 36, 120)  # Kick drum
            threading.Timer(0.5, lambda: self.synthesizer.note_off(9, 36)).start()
        except Exception as e:
            messagebox.showerror("Test Error", f"Could not test drums: {str(e)}")
    
    # Update methods for all controls
    def update_tempo(self, value):
        self.generator.settings.tempo = int(float(value))
    
    def update_key(self, event=None):
        self.generator.settings.key_signature = self.key_var.get()
    
    def update_scale(self, event=None):
        self.generator.settings.scale_type = self.scale_var.get()
    
    def update_note_range(self, value):
        self.generator.settings.note_range_low = self.note_low_var.get()
        self.generator.settings.note_range_high = self.note_high_var.get()
    
    def update_song_length(self, value):
        self.generator.settings.song_length_bars = int(float(value))
    
    def update_swing(self, value):
        self.generator.settings.swing_factor = float(value)
    
    def update_rest_prob(self, value):
        self.generator.settings.rest_probability = float(value)
    
    def update_syncopation(self, value):
        self.generator.settings.syncopation_prob = float(value)
    
    def update_triplets(self, value):
        self.generator.settings.triplet_probability = float(value)
    
    def update_dotted(self, value):
        self.generator.settings.dotted_note_prob = float(value)
    
    def update_chord_prog(self, event=None):
        self.generator.settings.chord_progression_style = self.chord_prog_var.get()
    
    def update_bass_style(self, event=None):
        self.generator.settings.bass_line_style = self.bass_style_var.get()
    
    def update_chord_complexity(self, value):
        self.generator.settings.chord_complexity = int(float(value))
    
    def update_direction(self, value):
        self.generator.settings.melody_direction_bias = float(value)
    
    def update_leap(self, value):
        self.generator.settings.leap_probability = float(value)
    
    def update_repetition(self, value):
        self.generator.settings.repetition_factor = float(value)
    
    def update_sequence(self, value):
        self.generator.settings.sequence_probability = float(value)
    
    def update_velocity(self, value):
        self.generator.settings.note_velocity_min = self.vel_min_var.get()
        self.generator.settings.note_velocity_max = self.vel_max_var.get()
    
    def update_accent(self, value):
        self.generator.settings.accent_probability = float(value)
    
    def update_ghost(self, value):
        self.generator.settings.ghost_note_prob = float(value)
    
    def update_dynamic(self, value):
        self.generator.settings.dynamic_range = float(value)
    
    def update_chaos(self, value):
        self.generator.settings.chaos_factor = float(value)
    
    def update_mutation(self, value):
        self.generator.settings.mutation_rate = float(value)
    
    # Random button methods
    def random_tempo(self):
        self.tempo_var.set(random.randint(60, 180))
        self.update_tempo(self.tempo_var.get())
    
    def random_key(self):
        key = random.choice(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])
        self.key_var.set(key)
        self.update_key()
    
    def random_scale(self):
        scale = random.choice(list(self.generator.scales.keys()))
        self.scale_var.set(scale)
        self.update_scale()
    
    def random_rhythm(self):
        self.swing_var.set(random.uniform(0, 0.5))
        self.rest_prob_var.set(random.uniform(0, 0.4))
        self.sync_var.set(random.uniform(0, 0.3))
        self.triplet_var.set(random.uniform(0, 0.3))
        self.dotted_var.set(random.uniform(0, 0.3))
        self.update_swing(self.swing_var.get())
        self.update_rest_prob(self.rest_prob_var.get())
        self.update_syncopation(self.sync_var.get())
        self.update_triplets(self.triplet_var.get())
        self.update_dotted(self.dotted_var.get())
    
    def random_harmony(self):
        prog = random.choice(list(self.generator.chord_progressions.keys()))
        style = random.choice(["root", "walking", "alternating"])
        self.chord_prog_var.set(prog)
        self.bass_style_var.set(style)
        self.chord_complex_var.set(random.randint(3, 6))
        self.update_chord_prog()
        self.update_bass_style()
        self.update_chord_complexity(self.chord_complex_var.get())
    
    def random_melody(self):
        self.direction_var.set(random.uniform(-1, 1))
        self.leap_var.set(random.uniform(0, 0.5))
        self.repeat_var.set(random.uniform(0, 1))
        self.sequence_var.set(random.uniform(0, 0.5))
        self.update_direction(self.direction_var.get())
        self.update_leap(self.leap_var.get())
        self.update_repetition(self.repeat_var.get())
        self.update_sequence(self.sequence_var.get())
    
    def randomize_all(self):
        """Randomize all settings"""
        self.generator.randomize_settings()
        self.update_ui_from_settings()
    
    def update_ui_from_settings(self):
        """Update UI controls from current settings"""
        self.tempo_var.set(self.generator.settings.tempo)
        self.key_var.set(self.generator.settings.key_signature)
        self.scale_var.set(self.generator.settings.scale_type)
        self.note_low_var.set(self.generator.settings.note_range_low)
        self.note_high_var.set(self.generator.settings.note_range_high)
        self.song_length_var.set(self.generator.settings.song_length_bars)
        self.swing_var.set(self.generator.settings.swing_factor)
        self.rest_prob_var.set(self.generator.settings.rest_probability)
        self.sync_var.set(self.generator.settings.syncopation_prob)
        self.triplet_var.set(self.generator.settings.triplet_probability)
        self.dotted_var.set(self.generator.settings.dotted_note_prob)
        self.chord_prog_var.set(self.generator.settings.chord_progression_style)
        self.bass_style_var.set(self.generator.settings.bass_line_style)
        self.chord_complex_var.set(self.generator.settings.chord_complexity)
        self.direction_var.set(self.generator.settings.melody_direction_bias)
        self.leap_var.set(self.generator.settings.leap_probability)
        self.repeat_var.set(self.generator.settings.repetition_factor)
        self.sequence_var.set(self.generator.settings.sequence_probability)
        self.vel_min_var.set(self.generator.settings.note_velocity_min)
        self.vel_max_var.set(self.generator.settings.note_velocity_max)
        self.accent_var.set(self.generator.settings.accent_probability)
        self.ghost_var.set(self.generator.settings.ghost_note_prob)
        self.dynamic_var.set(self.generator.settings.dynamic_range)
        self.chaos_var.set(self.generator.settings.chaos_factor)
        self.mutation_var.set(self.generator.settings.mutation_rate)
    
    # Action methods
    def generate_music(self):
        """Generate new music"""
        try:
            self.stop_music()
            self.generator.generate_music()
            self.update_visualization()
            messagebox.showinfo("Success", "Music generated successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate music: {str(e)}")
    
    def play_music(self):
        """Play the generated music"""
        if not self.generator.current_midi:
            messagebox.showwarning("No Music", "Please generate or convert music first!")
            return
        
        try:
            # Start animation and playback
            self.visualizer.start_playback_animation()
            self.synthesizer.play_midi_file(self.generator.current_midi, self.generator)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to play music: {str(e)}")
    
    def stop_music(self):
        """Stop music playback"""
        self.visualizer.stop_animation()
        self.synthesizer.stop_playback()
    
    def save_midi(self):
        """Save MIDI file"""
        if not self.generator.current_midi:
            messagebox.showwarning("No Music", "Please generate or convert music first!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".mid",
            filetypes=[("MIDI files", "*.mid"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.generator.current_midi.save(filename)
                messagebox.showinfo("Success", f"MIDI file saved as {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save MIDI: {str(e)}")
    
    def save_settings(self):
        """Save current settings to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Create a dictionary from the dataclass
                settings_dict = self.generator.settings.__dict__
                
                with open(filename, 'w') as f:
                    json.dump(settings_dict, f, indent=4)
                
                messagebox.showinfo("Success", f"Settings saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def load_settings(self):
        """Load settings from file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    settings_dict = json.load(f)
                
                # Update settings
                for key, value in settings_dict.items():
                    if hasattr(self.generator.settings, key):
                        setattr(self.generator.settings, key, value)
                
                # Update UI
                self.update_ui_from_settings()
                
                messagebox.showinfo("Success", f"Settings loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load settings: {str(e)}")
    
    def update_visualization(self):
        """Update the visualization"""
        self.visualizer.update_visualization()
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    # Create and run the application
    app = MIDIGeneratorGUI()
    app.run()