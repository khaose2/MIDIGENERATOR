"""
Ultimate MIDI Generator - Professional Edition
Advanced MIDI generation with real-time audio synthesis
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser, scrolledtext
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
from software_synthesizer import SoftwareSynthesizer

# Check for MP3 conversion capabilities
try:
    import librosa
    import soundfile
    from mp3_to_midi_converter import MP3ToMIDIConverter
    MP3_CONVERSION_AVAILABLE = True
    print("✅ MP3 to MIDI conversion available")
except ImportError as e:
    MP3_CONVERSION_AVAILABLE = False
    print(f"⚠️ MP3 conversion disabled - missing dependencies: {e}")

# Import digital keyboard
try:
    from digital_keyboard import DigitalKeyboard, DigitalKeyboardWindow
    DIGITAL_KEYBOARD_AVAILABLE = True
    print("✅ Digital Keyboard available")
except ImportError as e:
    DIGITAL_KEYBOARD_AVAILABLE = False
    print(f"⚠️ Digital Keyboard disabled - missing dependencies: {e}")

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
        
        # Create and store MIDI file
        self.current_midi = self.create_midi_file(all_notes)
        return self.current_midi
    
    def create_midi_file(self, notes_data):
        """Create a MIDI file from note data"""
        if not notes_data:
            return None
            
        mid = mido.MidiFile(ticks_per_beat=480)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        # Group notes by channel
        channel_notes = {}
        for note in notes_data:
            channel = note.get('channel', 0)
            if channel not in channel_notes:
                channel_notes[channel] = []
            channel_notes[channel].append(note)
        
        # Create notes for each channel
        for channel, notes in channel_notes.items():
            notes.sort(key=lambda x: x['start'])
            current_time = 0
            
            for note in notes:
                # Calculate delta time
                start_ticks = int(note['start'] * 480)  # Convert beats to ticks
                delta_time = start_ticks - current_time
                
                # Note on
                track.append(mido.Message('note_on', channel=channel, 
                                        note=note['note'], velocity=note['velocity'], 
                                        time=delta_time))
                
                # Note off
                duration_ticks = int(note['duration'] * 480)
                track.append(mido.Message('note_off', channel=channel, 
                                        note=note['note'], velocity=0, 
                                        time=duration_ticks))
                
                current_time = start_ticks + duration_ticks
        
        # Store notes_data for later use
        self.notes_data = []
        self.current_midi = None
        
        print("✅ MIDI Generator initialized with improved orchestration")
    
    def randomize_settings(self):
        """Randomize all settings for variety"""
        scales = list(self.scales.keys())
        keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        
        self.settings.tempo = random.randint(60, 180)
        self.settings.key_signature = random.choice(keys)
        self.settings.scale_type = random.choice(scales)
        self.settings.song_length_bars = random.randint(16, 64)
        self.settings.swing_factor = random.uniform(0.0, 0.3)
        self.settings.rest_probability = random.uniform(0.1, 0.4)
        self.settings.chaos_factor = random.uniform(0.0, 0.4)
        
        print(f"🎲 Settings randomized: {self.settings.tempo} BPM, {self.settings.key_signature} {self.settings.scale_type}")
    
    def create_midi_file(self, notes_data):
        """Create a MIDI file from note data"""
        if not notes_data:
            return None
            
        mid = mido.MidiFile(ticks_per_beat=480)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        # Group notes by channel
        channel_notes = {}
        for note in notes_data:
            channel = note.get('channel', 0)
            if channel not in channel_notes:
                channel_notes[channel] = []
            channel_notes[channel].append(note)
        
        # Create notes for each channel
        for channel, notes in channel_notes.items():
            notes.sort(key=lambda x: x['start'])
            current_time = 0
            
            for note in notes:
                # Calculate delta time
                start_ticks = int(note['start'] * 480)  # Convert beats to ticks
                delta_time = start_ticks - current_time
                
                # Note on
                track.append(mido.Message('note_on', channel=channel, 
                                        note=note['note'], velocity=note['velocity'], 
                                        time=delta_time))
                
                # Note off
                duration_ticks = int(note['duration'] * 480)
                track.append(mido.Message('note_off', channel=channel, 
                                        note=note['note'], velocity=0, 
                                        time=duration_ticks))
                
                current_time = start_ticks + duration_ticks
        
        return mid

    def load_midi_file(self, midi_path):
        """Load MIDI file and extract notes"""
        try:
            midi_file = mido.MidiFile(midi_path)
            self.notes_data = []
            
            # Extract notes from MIDI file
            current_time = 0
            for track in midi_file.tracks:
                track_time = 0
                active_notes = {}  # Track note_on events
                
                for msg in track:
                    track_time += msg.time
                    
                    if msg.type == 'note_on' and msg.velocity > 0:
                        # Start of a note
                        note_key = (msg.channel, msg.note)
                        active_notes[note_key] = {
                            'note': msg.note,
                            'start': track_time / midi_file.ticks_per_beat,
                            'velocity': msg.velocity,
                            'channel': msg.channel
                        }
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        # End of a note
                        note_key = (msg.channel, msg.note)
                        if note_key in active_notes:
                            note_data = active_notes[note_key]
                            duration = (track_time / midi_file.ticks_per_beat) - note_data['start']
                            note_data['duration'] = max(0.1, duration)  # Ensure minimum duration
                            
                            self.notes_data.append(note_data)
                            del active_notes[note_key]
            
            # Store MIDI file
            self.current_midi = midi_file
            return True
        except Exception as e:
            print(f"Error loading MIDI file: {e}")
            return False


class MIDIGeneratorGUI:
    """Full-featured GUI application class for the MIDI Generator"""
    
    def __init__(self):
        # Initialize components
        self.generator = MIDIGenerator()
        self.synthesizer = SoftwareSynthesizer()
        
        # Initialize GUI
        import tkinter as tk
        self.root = tk.Tk()
        self.root.title("Ultimate MIDI Generator - Professional Edition")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initialize control variables
        self.init_variables()
        
        # Create tabs
        self.create_main_tab()
        self.create_settings_tab()
        self.create_advanced_tab()
        self.create_audio_tab()
        if DIGITAL_KEYBOARD_AVAILABLE:
            self.create_keyboard_tab()
        
        # Create creative generation tab if MP3 conversion is available
        if MP3_CONVERSION_AVAILABLE:
            self.create_creative_tab()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - All audio systems operational")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, 
                                  relief=tk.SUNKEN, anchor=tk.W, bg="lightgray")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        print("✅ Full-featured MIDIGeneratorGUI initialized successfully")
        print("✅ All audio components loaded and working")
    
    def init_variables(self):
        """Initialize all control variables"""
        import tkinter as tk
        
        # Basic settings
        self.tempo_var = tk.IntVar(value=120)
        self.key_var = tk.StringVar(value="C")
        self.scale_var = tk.StringVar(value="major")
        self.song_length_var = tk.IntVar(value=32)
        
        # Musical settings
        self.note_low_var = tk.IntVar(value=60)
        self.note_high_var = tk.IntVar(value=84)
        self.swing_var = tk.DoubleVar(value=0.0)
        self.rest_prob_var = tk.DoubleVar(value=0.2)
        self.chaos_var = tk.DoubleVar(value=0.1)
        
        # Instrument settings
        self.melody_instrument_var = tk.StringVar(value="piano")
        self.bass_instrument_var = tk.StringVar(value="sawtooth")
        self.pad_instrument_var = tk.StringVar(value="sine")
        
        # Audio settings
        self.volume_var = tk.DoubleVar(value=0.7)
        self.filter_cutoff_var = tk.DoubleVar(value=20000)
        self.stereo_width_var = tk.DoubleVar(value=0.5)
        
        # Additional MIDI settings for settings tab
        self.velocity_var = tk.IntVar(value=80)
        self.channel_var = tk.IntVar(value=1)
        self.num_notes_var = tk.IntVar(value=50)
    
    def create_main_tab(self):
        """Create the main control tab"""
        import tkinter as tk
        
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Main Controls")
        
        # Title
        title_label = tk.Label(main_frame, text="🎵 Ultimate MIDI Generator 🎵", 
                              font=("Arial", 20, "bold"), fg="navy")
        title_label.pack(pady=20)
        
        # Main controls frame
        controls_frame = ttk.LabelFrame(main_frame, text="Generation Controls", padding=10)
        controls_frame.pack(pady=10, padx=20, fill="x")
        
        # Generate button
        generate_btn = tk.Button(controls_frame, text="🎼 Generate New Music", 
                                command=self.generate_music, font=("Arial", 14, "bold"),
                                bg="lightgreen", fg="darkgreen", pady=10)
        generate_btn.pack(pady=10, fill="x")
        
        # Playback controls
        playback_frame = ttk.LabelFrame(main_frame, text="Playback Controls", padding=10)
        playback_frame.pack(pady=10, padx=20, fill="x")
        
        play_frame = tk.Frame(playback_frame)
        play_frame.pack(fill="x")
        
        play_btn = tk.Button(play_frame, text="▶ Play", command=self.play_music,
                            font=("Arial", 12), bg="lightblue", fg="navy", width=15)
        play_btn.pack(side="left", padx=5)
        
        stop_btn = tk.Button(play_frame, text="⏹ Stop", command=self.stop_music,
                            font=("Arial", 12), bg="lightcoral", fg="darkred", width=15)
        stop_btn.pack(side="left", padx=5)
        
        # Quick settings frame
        quick_frame = ttk.LabelFrame(main_frame, text="Quick Settings", padding=10)
        quick_frame.pack(pady=10, padx=20, fill="x")
        
        # Tempo
        tempo_frame = tk.Frame(quick_frame)
        tempo_frame.pack(fill="x", pady=5)
        tk.Label(tempo_frame, text="Tempo:", width=15, anchor="w").pack(side="left")
        tempo_scale = tk.Scale(tempo_frame, from_=60, to=180, orient="horizontal",
                              variable=self.tempo_var, command=self.update_tempo)
        tempo_scale.pack(side="left", fill="x", expand=True)
        tk.Label(tempo_frame, textvariable=self.tempo_var, width=5).pack(side="right")
        
        # Key and Scale
        key_frame = tk.Frame(quick_frame)
        key_frame.pack(fill="x", pady=5)
        tk.Label(key_frame, text="Key:", width=15, anchor="w").pack(side="left")
        key_combo = ttk.Combobox(key_frame, textvariable=self.key_var,
                                values=["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
                                state="readonly", width=10)
        key_combo.pack(side="left", padx=5)
        key_combo.bind("<<ComboboxSelected>>", self.update_key)
        
        tk.Label(key_frame, text="Scale:", width=10, anchor="w").pack(side="left", padx=(20,0))
        scale_combo = ttk.Combobox(key_frame, textvariable=self.scale_var,
                                  values=list(self.generator.scales.keys()),
                                  state="readonly", width=15)
        scale_combo.pack(side="left", padx=5)
        scale_combo.bind("<<ComboboxSelected>>", self.update_scale)
        
        # File operations
        file_frame = ttk.LabelFrame(main_frame, text="File Operations", padding=10)
        file_frame.pack(pady=10, padx=20, fill="x")
        
        file_btn_frame = tk.Frame(file_frame)
        file_btn_frame.pack(fill="x")
        
        save_btn = tk.Button(file_btn_frame, text="💾 Save MIDI", command=self.save_midi,
                            font=("Arial", 10), width=15)
        save_btn.pack(side="left", padx=5)
        
        randomize_btn = tk.Button(file_btn_frame, text="🎲 Randomize All", command=self.randomize_all,
                                 font=("Arial", 10), bg="lightyellow", width=15)
        randomize_btn.pack(side="left", padx=5)
        
        load_mp3_btn = tk.Button(file_btn_frame, text="🎵 Load MP3 as Melody", 
                                command=self.load_mp3_as_melody,
                                font=("Arial", 10), width=20)
        load_mp3_btn.pack(side="left", padx=5)
        
        batch_mp3_btn = tk.Button(file_btn_frame, text="📁 Batch MP3 Convert", 
                                 command=self.show_batch_conversion_dialog,
                                 font=("Arial", 10), width=18)
        batch_mp3_btn.pack(side="left", padx=5)
        
        if DIGITAL_KEYBOARD_AVAILABLE:
            keyboard_btn = tk.Button(file_btn_frame, text="🎹 Digital Keyboard", 
                                   command=self.open_keyboard_tab,
                                   font=("Arial", 10), bg="#9b59b6", fg="white", width=15)
            keyboard_btn.pack(side="left", padx=5)
        
        # Visualization frame
        viz_frame = ttk.LabelFrame(main_frame, text="Piano Roll Visualization", padding=10)
        viz_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.fig, self.ax = plt.subplots(figsize=(10, 3), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.fig.patch.set_facecolor('#f0f0f0')  # Match GUI background
        self.ax.set_facecolor('#2E2E2E')
    
    def generate_music(self):
        """Generate new music"""
        try:
            self.status_var.set("Generating music...")
            self.root.update()
            
            self.generator.generate_music()
            self.status_var.set("Music generated successfully!")
            print(f"Generated {len(self.generator.notes_data)} notes")
            
            # Update visualization
            self.update_visualization()
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            print(f"Error generating music: {e}")
    
    def play_music(self):
        """Play the generated music"""
        if not self.generator.current_midi:
            self.status_var.set("Please generate music first!")
            return
        
        try:
            self.status_var.set("Playing music...")
            self.synthesizer.play_midi_file(self.generator.current_midi, self.generator)
            self.status_var.set("Music playing...")
            
        except Exception as e:
            self.status_var.set(f"Playback error: {str(e)}")
            print(f"Error playing music: {e}")
    
    def stop_music(self):
        """Stop music playback"""
        try:
            self.synthesizer.stop_playback()
            self.status_var.set("Playback stopped")
            
        except Exception as e:
            self.status_var.set(f"Stop error: {str(e)}")
            print(f"Error stopping music: {e}")
    
    def save_midi(self):
        """Saves the current MIDI data to a .mid file."""
        if not self.generator.current_midi:
            messagebox.showwarning("No Music", "Please generate music before saving.")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".mid",
            filetypes=[("MIDI Files", "*.mid"), ("All Files", "*.*")]
        )
        if filepath:
            try:
                self.generator.current_midi.save(filepath)
                self.status_var.set(f"MIDI saved to {filepath}")
                messagebox.showinfo("Success", f"Successfully saved MIDI file!")
            except Exception as e:
                messagebox.showerror("Save Error", f"Could not save MIDI file: {e}")

    def randomize_all(self):
        """Randomizes all settings and generates new music."""
        self.generator.randomize_settings()
        
        # Update GUI variables to reflect the new random settings
        self.tempo_var.set(self.generator.settings.tempo)
        self.key_var.set(self.generator.settings.key_signature)
        self.scale_var.set(self.generator.settings.scale_type)
        self.song_length_var.set(self.generator.settings.song_length_bars)
        self.note_low_var.set(self.generator.settings.note_range_low)
        self.note_high_var.set(self.generator.settings.note_range_high)
        self.swing_var.set(self.generator.settings.swing_factor)
        self.rest_prob_var.set(self.generator.settings.rest_probability)
        self.chaos_var.set(self.generator.settings.chaos_factor)
        
        self.status_var.set("Settings have been randomized!")
        self.generate_music()  # Automatically generate music with new settings

    def random_tempo(self):
        """Randomize just the tempo."""
        new_tempo = random.randint(60, 180)
        self.tempo_var.set(new_tempo)
        self.update_tempo(new_tempo)

    def random_key(self):
        """Randomize just the key."""
        keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        new_key = random.choice(keys)
        self.key_var.set(new_key)
        self.update_key()

    def random_scale(self):
        """Randomize just the scale."""
        scales = list(self.generator.scales.keys())
        new_scale = random.choice(scales)
        self.scale_var.set(new_scale)
        self.update_scale()

    # === MP3 TO MIDI INTEGRATION ===

    def load_mp3_as_melody(self):
        """Opens a file dialog to load an MP3 and convert it to a MIDI melody."""
        if not MP3_CONVERSION_AVAILABLE:
            messagebox.showerror("MP3 Conversion Unavailable", 
                               "MP3 to MIDI conversion requires additional libraries.\n"
                               "Please install: pip install librosa soundfile")
            return
        
        # File dialog for MP3 selection
        mp3_path = filedialog.askopenfilename(
            title="Select MP3 file to convert",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.flac *.m4a"),
                ("MP3 Files", "*.mp3"),
                ("WAV Files", "*.wav"),
                ("All Files", "*.*")
            ]
        )
        
        if not mp3_path:
            return
        
        # Create conversion dialog
        self.show_mp3_conversion_dialog(mp3_path)

    def show_mp3_conversion_dialog(self, mp3_path):
        """Shows a dialog for MP3 to MIDI conversion options"""
        if not MP3_CONVERSION_AVAILABLE:
            messagebox.showerror("MP3 Conversion Unavailable", 
                               "MP3 to MIDI conversion requires additional libraries.")
            return
        
        # Create a new dialog window
        conversion_dialog = tk.Toplevel(self.root)
        conversion_dialog.title("MP3 to MIDI Conversion")
        conversion_dialog.geometry("580x650")  # Slightly smaller to ensure buttons are visible
        conversion_dialog.resizable(True, True)  # Allow resizing
        conversion_dialog.transient(self.root)
        conversion_dialog.grab_set()
        
        # Make dialog appear in center of screen
        conversion_dialog.update_idletasks()
        x = (conversion_dialog.winfo_screenwidth() // 2) - (580 // 2)
        y = (conversion_dialog.winfo_screenheight() // 2) - (650 // 2)
        conversion_dialog.geometry(f"580x650+{x}+{y}")
        
        # Set minimum size to ensure buttons are always visible
        conversion_dialog.minsize(580, 600)
        
        # Dialog content
        tk.Label(conversion_dialog, text="MP3 to MIDI Conversion", 
                font=("Arial", 16, "bold")).pack(pady=10)
        
        tk.Label(conversion_dialog, text=f"File: {os.path.basename(mp3_path)}", 
                font=("Arial", 10)).pack(pady=5)
        
        # Algorithm selection
        algorithm_frame = ttk.LabelFrame(conversion_dialog, text="Conversion Algorithm")
        algorithm_frame.pack(fill="x", padx=20, pady=10)
        
        algorithm_var = tk.StringVar(value="melodia")
        
        ttk.Radiobutton(algorithm_frame, text="Melodia (Best for melodies)", 
                       variable=algorithm_var, value="melodia").pack(anchor="w", padx=10, pady=5)
        
        ttk.Radiobutton(algorithm_frame, text="Multi-pitch (Better for chords)", 
                       variable=algorithm_var, value="multi-pitch").pack(anchor="w", padx=10, pady=5)
        
        ttk.Radiobutton(algorithm_frame, text="Neural Network (Experimental)", 
                       variable=algorithm_var, value="neural").pack(anchor="w", padx=10, pady=5)
        
        # Advanced options
        options_frame = ttk.LabelFrame(conversion_dialog, text="Options")
        options_frame.pack(fill="x", padx=20, pady=10)
        
        # Sensitivity
        sensitivity_frame = tk.Frame(options_frame)
        sensitivity_frame.pack(fill="x", pady=5)
        
        tk.Label(sensitivity_frame, text="Sensitivity:").pack(side="left", padx=10)
        sensitivity_var = tk.DoubleVar(value=0.5)
        sensitivity_scale = tk.Scale(sensitivity_frame, from_=0.1, to=1.0, resolution=0.1,
                                   orient="horizontal", variable=sensitivity_var)
        sensitivity_scale.pack(side="right", fill="x", expand=True, padx=10)
        
        # Min note duration
        duration_frame = tk.Frame(options_frame)
        duration_frame.pack(fill="x", pady=5)
        
        tk.Label(duration_frame, text="Min Note Duration (ms):").pack(side="left", padx=10)
        duration_var = tk.IntVar(value=100)
        duration_scale = tk.Scale(duration_frame, from_=50, to=500, resolution=10,
                                orient="horizontal", variable=duration_var)
        duration_scale.pack(side="right", fill="x", expand=True, padx=10)
        
        # Progress tracking
        progress_frame = ttk.LabelFrame(conversion_dialog, text="Conversion Progress")
        progress_frame.pack(fill="x", padx=20, pady=10)
        
        progress_var = tk.DoubleVar(value=0.0)
        progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
        progress_bar.pack(fill="x", padx=10, pady=10)
        
        status_var = tk.StringVar(value="Ready to convert...")
        status_label = tk.Label(progress_frame, textvariable=status_var, font=("Arial", 9))
        status_label.pack(pady=5)
        
        # Analysis output - Compact to ensure buttons are visible
        analysis_frame = ttk.LabelFrame(conversion_dialog, text="Analysis Results")
        analysis_frame.pack(fill="both", expand=True, padx=20, pady=(10, 5))
        
        # Create text with scrollbar
        text_frame = tk.Frame(analysis_frame)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        analysis_text = tk.Text(text_frame, height=3, wrap=tk.WORD, font=("Consolas", 9))
        scrollbar_analysis = ttk.Scrollbar(text_frame, orient="vertical", command=analysis_text.yview)
        analysis_text.configure(yscrollcommand=scrollbar_analysis.set)
        
        analysis_text.pack(side="left", fill="both", expand=True)
        scrollbar_analysis.pack(side="right", fill="y")
        
        analysis_text.insert(tk.END, "📋 Click 'Preview Analysis' to analyze the audio file...\n")
        analysis_text.insert(tk.END, "🎵 Then click 'Convert to MIDI' to perform the conversion.\n")
        analysis_text.config(state="disabled")  # Make read-only initially
        
        # Define the conversion functions with access to dialog variables
        def preview_conversion():
            """Preview the MP3 conversion"""
            try:
                status_var.set("Analyzing audio...")
                progress_var.set(10)
                conversion_dialog.update()
                
                # Get selected algorithm
                algo = algorithm_var.get()
                converter_algo = "cqt"  # Default
                if algo == "melodia":
                    converter_algo = "onset"
                elif algo == "multi-pitch":
                    converter_algo = "chroma"
                elif algo == "neural":
                    converter_algo = "auto"
                
                # Create converter with progress callback
                def update_progress_callback(progress, message):
                    progress_var.set(progress * 100)
                    status_var.set(message)
                    conversion_dialog.update()
                
                # Create converter
                converter = MP3ToMIDIConverter(update_progress_callback)
                converter.sensitivity = sensitivity_var.get()
                
                # Preview conversion (first 10 seconds)
                result = converter.preview_conversion(mp3_path, converter_algo, 10.0)
                
                # Display results
                analysis_text.config(state="normal")  # Enable editing
                analysis_text.delete(1.0, tk.END)
                analysis_text.insert(tk.END, f"🔍 Analysis of {os.path.basename(mp3_path)}...\n\n")
                
                if result['success']:
                    analysis = result.get('analysis', {})
                    notes = result.get('notes', [])
                    
                    analysis_text.insert(tk.END, f"Algorithm: {algo}\n")
                    analysis_text.insert(tk.END, f"Notes detected: {len(notes)}\n")
                    analysis_text.insert(tk.END, f"Estimated full file notes: {result.get('estimated_full_notes', 'Unknown')}\n\n")
                    
                    if analysis:
                        analysis_text.insert(tk.END, f"Harmonic ratio: {analysis.get('harmonic_ratio', 0):.2f}\n")
                        analysis_text.insert(tk.END, f"Tempo: {analysis.get('tempo', 0):.1f} BPM\n")
                        analysis_text.insert(tk.END, f"Note density: {analysis.get('onset_density', 0):.2f} notes/sec\n")
                    
                    status_var.set("Analysis complete! Ready for conversion.")
                    progress_var.set(100)
                    analysis_text.config(state="disabled")  # Make read-only
                else:
                    analysis_text.insert(tk.END, f"❌ Error: {result.get('error', 'Unknown error')}\n")
                    status_var.set("Analysis failed.")
                    progress_var.set(0)
                    analysis_text.config(state="disabled")  # Make read-only
                    
            except Exception as e:
                status_var.set(f"Error: {str(e)}")
                analysis_text.config(state="normal")
                analysis_text.insert(tk.END, f"\n❌ Error during analysis: {str(e)}")
                analysis_text.config(state="disabled")
        
        def convert_to_midi():
            """Convert the MP3 to MIDI and load it"""
            try:
                status_var.set("Converting to MIDI...")
                progress_var.set(10)
                conversion_dialog.update()
                
                # Get the selected algorithm
                algo = algorithm_var.get()
                converter_algo = "cqt"  # Default
                if algo == "melodia":
                    converter_algo = "onset"
                elif algo == "multi-pitch":
                    converter_algo = "chroma"
                elif algo == "neural":
                    converter_algo = "auto"
                
                # Get sensitivity and duration values
                sensitivity = sensitivity_var.get()
                min_duration = duration_var.get() / 1000.0  # Convert ms to seconds
                
                # Create converter with progress callback
                def update_progress_callback(progress, message):
                    progress_var.set(progress * 100)
                    status_var.set(message)
                    conversion_dialog.update()
                
                converter = MP3ToMIDIConverter(update_progress_callback)
                converter.sensitivity = sensitivity
                converter.min_duration = min_duration
                
                # Create output path
                output_dir = os.path.dirname(mp3_path)
                output_filename = os.path.splitext(os.path.basename(mp3_path))[0] + "_converted.mid"
                output_path = os.path.join(output_dir, output_filename)
                
                # Convert the file
                if converter_algo == "auto":
                    result = converter.convert_with_auto_algorithm(mp3_path, output_path)
                    success = result.get('success', False)
                else:
                    success = converter.convert_mp3_to_midi(mp3_path, output_path, converter_algo)
                
                if success:
                    # Load the converted notes into our generator
                    self.generator.load_midi_file(output_path)
                    status_var.set("Conversion complete!")
                    analysis_text.config(state="normal")
                    analysis_text.insert(tk.END, f"\n✅ Conversion successful!\n")
                    analysis_text.insert(tk.END, f"📁 MIDI saved to: {output_path}\n")
                    analysis_text.insert(tk.END, f"🎵 Generated {len(self.generator.notes_data)} notes\n")
                    analysis_text.config(state="disabled")
                    
                    # Update visualization
                    self.update_visualization()
                    
                    # Automatically close dialog after a short delay
                    conversion_dialog.after(3000, conversion_dialog.destroy)
                else:
                    status_var.set("Conversion failed")
                    analysis_text.config(state="normal")
                    analysis_text.insert(tk.END, "\n❌ Conversion failed. Please try a different algorithm.\n")
                    analysis_text.config(state="disabled")
                    
            except Exception as e:
                status_var.set(f"Error: {str(e)}")
                analysis_text.config(state="normal")
                analysis_text.insert(tk.END, f"\n❌ Error during conversion: {str(e)}")
                analysis_text.config(state="disabled")
        
        # ACTION BUTTONS - Fixed at bottom to ensure they're always visible
        button_frame = tk.Frame(conversion_dialog, bg="#f0f0f0", relief="raised", bd=2, height=80)
        button_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        button_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        # Instruction label
        instruction_label = tk.Label(button_frame, text="🎯 Choose an action:", 
                                   font=("Arial", 12, "bold"), bg="#f0f0f0", fg="#2c3e50")
        instruction_label.pack(pady=(10, 5))
        
        # Buttons container
        buttons_container = tk.Frame(button_frame, bg="#f0f0f0")
        buttons_container.pack()
        
        # Preview button
        preview_btn = tk.Button(buttons_container, text="🔍 Preview Analysis", 
                              command=preview_conversion,
                              bg="#3498db", fg="white", font=("Arial", 11, "bold"),
                              relief="raised", bd=3, padx=15, pady=5,
                              cursor="hand2", width=18)
        preview_btn.pack(side="left", padx=8)
        
        # Convert button  
        convert_btn = tk.Button(buttons_container, text="🎵 Convert to MIDI", 
                              command=convert_to_midi,
                              bg="#27ae60", fg="white", font=("Arial", 11, "bold"),
                              relief="raised", bd=3, padx=15, pady=5,
                              cursor="hand2", width=18)
        convert_btn.pack(side="left", padx=8)
        
        # Close button
        close_btn = tk.Button(buttons_container, text="❌ Close", 
                            command=conversion_dialog.destroy,
                            font=("Arial", 10), bg="#e74c3c", fg="white",
                            relief="raised", bd=2, cursor="hand2", width=10)
        close_btn.pack(side="left", padx=8)

    def show_batch_conversion_dialog(self):
        """Show batch MP3 to MIDI conversion dialog"""
        if not MP3_CONVERSION_AVAILABLE:
            messagebox.showerror("MP3 Conversion Unavailable", 
                               "MP3 to MIDI conversion requires additional libraries.\n"
                               "Please install: pip install librosa soundfile")
            return
        
        messagebox.showinfo("Batch Conversion", "Batch conversion feature coming soon!")

    def create_creative_tab(self):
        """Create the creative generation tab"""
        creative_frame = ttk.Frame(self.notebook)
        self.notebook.add(creative_frame, text="🎨 Creative")
        
        # Title
        title_label = tk.Label(creative_frame, text="🎨 Creative Music Generation", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # MP3 to MIDI section
        mp3_frame = ttk.LabelFrame(creative_frame, text="Audio to MIDI Conversion", padding=10)
        mp3_frame.pack(pady=10, padx=20, fill="x")
        
        tk.Label(mp3_frame, text="Convert audio files to MIDI and generate inspired music",
                font=("Arial", 10), fg="gray").pack(pady=5)
        
        mp3_btn_frame = tk.Frame(mp3_frame)
        mp3_btn_frame.pack(fill="x", pady=5)
        
        tk.Button(mp3_btn_frame, text="🎵 Load MP3 File", 
                 command=self.load_mp3_as_melody,
                 font=("Arial", 11), bg="lightblue").pack(side="left", padx=5)
        
        tk.Button(mp3_btn_frame, text="📁 Batch Conversion", 
                 command=self.show_batch_conversion_dialog,
                 font=("Arial", 11), bg="lightcyan").pack(side="left", padx=5)
        
        # AI Generation section
        ai_frame = ttk.LabelFrame(creative_frame, text="AI-Powered Generation", padding=10)
        ai_frame.pack(pady=10, padx=20, fill="x")
        
        tk.Label(ai_frame, text="Use artificial intelligence to create unique musical compositions",
                font=("Arial", 10), fg="gray").pack(pady=5)
        
        ai_btn_frame = tk.Frame(ai_frame)
        ai_btn_frame.pack(fill="x", pady=5)
        
        tk.Button(ai_btn_frame, text="🧠 Generate AI Music", 
                 command=self.generate_ai_music,
                 font=("Arial", 11), bg="mediumpurple", fg="white").pack(side="left", padx=5)
        
        tk.Button(ai_btn_frame, text="🎭 Style Transfer", 
                 command=self.style_transfer,
                 font=("Arial", 11), bg="plum").pack(side="left", padx=5)

    # === HANDLER FUNCTIONS FOR GUI CONTROLS ===

    def create_settings_tab(self):
        """Create the settings configuration tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Title
        title_label = tk.Label(settings_frame, text="⚙️ Application Settings", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # Create scrollable content
        canvas = tk.Canvas(settings_frame)
        scrollbar = ttk.Scrollbar(settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
    
        # Audio Settings
        audio_frame = ttk.LabelFrame(scrollable_frame, text="Audio Settings", padding=10)
        audio_frame.pack(fill="x", padx=20, pady=10)
        
        # Volume control
        volume_frame = tk.Frame(audio_frame)
        volume_frame.pack(fill="x", pady=5)
        tk.Label(volume_frame, text="Master Volume:", font=("Arial", 10, "bold")).pack(side="left")
        volume_scale = tk.Scale(volume_frame, from_=0.0, to=1.0, resolution=0.1, 
                               orient="horizontal", variable=self.volume_var,
                               command=self.update_volume)
        volume_scale.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Filter cutoff
        filter_frame = tk.Frame(audio_frame)
        filter_frame.pack(fill="x", pady=5)
        tk.Label(filter_frame, text="Filter Cutoff (Hz):", font=("Arial", 10, "bold")).pack(side="left")
        filter_scale = tk.Scale(filter_frame, from_=100, to=20000, resolution=100, 
                               orient="horizontal", variable=self.filter_cutoff_var,
                               command=self.update_filter)
        filter_scale.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Stereo width
        stereo_frame = tk.Frame(audio_frame)
        stereo_frame.pack(fill="x", pady=5)
        tk.Label(stereo_frame, text="Stereo Width:", font=("Arial", 10, "bold")).pack(side="left")
        stereo_scale = tk.Scale(stereo_frame, from_=0.0, to=1.0, resolution=0.1, 
                               orient="horizontal", variable=self.stereo_width_var,
                               command=self.update_stereo_width)
        stereo_scale.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # MIDI Settings
        midi_frame = ttk.LabelFrame(scrollable_frame, text="MIDI Settings", padding=10)
        midi_frame.pack(fill="x", padx=20, pady=10)
        
        # Default velocity
        velocity_frame = tk.Frame(midi_frame)
        velocity_frame.pack(fill="x", pady=5)
        tk.Label(velocity_frame, text="Default Velocity:", font=("Arial", 10, "bold")).pack(side="left")
        velocity_scale = tk.Scale(velocity_frame, from_=1, to=127, resolution=1, 
                                 orient="horizontal", variable=self.velocity_var)
        velocity_scale.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Default channel
        channel_frame = tk.Frame(midi_frame)
        channel_frame.pack(fill="x", pady=5)
        tk.Label(channel_frame, text="MIDI Channel:", font=("Arial", 10, "bold")).pack(side="left")
        channel_scale = tk.Scale(channel_frame, from_=1, to=16, resolution=1, 
                                orient="horizontal", variable=self.channel_var)
        channel_scale.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Generation Settings
        gen_frame = ttk.LabelFrame(scrollable_frame, text="Generation Settings", padding=10)
        gen_frame.pack(fill="x", padx=20, pady=10)
        
        # Number of notes
        notes_frame = tk.Frame(gen_frame)
        notes_frame.pack(fill="x", pady=5)
        tk.Label(notes_frame, text="Number of Notes:", font=("Arial", 10, "bold")).pack(side="left")
        notes_scale = tk.Scale(notes_frame, from_=10, to=200, resolution=5, 
                              orient="horizontal", variable=self.num_notes_var)
        notes_scale.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Tempo
        tempo_frame = tk.Frame(gen_frame)
        tempo_frame.pack(fill="x", pady=5)
        tk.Label(tempo_frame, text="Tempo (BPM):", font=("Arial", 10, "bold")).pack(side="left")
        tempo_scale = tk.Scale(tempo_frame, from_=60, to=200, resolution=5, 
                              orient="horizontal", variable=self.tempo_var,
                              command=self.update_tempo)
        tempo_scale.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Application Settings
        app_frame = ttk.LabelFrame(scrollable_frame, text="Application Settings", padding=10)
        app_frame.pack(fill="x", padx=20, pady=10)
        
        # Auto-save checkbox
        auto_save_frame = tk.Frame(app_frame)
        auto_save_frame.pack(fill="x", pady=5)
        self.auto_save_var = tk.BooleanVar(value=True)
        tk.Checkbutton(auto_save_frame, text="Auto-save generated MIDI files", 
                      variable=self.auto_save_var, font=("Arial", 10)).pack(side="left")
        
        # Show tooltips checkbox
        tooltips_frame = tk.Frame(app_frame)
        tooltips_frame.pack(fill="x", pady=5)
        self.show_tooltips_var = tk.BooleanVar(value=True)
        tk.Checkbutton(tooltips_frame, text="Show helpful tooltips", 
                      variable=self.show_tooltips_var, font=("Arial", 10)).pack(side="left")
        
        # Theme selection
        theme_frame = tk.Frame(app_frame)
        theme_frame.pack(fill="x", pady=5)
        tk.Label(theme_frame, text="Theme:", font=("Arial", 10, "bold")).pack(side="left")
        self.theme_var = tk.StringVar(value="Default")
        theme_menu = ttk.Combobox(theme_frame, textvariable=self.theme_var, 
                                 values=["Default", "Dark", "Light", "Colorful"], 
                                 state="readonly")
        theme_menu.pack(side="right", padx=(10, 0))
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
    
    def create_advanced_tab(self):
        """Create the advanced features tab"""
        advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(advanced_frame, text="🚀 Advanced")
        
        # Title
        title_label = tk.Label(advanced_frame, text="🚀 Advanced Features", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # Create scrollable content
        canvas = tk.Canvas(advanced_frame)
        scrollbar = ttk.Scrollbar(advanced_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        def on_mousewheel_advanced(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel_advanced)
    
        # AI-Powered Generation
        ai_frame = ttk.LabelFrame(scrollable_frame, text="AI-Powered Generation", padding=10)
        ai_frame.pack(fill="x", padx=20, pady=10)
        
        # Neural network style generation
        tk.Label(ai_frame, text="Neural Network Style:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.ai_style_var = tk.StringVar(value="Classical")
        ai_style_frame = tk.Frame(ai_frame)
        ai_style_frame.pack(fill="x", pady=5)
        
        styles = ["Classical", "Jazz", "Blues", "Rock", "Ambient", "Electronic"]
        for i, style in enumerate(styles):
            tk.Radiobutton(ai_style_frame, text=style, variable=self.ai_style_var, 
                          value=style, font=("Arial", 9)).pack(side="left", padx=5)
        
        # AI generation controls
        ai_controls_frame = tk.Frame(ai_frame)
        ai_controls_frame.pack(fill="x", pady=10)
        
        tk.Button(ai_controls_frame, text="🧠 Generate AI Music", 
                 command=self.generate_ai_music, font=("Arial", 11, "bold"),
                 bg="#9C27B0", fg="white").pack(side="left", padx=5)
        
        tk.Button(ai_controls_frame, text="🎭 Style Transfer", 
                 command=self.style_transfer, font=("Arial", 11),
                 bg="#673AB7", fg="white").pack(side="left", padx=5)
        
        # Advanced Synthesis
        synth_frame = ttk.LabelFrame(scrollable_frame, text="Advanced Synthesis", padding=10)
        synth_frame.pack(fill="x", padx=20, pady=10)
        
        # Wavetable synthesis
        wave_frame = tk.Frame(synth_frame)
        wave_frame.pack(fill="x", pady=5)
        tk.Label(wave_frame, text="Wavetable:", font=("Arial", 10, "bold")).pack(side="left")
        
        self.wavetable_var = tk.StringVar(value="Sawtooth")
        wavetable_menu = ttk.Combobox(wave_frame, textvariable=self.wavetable_var,
                                     values=["Sine", "Sawtooth", "Square", "Triangle", "Noise"], 
                                     state="readonly")
        wavetable_menu.pack(side="right", padx=(10, 0))
        
        # FM synthesis parameters
        fm_frame = tk.Frame(synth_frame)
        fm_frame.pack(fill="x", pady=5)
        tk.Label(fm_frame, text="FM Modulation Depth:", font=("Arial", 10, "bold")).pack(side="left")
        
        self.fm_depth_var = tk.DoubleVar(value=0.5)
        fm_scale = tk.Scale(fm_frame, from_=0.0, to=2.0, resolution=0.1, 
                           orient="horizontal", variable=self.fm_depth_var)
        fm_scale.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Advanced Effects
        effects_frame = ttk.LabelFrame(scrollable_frame, text="Advanced Effects", padding=10)
        effects_frame.pack(fill="x", padx=20, pady=10)
        
        # Reverb controls
        reverb_frame = tk.Frame(effects_frame)
        reverb_frame.pack(fill="x", pady=5)
        tk.Label(reverb_frame, text="Reverb Size:", font=("Arial", 10, "bold")).pack(side="left")
        
        self.reverb_size_var = tk.DoubleVar(value=0.3)
        reverb_scale = tk.Scale(reverb_frame, from_=0.0, to=1.0, resolution=0.1, 
                               orient="horizontal", variable=self.reverb_size_var)
        reverb_scale.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Delay controls
        delay_frame = tk.Frame(effects_frame)
        delay_frame.pack(fill="x", pady=5)
        tk.Label(delay_frame, text="Delay Time (ms):", font=("Arial", 10, "bold")).pack(side="left")
        
        self.delay_time_var = tk.IntVar(value=250)
        delay_scale = tk.Scale(delay_frame, from_=50, to=1000, resolution=50, 
                              orient="horizontal", variable=self.delay_time_var)
        delay_scale.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Algorithmic Composition
        algo_frame = ttk.LabelFrame(scrollable_frame, text="Algorithmic Composition", padding=10)
        algo_frame.pack(fill="x", padx=20, pady=10)
        
        # Markov chain generation
        tk.Label(algo_frame, text="Markov Chain Order:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.markov_order_var = tk.IntVar(value=2)
        markov_frame = tk.Frame(algo_frame)
        markov_frame.pack(fill="x", pady=5)
        
        for order in range(1, 5):
            tk.Radiobutton(markov_frame, text=f"Order {order}", variable=self.markov_order_var, 
                          value=order, font=("Arial", 9)).pack(side="left", padx=10)
        
        # Algorithm controls
        algo_controls_frame = tk.Frame(algo_frame)
        algo_controls_frame.pack(fill="x", pady=10)
        
        tk.Button(algo_controls_frame, text="🔀 Markov Generation", 
                 command=self.generate_markov, font=("Arial", 11),
                 bg="#FF5722", fg="white").pack(side="left", padx=5)
        
        tk.Button(algo_controls_frame, text="🌐 Cellular Automata", 
                 command=self.generate_cellular, font=("Arial", 11),
                 bg="#795548", fg="white").pack(side="left", padx=5)
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        def on_mousewheel_audio(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel_audio)
    
    def test_note(self, note):
        """Test a single note with current settings"""
        try:
            # Create a simple test note
            test_midi = mido.MidiFile()
            track = mido.MidiTrack()
            test_midi.tracks.append(track)
            
            # Add note on and off messages
            track.append(mido.Message('note_on', note=note, velocity=80, time=0))
            track.append(mido.Message('note_off', note=note, velocity=0, time=480))
            
            self.synthesizer.play_midi_data(test_midi)
            self.status_var.set(f"Testing note {note}")
            
        except Exception as e:
            self.status_var.set(f"Test note error: {str(e)}")
    
    def test_chord(self):
        """Test a chord with current settings"""
        try:
            # Create a simple test chord (C major)
            test_midi = mido.MidiFile()
            track = mido.MidiTrack()
            test_midi.tracks.append(track)
            
            # Add chord notes
            chord_notes = [60, 64, 67]  # C, E, G
            for note in chord_notes:
                track.append(mido.Message('note_on', note=note, velocity=70, time=0))
            
            for note in chord_notes:
                track.append(mido.Message('note_off', note=note, velocity=0, time=480))
            
            self.synthesizer.play_midi_data(test_midi)
            self.status_var.set("Testing C major chord")
            
        except Exception as e:
            self.status_var.set(f"Test chord error: {str(e)}")
    
    def apply_audio_settings(self):
        """Apply current audio settings to the synthesizer"""
        try:
            # Apply ADSR settings
            if hasattr(self.synthesizer, 'set_adsr'):
                self.synthesizer.set_adsr(
                    attack=self.attack_var.get(),
                    decay=self.decay_var.get(),
                    sustain=self.sustain_var.get(),
                    release=self.release_var.get()
                )
            
            # Apply filter settings
            if hasattr(self.synthesizer, 'set_filter'):
                self.synthesizer.set_filter(
                    filter_type=self.filter_type_var.get(),
                    cutoff=self.filter_cutoff_var.get()
                )
            
            # Apply effects
            if hasattr(self.synthesizer, 'set_effects'):
                self.synthesizer.set_effects(
                    reverb=self.reverb_enabled_var.get(),
                    reverb_amount=self.reverb_size_var.get(),
                    delay=self.delay_enabled_var.get(),
                    delay_time=self.delay_time_var.get(),
                    distortion=self.distortion_enabled_var.get(),
                    distortion_amount=self.distortion_amount_var.get()
                )
            
            self.status_var.set("Audio settings applied successfully!")
            
        except Exception as e:
            self.status_var.set(f"Error applying audio settings: {str(e)}")

    def update_volume(self, value):
        """Update master volume"""
        try:
            volume = float(value)
            if hasattr(self.synthesizer, 'set_master_volume'):
                self.synthesizer.set_master_volume(volume)
            self.status_var.set(f"Volume set to {volume:.1f}")
        except Exception as e:
            print(f"Error updating volume: {e}")
    
    def update_filter(self, value):
        """Update filter cutoff"""
        try:
            cutoff = float(value)
            if hasattr(self.synthesizer, 'set_filter_cutoff'):
                self.synthesizer.set_filter_cutoff(cutoff)
            self.status_var.set(f"Filter cutoff set to {cutoff:.0f} Hz")
        except Exception as e:
            print(f"Error updating filter: {e}")
    
    def update_stereo_width(self, value):
        """Update stereo width"""
        try:
            width = float(value)
            if hasattr(self.synthesizer, 'set_stereo_width'):
                self.synthesizer.set_stereo_width(width)
            self.status_var.set(f"Stereo width set to {width:.1f}")
        except Exception as e:
            print(f"Error updating stereo width: {e}")

    def update_tempo(self, value):
        """Called when the tempo slider is changed."""
        self.generator.settings.tempo = self.tempo_var.get()
        self.status_var.set(f"Tempo set to {self.generator.settings.tempo} BPM")

    def update_key(self, event=None):
        """Called when the key combobox is changed."""
        self.generator.settings.key_signature = self.key_var.get()
        self.status_var.set(f"Key set to {self.generator.settings.key_signature}")

    def update_scale(self, event=None):
        """Called when the scale combobox is changed."""
        self.generator.settings.scale_type = self.scale_var.get()
        self.status_var.set(f"Scale set to {self.generator.settings.scale_type}")

    def update_song_length(self, value):
        self.generator.settings.song_length_bars = self.song_length_var.get()

    def update_note_range(self, value):
        self.generator.settings.note_range_low = self.note_low_var.get()
        self.generator.settings.note_range_high = self.note_high_var.get()
        # Add logic to ensure low is not higher than high
        if self.note_low_var.get() >= self.note_high_var.get():
            self.note_high_var.set(self.note_low_var.get() + 1)
            self.generator.settings.note_range_high = self.note_high_var.get()

    def update_swing(self, value):
        self.generator.settings.swing_factor = self.swing_var.get()

    def update_rest_prob(self, value):
        self.generator.settings.rest_probability = self.rest_prob_var.get()

    def update_chaos(self, value):
        self.generator.settings.chaos_factor = self.chaos_var.get()

    def create_keyboard_tab(self):
        """Create the digital keyboard tab"""
        keyboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(keyboard_frame, text="🎹 Digital Keyboard")
        
        # Initialize the digital keyboard
        try:
            self.digital_keyboard = DigitalKeyboard(keyboard_frame, self.synthesizer)
            print("✅ Digital Keyboard tab created successfully")
        except Exception as e:
            # Fallback UI if keyboard creation fails
            tk.Label(keyboard_frame, text="🎹 Digital Keyboard", 
                    font=("Arial", 16, "bold")).pack(pady=20)
            tk.Label(keyboard_frame, text="Digital Keyboard failed to initialize:", 
                    font=("Arial", 12)).pack(pady=10)
            tk.Label(keyboard_frame, text=str(e), 
                    font=("Arial", 10), wraplength=400, justify="center").pack(pady=5)
            
            # Add a button to try launching in separate window
            tk.Button(keyboard_frame, text="🎹 Open in Separate Window", 
                     command=self.open_keyboard_window,
                     font=("Arial", 12), bg="#9b59b6", fg="white").pack(pady=20)
            
            print(f"❌ Digital Keyboard tab creation failed: {e}")
    
    def open_keyboard_tab(self):
        """Switch to the keyboard tab"""
        if DIGITAL_KEYBOARD_AVAILABLE and hasattr(self, 'digital_keyboard'):
            # Switch to keyboard tab
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") == "🎹 Digital Keyboard":
                    self.notebook.select(i)
                    break
            self.status_var.set("Switched to Digital Keyboard")
        else:
            self.open_keyboard_window()
    
    def open_keyboard_window(self):
        """Open digital keyboard in a separate window"""
        try:
            from digital_keyboard import DigitalKeyboardWindow
            keyboard_window = DigitalKeyboardWindow(self.synthesizer)
            self.status_var.set("Digital Keyboard opened in separate window")
        except Exception as e:
            messagebox.showerror("Keyboard Error", f"Failed to open digital keyboard: {e}")
            self.status_var.set(f"Keyboard error: {e}")

    def create_audio_tab(self):
        """Create the audio synthesis tab (placeholder)"""
        audio_frame = ttk.Frame(self.notebook)
        self.notebook.add(audio_frame, text="🔊 Audio")
        
        # Title
        title_label = tk.Label(audio_frame, text="🔊 Audio Synthesis", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # Audio controls frame
        controls_frame = ttk.LabelFrame(audio_frame, text="Audio Controls", padding=10)
        controls_frame.pack(pady=10, padx=20, fill="x")
        
        # Master volume
        volume_frame = tk.Frame(controls_frame)
        volume_frame.pack(fill="x", pady=5)
        tk.Label(volume_frame, text="Master Volume:", width=15, anchor="w").pack(side="left")
        volume_scale = tk.Scale(volume_frame, from_=0.0, to=1.0, resolution=0.1,
                              orient="horizontal", variable=self.volume_var,
                              command=self.update_volume)
        volume_scale.pack(side="left", fill="x", expand=True)
        
        # Test buttons
        test_frame = ttk.LabelFrame(audio_frame, text="Audio Tests", padding=10)
        test_frame.pack(pady=10, padx=20, fill="x")
        
        test_btn_frame = tk.Frame(test_frame)
        test_btn_frame.pack(fill="x")
        
        tk.Button(test_btn_frame, text="Test Note C4", 
                 command=lambda: self.test_note(60),
                 font=("Arial", 10), width=12).pack(side="left", padx=5)
        
        tk.Button(test_btn_frame, text="Test Chord", 
                 command=self.test_chord,
                 font=("Arial", 10), width=12).pack(side="left", padx=5)
        
        print("✅ Audio tab created")
    
    def test_note(self, note):
        """Test a single note"""
        try:
            self.synthesizer.note_on(0, note, 80)
            self.root.after(500, lambda: self.synthesizer.note_off(0, note))
            self.status_var.set(f"Testing note {note}")
        except Exception as e:
            self.status_var.set(f"Test note error: {str(e)}")
    
    def test_chord(self):
        """Test a chord"""
        try:
            chord_notes = [60, 64, 67]  # C major
            for note in chord_notes:
                self.synthesizer.note_on(0, note, 70)
            self.root.after(1000, lambda: [self.synthesizer.note_off(0, note) for note in chord_notes])
            self.status_var.set("Testing C major chord")
        except Exception as e:
            self.status_var.set(f"Test chord error: {str(e)}")
    
    # === AI AND ADVANCED GENERATION METHODS ===

    def generate_ai_music(self):
        """Generate music using AI-style algorithms"""
        try:
            style = self.ai_style_var.get()
            self.status_var.set(f"Generating {style} style music using AI algorithms...")
            
            # Use enhanced generation with style-specific parameters
            if style == "Jazz":
                self.generator.settings.swing_factor = 0.3
                self.generator.settings.syncopation_prob = 0.4
                self.generator.settings.chord_complexity = 4
            elif style == "Classical":
                self.generator.settings.voice_leading = True
                self.generator.settings.parallel_motion_avoid = True
                self.generator.settings.sequence_probability = 0.3
            elif style == "Blues":
                self.generator.settings.scale_type = "blues"
                self.generator.settings.repetition_factor = 0.5
            elif style == "Electronic":
                self.generator.settings.syncopation_prob = 0.6
                self.generator.settings.rest_probability = 0.1
            elif style == "Ambient":
                self.generator.settings.note_length_min = 1.0
                self.generator.settings.note_length_max = 4.0
                self.generator.settings.rest_probability = 0.3
            
            # Generate the music
            self.generator.generate_music()
            self.update_visualization()
            self.status_var.set(f"✅ {style} style music generated!")
            
        except Exception as e:
            self.status_var.set(f"AI generation error: {str(e)}")
            print(f"Error in AI music generation: {e}")

    def style_transfer(self):
        """Apply style transfer to existing music"""
        try:
            if not self.generator.current_midi:
                self.status_var.set("Please generate music first for style transfer!")
                return
            
            style = self.ai_style_var.get()
            self.status_var.set(f"Applying {style} style transfer...")
            
            # Create a variation with style-specific modifications
            original_notes = self.generator.notes_data.copy()
            
            # Apply style-specific transformations
            for note in original_notes:
                if style == "Jazz":
                    # Add swing timing
                    if note['start'] % 1 == 0.5:  # On off-beats
                        note['start'] += 0.1  # Swing delay
                elif style == "Classical":
                    # Add ornamentations occasionally
                    if random.random() < 0.1:
                        note['velocity'] = min(127, note['velocity'] + 10)
                elif style == "Electronic":
                    # Quantize timing
                    note['start'] = round(note['start'] * 4) / 4
            
            self.generator.notes_data = original_notes
            self.generator.current_midi = self.generator.create_midi_file(original_notes)
            self.update_visualization()
            self.status_var.set(f"✅ {style} style transfer applied!")
            
        except Exception as e:
            self.status_var.set(f"Style transfer error: {str(e)}")
            print(f"Error in style transfer: {e}")

    def generate_markov(self):
        """Generate music using Markov chain algorithms"""
        try:
            order = self.markov_order_var.get()
            self.status_var.set(f"Generating music with Markov chain (order {order})...")
            
            # Use existing notes as training data if available
            training_notes = self.generator.notes_data if self.generator.notes_data else []
            
            if not training_notes:
                # Generate some seed data first
                self.generator.generate_music()
                training_notes = self.generator.notes_data
            
            # Simple Markov chain implementation
            note_transitions = {}
            for i in range(len(training_notes) - order):
                current_state = tuple(n['note'] for n in training_notes[i:i+order])
                next_note = training_notes[i+order]['note']
                
                if current_state not in note_transitions:
                    note_transitions[current_state] = []
                note_transitions[current_state].append(next_note)
            
            # Generate new sequence
            new_notes = []
            if note_transitions:
                # Start with a random state
                current_state = random.choice(list(note_transitions.keys()))
                
                for i in range(self.generator.settings.song_length_bars * 4):
                    if current_state in note_transitions:
                        next_note = random.choice(note_transitions[current_state])
                        new_notes.append({
                            'note': next_note,
                            'start': i * 0.5,
                            'duration': 0.5,
                            'velocity': random.randint(70, 100),
                            'channel': 0
                        })
                        
                        # Update state
                        current_state = current_state[1:] + (next_note,)
                    else:
                        break
            
            if new_notes:
                self.generator.notes_data = new_notes
                self.generator.current_midi = self.generator.create_midi_file(new_notes)
                self.update_visualization()
                self.status_var.set(f"✅ Markov chain music generated (order {order})!")
            else:
                self.status_var.set("❌ Markov generation failed - insufficient training data")
                
        except Exception as e:
            self.status_var.set(f"Markov generation error: {str(e)}")
            print(f"Error in Markov generation: {e}")

    def generate_cellular(self):
        """Generate music using cellular automata"""
        try:
            self.status_var.set("Generating music with cellular automata...")
            
            # Create a 2D grid for cellular automata
            grid_width = 32  # Number of beats
            grid_height = 24  # Number of notes (2 octaves)
            
            # Initialize random grid
            grid = [[random.choice([0, 1]) for _ in range(grid_width)] for _ in range(grid_height)]
            
            # Apply cellular automata rules (Conway's Game of Life variant)
            generations = 5
            for gen in range(generations):
                new_grid = [row[:] for row in grid]  # Copy grid
                
                for y in range(1, grid_height - 1):
                    for x in range(1, grid_width - 1):
                        # Count live neighbors
                        neighbors = sum(grid[y+dy][x+dx] 
                                      for dy in [-1, 0, 1] 
                                      for dx in [-1, 0, 1] 
                                      if (dy, dx) != (0, 0))
                        
                        # Apply rules
                        if grid[y][x] == 1:  # Live cell
                            new_grid[y][x] = 1 if neighbors in [2, 3] else 0
                        else:  # Dead cell
                            new_grid[y][x] = 1 if neighbors == 3 else 0
                
                grid = new_grid
            
            # Convert grid to notes
            new_notes = []
            base_note = 60  # Middle C
            
            for y in range(grid_height):
                for x in range(grid_width):
                    if grid[y][x] == 1:
                        note = base_note + (grid_height - y - 1)  # Higher y = higher pitch
                        new_notes.append({
                            'note': note,
                            'start': x * 0.25,  # Quarter note spacing
                            'duration': 0.25,

                            'velocity': random.randint(60, 90),
                            'channel': 0
                        })
            
            if new_notes:
                self.generator.notes_data = new_notes
                self.generator.current_midi = self.generator.create_midi_file(new_notes)
                self.update_visualization()
                self.status_var.set(f"✅ Cellular automata music generated ({len(new_notes)} notes)!");
            else:
                self.status_var.set("❌ Cellular automata generated no notes")
                
        except Exception as e:
            self.status_var.set(f"Cellular automata error: {str(e)}")
            print(f"Error in cellular automata generation: {e}")

    def generate_fractal(self):
        """Generate music using fractal algorithms"""
        try:
            self.status_var.set("Generating fractal music...")
            
            # Simple fractal melody generation using L-systems
            axiom = "A"
            rules = {"A": "AB", "B": "A"}
            iterations = 4
            
            # Generate L-system string
            current = axiom
            for _ in range(iterations):
                next_string = ""
                for char in current:
                    next_string += rules.get(char, char)
                current = next_string
            
            # Convert to musical notes
            new_notes = []
            base_note = 60
            time = 0
            
            note_map = {"A": 0, "B": 2}  # Major scale intervals
            scale = [0, 2, 4, 5, 7, 9, 11]  # Major scale
            
            for char in current[:64]:  # Limit length
                if char in note_map:
                    scale_degree = note_map[char]
                    note = base_note + scale[scale_degree % len(scale)]
                    
                    new_notes.append({
                        'note': note,
                        'start': time,
                        'duration': 0.5,
                        'velocity': random.randint(70, 100),
                        'channel': 0
                    })
                    time += 0.5
            
            if new_notes:
                self.generator.notes_data = new_notes
                self.generator.current_midi = self.generator.create_midi_file(new_notes)
                self.update_visualization()
                self.status_var.set(f"✅ Fractal music generated ({len(new_notes)} notes)!");
            else:
                self.status_var.set("❌ Fractal generation produced no notes")
                
        except Exception as e:
            self.status_var.set(f"Fractal generation error: {str(e)}")
            print(f"Error in fractal generation: {e}")

    def generate_polyrhythm(self):
        """Generate polyrhythmic music"""
        try:
            self.status_var.set("Generating polyrhythmic music...")
            
            new_notes = []
            total_time = self.generator.settings.song_length_bars * 4  # 4 beats per bar
            
            # Create multiple rhythmic layers
            rhythms = [3, 4, 5]  # Different note divisions
            base_notes = [60, 64, 67]  # C major triad
            
            for i, (rhythm, base_note) in enumerate(zip(rhythms, base_notes)):
                note_interval = total_time / rhythm
                
                for beat in range(rhythm):
                    start_time = beat * note_interval
                    
                    new_notes.append({
                        'note': base_note + random.choice([0, 12]),  # Octave variation
                        'start': start_time,
                        'duration': note_interval * 0.8,  # Slight gap between notes
                        'velocity': random.randint(60, 90),
                        'channel': i
                    })
            
            if new_notes:
                self.generator.notes_data = new_notes
                self.generator.current_midi = self.generator.create_midi_file(new_notes)
                self.update_visualization()
                self.status_var.set(f"✅ Polyrhythmic music generated ({len(new_notes)} notes)!")
            else:
                self.status_var.set("❌ Polyrhythm generation failed")
                
        except Exception as e:
            self.status_var.set(f"Polyrhythm error: {str(e)}")
            print(f"Error in polyrhythm generation: {e}")

    def extract_notes_from_midi(self, midi_file):
        """Extract note data from a MIDI file for visualization"""
        try:
            notes_data = []
            current_time = 0
            active_notes = {}  # Track note_on events
            
            for track in midi_file.tracks:
                track_time = 0
                for msg in track:
                    track_time += msg.time
                    
                    if msg.type == 'note_on' and msg.velocity > 0:
                        # Start of a note
                        note_key = (msg.channel, msg.note)
                        active_notes[note_key] = {
                            'start': track_time / 480.0,  # Convert ticks to beats
                            'velocity': msg.velocity,
                            'note': msg.note,
                            'channel': msg.channel
                        }
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        # End of a note
                        note_key = (msg.channel, msg.note)
                        if note_key in active_notes:
                            note_data = active_notes[note_key]
                            note_data['duration'] = (track_time / 480.0) - note_data['start']
                            
                            if note_data['duration'] > 0:  # Valid duration
                                notes_data.append(note_data)
                            
                            del active_notes[note_key]
            
            # Handle any remaining active notes
            for note_data in active_notes.values():
                note_data['duration'] = 0.5  # Default duration
                notes_data.append(note_data)
            
            return notes_data
            
        except Exception as e:
            print(f"Error extracting notes from MIDI: {e}")
            return []

    def update_visualization(self):
        """Update the piano roll visualization with current notes"""
        try:
            self.ax.clear()
            
            if not self.generator.notes_data:
                self.ax.text(0.5, 0.5, "No notes to display", 
                            ha='center', va='center', color='white', fontsize=12)
                self.canvas.draw()
                return
                
            # Get min/max time and pitch values for scaling
            min_time = min(note.get('start', note.get('time', 0)) for note in self.generator.notes_data)
            max_time = max(note.get('start', note.get('time', 0)) + 
                          note.get('duration', 0.5) for note in self.generator.notes_data)
            
            # Add some padding
            time_padding = (max_time - min_time) * 0.05
            min_time = max(0, min_time - time_padding)
            max_time = max_time + time_padding
            
            # Draw note rectangles
            for note in self.generator.notes_data:
                # Get note properties
                pitch = note.get('note', 60)
                start = note.get('start', note.get('time', 0))
                duration = note.get('duration', 0.5)
                velocity = note.get('velocity', 80)
                channel = note.get('channel', 0)
                
                # Choose color based on channel
                color_map = {
                    0: '#3498db',  # Melody - blue
                    1: '#2ecc71',  # Bass - green
                    2: '#9b59b6',  # Pad - purple
                    3: '#e74c3c',  # Lead - red
                    9: '#f39c12'   # Drums - orange
                }
                color = color_map.get(channel, '#95a5a6')  # Default gray
                
                # Adjust opacity based on velocity
                alpha = 0.4 + (velocity / 127) * 0.6
                
                # Draw the note rectangle
                self.ax.add_patch(
                    plt.Rectangle(
                        (start, pitch - 0.4),
                        duration,
                        0.8,
                        color=color,
                        alpha=alpha
                    )
                )
            
            # Set axis limits and labels
            self.ax.set_xlim(min_time, max_time)
            self.ax.set_ylim(
                min(note.get('note', 60) for note in self.generator.notes_data) - 5,
                max(note.get('note', 60) for note in self.generator.notes_data) + 5
            )
            
            # Add grid and labels
            self.ax.grid(True, alpha=0.3, linestyle='--')
            self.ax.set_xlabel('Time (beats)')
            self.ax.set_ylabel('MIDI Note')
            self.ax.set_title('Piano Roll Visualization')
            
            # Draw piano keyboard on the y-axis
            self.draw_piano_keys()
            
            # Refresh the canvas
            self.canvas.draw()
            
        except Exception as e:
            print(f"Visualization error: {e}")

    def draw_piano_keys(self):
        """Draw piano keyboard markers on the y-axis"""
        try:
            # Get y-axis limits
            y_min, y_max = self.ax.get_ylim()
            
            # Round to integers and add padding
            y_min = max(0, int(y_min) - 1)
            y_max = min(127, int(y_max) + 1)
            
            # Create custom y-ticks for piano keys
            yticks = list(range(y_min, y_max + 1))
            self.ax.set_yticks(yticks)
            
            # Create labels with note names
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            labels = []
            
            for note in yticks:
                # Check if it's a C note for octave labels
                octave = (note // 12) - 1
                note_name = note_names[note % 12]
                
                # Add octave number for C notes
                if note_name == 'C':
                    label = f"{note_name}{octave}"
                else:
                    label = note_name
                    
                labels.append(label)
            
            self.ax.set_yticklabels(labels)
            
            # Color the background for white/black keys
            for note in range(y_min, y_max + 1):
                note_idx = note % 12
                # Check if it's a black key
                if note_idx in [1, 3, 6, 8, 10]:  # C#, D#, F#, G#, A#
                    self.ax.axhspan(note - 0.5, note + 0.5, color='black', alpha=0.1, zorder=-1)
                
        except Exception as e:
            print(f"Piano key drawing error: {e}")

# Main entry point - add this to ensure the app runs properly when called directly
if __name__ == "__main__":
    try:
        print("Starting MIDI Generator...")
        app = MIDIGeneratorGUI()
        app.root.mainloop()
        print("MIDI Generator closed.")
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()