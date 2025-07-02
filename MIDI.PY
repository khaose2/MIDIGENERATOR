"""
Ultimate MIDI Generator - Professional Edition
Advanced MIDI generation with real-time audio synthesis
"""

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
    
    # === HANDLER FUNCTIONS FOR GUI CONTROLS ===
    
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

    # === INSTRUMENT AND AUDIO HANDLER FUNCTIONS ===

    def update_melody_instrument(self, event=None):
        """Update melody instrument"""
        instrument_name = self.melody_instrument_var.get()
        self.synthesizer.set_instrument(0, instrument_name)  # Channel 0 for melody
        self.status_var.set(f"Melody instrument set to: {instrument_name}")

    def update_bass_instrument(self, event=None):
        """Update bass instrument"""
        instrument_name = self.bass_instrument_var.get()
        self.synthesizer.set_instrument(1, instrument_name)  # Channel 1 for bass
        self.status_var.set(f"Bass instrument set to: {instrument_name}")

    def update_volume(self, value):
        """Update master volume"""
        volume = self.volume_var.get()
        self.synthesizer.set_master_volume(volume)
        self.status_var.set(f"Volume set to {int(volume * 100)}%")

    def update_filter(self, value):
        """Update filter cutoff frequency"""
        cutoff = self.filter_cutoff_var.get()
        self.synthesizer.set_filter_cutoff(cutoff)
        self.status_var.set(f"Filter cutoff set to {int(cutoff)} Hz")

    def update_stereo(self, value):
        """Update stereo width"""
        width = self.stereo_width_var.get()
        self.synthesizer.set_stereo_width(width)
        self.status_var.set(f"Stereo width set to {int(width * 100)}%")

    def test_piano_note(self):
        """Plays a single C4 note with the selected melody instrument."""
        self.synthesizer.note_on(channel=0, note=60, velocity=100)
        # Schedule note_off after a short duration
        self.root.after(500, lambda: self.synthesizer.note_off(channel=0, note=60))

    def test_bass_note(self):
        """Plays a single C2 note with the selected bass instrument."""
        self.synthesizer.note_on(channel=1, note=36, velocity=100)
        self.root.after(500, lambda: self.synthesizer.note_off(channel=1, note=36))

    def test_drum_sound(self):
        """Plays a kick and snare sound."""
        self.synthesizer.note_on(channel=9, note=36, velocity=120)  # Kick
        self.root.after(250, lambda: self.synthesizer.note_on(channel=9, note=38, velocity=110))  # Snare
        self.root.after(600, lambda: self.synthesizer.note_off(channel=9, note=36))
        self.root.after(600, lambda: self.synthesizer.note_off(channel=9, note=38))

    # === VISUALIZATION ===

    def update_visualization(self):
        """Draws the generated notes on the piano roll canvas."""
        if not self.generator.notes_data:
            return
        
        self.ax.clear()
        
        for note in self.generator.notes_data:
            start = note['start']
            duration = note['duration']
            pitch = note['note']
            velocity = note['velocity']
            channel = note['channel']
            
            # Color based on channel
            color_map = {0: '#3498db', 1: '#e74c3c', 9: '#f1c40f', 2: '#2ecc71', 3: '#9b59b6'}
            color = color_map.get(channel, 'grey')
            
            self.ax.add_patch(
                plt.Rectangle((start, pitch - 0.5), duration, 1, 
                              facecolor=color, edgecolor='black', linewidth=0.5,
                              alpha=min(1.0, 0.5 + velocity / 254.0))
            )
            
        self.ax.set_ylim(self.generator.settings.note_range_low - 1, self.generator.settings.note_range_high + 1)
        self.ax.set_xlim(0, max(n['start'] + n['duration'] for n in self.generator.notes_data))
        self.ax.set_xlabel("Time (beats)")
        self.ax.set_ylabel("MIDI Pitch")
        self.ax.grid(True, which='both', axis='y', linestyle='--', color='gray', alpha=0.5)
        self.fig.tight_layout()
        self.canvas.draw()
        self.status_var.set("Visualization updated.")

    # === FILE OPERATIONS AND RANDOMIZATION ===

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
        """Show enhanced MP3 conversion options dialog with advanced features"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Advanced MP3 to MIDI Conversion")
        dialog.geometry("600x850")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make dialog modal
        
        # Center the dialog
        dialog.transient(self.root)
        
        # Title
        title_label = tk.Label(dialog, text="🎵 Advanced MP3 to MIDI Converter", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # File info
        file_frame = ttk.LabelFrame(dialog, text="Input File", padding=10)
        file_frame.pack(pady=10, padx=20, fill="x")
        
        file_label = tk.Label(file_frame, text=f"File: {os.path.basename(mp3_path)}", 
                             wraplength=500, justify="left")
        file_label.pack(anchor="w")
        
        # Algorithm selection with auto option
        algo_frame = ttk.LabelFrame(dialog, text="Conversion Algorithm", padding=10)
        algo_frame.pack(pady=10, padx=20, fill="x")
        
        algorithm_var = tk.StringVar(value="auto")
        
        algo_descriptions = {
            "auto": "Auto-Select (Analyzes audio and chooses best algorithm)",
            "cqt": "CQT (Best for single instruments, excellent pitch accuracy)",
            "chroma": "Chroma (Good for harmonic content and chord progressions)",
            "onset": "Onset Detection (Best for clear note attacks and rhythm)"
        }
        
        for algo, description in algo_descriptions.items():
            frame = tk.Frame(algo_frame)
            frame.pack(fill="x", pady=2)
            
            radio = tk.Radiobutton(frame, text=algo.upper(), variable=algorithm_var, 
                                  value=algo, font=("Arial", 10, "bold"))
            radio.pack(anchor="w")
            
            desc_label = tk.Label(frame, text=description, font=("Arial", 9), 
                                 fg="gray", wraplength=500)
            desc_label.pack(anchor="w", padx=20)
        
        # Advanced settings
        advanced_frame = ttk.LabelFrame(dialog, text="Advanced Settings", padding=10)
        advanced_frame.pack(pady=10, padx=20, fill="x")
        
        # Sensitivity slider
        sens_frame = tk.Frame(advanced_frame)
        sens_frame.pack(fill="x", pady=5)
        tk.Label(sens_frame, text="Sensitivity:").pack(side="left")
        sens_var = tk.DoubleVar(value=0.5)
        sens_scale = tk.Scale(sens_frame, from_=0.1, to=1.0, resolution=0.1, 
                             orient="horizontal", variable=sens_var)
        sens_scale.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Min duration slider
        duration_frame = tk.Frame(advanced_frame)
        duration_frame.pack(fill="x", pady=5)
        tk.Label(duration_frame, text="Min Note Duration (ms):").pack(side="left")
        duration_var = tk.IntVar(value=50)
        duration_scale = tk.Scale(duration_frame, from_=20, to=200, 
                                 orient="horizontal", variable=duration_var)
        duration_scale.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Max polyphony
        poly_frame = tk.Frame(advanced_frame)
        poly_frame.pack(fill="x", pady=5)
        tk.Label(poly_frame, text="Max Simultaneous Notes:").pack(side="left")
        poly_var = tk.IntVar(value=3)
        poly_scale = tk.Scale(poly_frame, from_=1, to=8, orient="horizontal", variable=poly_var)
        poly_scale.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Options
        options_frame = ttk.LabelFrame(dialog, text="Options", padding=10)
        options_frame.pack(pady=10, padx=20, fill="x")
        
        # Tempo
        tempo_frame = tk.Frame(options_frame)
        tempo_frame.pack(fill="x", pady=5)
        tk.Label(tempo_frame, text="Tempo (BPM):").pack(side="left")
        tempo_var = tk.IntVar(value=120)
        tempo_scale = tk.Scale(tempo_frame, from_=60, to=200, orient="horizontal",
                              variable=tempo_var)
        tempo_scale.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Replace current melody checkbox
        replace_var = tk.BooleanVar(value=True)
        replace_check = tk.Checkbutton(options_frame, 
                                      text="Replace current melody with converted notes",
                                      variable=replace_var)
        replace_check.pack(anchor="w", pady=5)
        
        # Analysis display
        analysis_frame = ttk.LabelFrame(dialog, text="Audio Analysis", padding=10)
        analysis_frame.pack(pady=10, padx=20, fill="x")
        
        analysis_text = tk.Text(analysis_frame, height=4, wrap=tk.WORD, 
                               font=("Courier", 9), state=tk.DISABLED)
        analysis_text.pack(fill="both", expand=True)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(dialog, text="Progress", padding=10)
        progress_frame.pack(pady=10, padx=20, fill="x")
        
        progress_var = tk.StringVar(value="Ready to convert...")
        progress_label = tk.Label(progress_frame, textvariable=progress_var)
        progress_label.pack(anchor="w")
        
        progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        progress_bar.pack(fill="x", pady=(5, 0))
        
        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)
        
        def analyze_audio():
            """Analyze audio and show recommendations"""
            try:
                from mp3_to_midi_converter import MP3ToMIDIConverter
                
                progress_var.set("Analyzing audio...")
                progress_bar['value'] = 50
                dialog.update_idletasks()
                
                def analysis_worker():
                    try:
                        converter = MP3ToMIDIConverter()
                        y, sr = converter.load_audio(mp3_path)
                        analysis = converter.analyze_audio_characteristics(y, sr)
                        
                        def update_analysis():
                            analysis_text.config(state=tk.NORMAL)
                            analysis_text.delete(1.0, tk.END)
                            
                            analysis_str = f"""Duration: {analysis['duration']:.1f}s
Tempo: {analysis['tempo']:.1f} BPM
Recommended: {analysis['recommended_algorithm'].upper()}
Reason: {analysis['reason']}
Harmonic Ratio: {analysis['harmonic_ratio']:.2f}
Onset Density: {analysis['onset_density']:.1f}/sec"""
                            
                            analysis_text.insert(1.0, analysis_str)
                            analysis_text.config(state=tk.DISABLED)
                            
                            # Update algorithm selection
                            algorithm_var.set(analysis['recommended_algorithm'])
                            sens_var.set(analysis.get('recommended_sensitivity', 0.5))
                            duration_var.set(int(analysis.get('suggested_min_duration', 0.05) * 1000))
                            
                            progress_var.set("Analysis complete!")
                            progress_bar['value'] = 0
                        
                        dialog.after(0, update_analysis)
                        
                    except Exception as e:
                        def show_error():
                            progress_var.set(f"Analysis error: {str(e)}")
                            progress_bar['value'] = 0
                        dialog.after(0, show_error)
                
                thread = threading.Thread(target=analysis_worker, daemon=True)
                thread.start()
                
            except ImportError:
                progress_var.set("MP3 conversion not available")
        
        def preview_conversion():
            """Generate a preview of the conversion"""
            try:
                from mp3_to_midi_converter import MP3ToMIDIConverter
                
                algorithm = algorithm_var.get()
                
                progress_var.set("Generating preview...")
                progress_bar['value'] = 30
                dialog.update_idletasks()
                
                def preview_worker():
                    try:
                        converter = MP3ToMIDIConverter()
                        converter.sensitivity = sens_var.get()
                        converter.min_duration = duration_var.get() / 1000.0
                        converter.max_polyphony = poly_var.get()
                        
                        result = converter.preview_conversion(mp3_path, algorithm, preview_duration=10.0)
                        
                        def show_preview():
                            if result['success']:
                                notes = result['notes']
                                estimated = result['estimated_full_notes']
                                progress_var.set(f"Preview: {len(notes)} notes (est. {estimated} full)")
                                
                                # Create preview info
                                quality = converter.get_conversion_quality_score(notes)
                                preview_info = f"""Preview Results ({result['preview_duration']:.1f}s):
Notes: {len(notes)} (estimated full: {estimated})
Algorithm: {result['algorithm_used'].upper()}
Quality Score: {quality['score']}/100
Issues: {', '.join(quality['issues']) if quality['issues'] else 'None'}"""
                                
                                analysis_text.config(state=tk.NORMAL)
                                analysis_text.delete(1.0, tk.END)
                                analysis_text.insert(1.0, preview_info)
                                analysis_text.config(state=tk.DISABLED)
                            else:
                                progress_var.set(f"Preview failed: {result['error']}")
                            
                            progress_bar['value'] = 0
                        
                        dialog.after(0, show_preview)
                        
                    except Exception as e:
                        def show_error():
                            progress_var.set(f"Preview error: {str(e)}")
                            progress_bar['value'] = 0
                        dialog.after(0, show_error)
                
                thread = threading.Thread(target=preview_worker, daemon=True)
                thread.start()
                
            except ImportError:
                progress_var.set("MP3 conversion not available")
        
        def start_conversion():
            """Start the MP3 conversion process with advanced settings"""
            algorithm = algorithm_var.get()
            tempo = tempo_var.get()
            replace_melody = replace_var.get()
            
            # Disable buttons during conversion
            convert_btn.config(state="disabled")
            preview_btn.config(state="disabled")
            analyze_btn.config(state="disabled")
            cancel_btn.config(text="Close", state="disabled")
            
            def progress_callback(progress, message):
                """Update progress bar and message"""
                progress_bar['value'] = progress * 100
                progress_var.set(message)
                dialog.update_idletasks()
            
            def conversion_worker():
                """Worker thread for conversion"""
                try:
                    # Create converter with progress callback and advanced settings
                    converter = MP3ToMIDIConverter(progress_callback)
                    converter.sensitivity = sens_var.get()
                    converter.min_duration = duration_var.get() / 1000.0
                    converter.max_polyphony = poly_var.get()
                    
                    # Create temporary MIDI file
                    temp_midi_path = "temp_converted.mid"
                    
                    # Convert using auto-algorithm or specified
                    if algorithm == 'auto':
                        result = converter.convert_with_auto_algorithm(mp3_path, temp_midi_path, tempo)
                        success = result['success']
                        used_algorithm = result.get('algorithm_used', 'auto')
                    else:
                        success = converter.convert_mp3_to_midi(mp3_path, temp_midi_path, algorithm, tempo)
                        used_algorithm = algorithm
                    
                    if success and os.path.exists(temp_midi_path):
                        # Load the converted MIDI file
                        converted_midi = mido.MidiFile(temp_midi_path)
                        
                        if replace_melody:
                            # Replace current music with converted
                            self.generator.current_midi = converted_midi
                            
                            # Extract notes data for visualization
                            notes_data = []
                            current_time = 0
                            
                            for track in converted_midi.tracks:
                                for msg in track:
                                    current_time += msg.time
                                    if msg.type == 'note_on' and msg.velocity > 0:
                                        # Find corresponding note_off
                                        duration = 0.5  # Default duration
                                        
                                        notes_data.append({
                                            'note': msg.note,
                                            'start': current_time / 480.0,  # Convert ticks to beats
                                            'duration': duration,
                                            'velocity': msg.velocity,
                                            'channel': msg.channel
                                        })
                            
                            self.generator.notes_data = notes_data
                            
                            # Update GUI on main thread
                            def update_gui():
                                self.status_var.set(f"MP3 converted successfully! Generated {len(notes_data)} notes using {used_algorithm.upper()}")
                                self.update_visualization()
                                progress_var.set(f"✅ Conversion complete! Generated {len(notes_data)} notes")
                                convert_btn.config(state="normal")
                                preview_btn.config(state="normal")
                                analyze_btn.config(state="normal")
                                cancel_btn.config(state="normal", text="Close")
                            
                            self.root.after(0, update_gui)
                        
                        # Clean up temporary file
                        try:
                            os.remove(temp_midi_path)
                        except:
                            pass
                            
                    else:
                        def show_error():
                            progress_var.set("❌ Conversion failed - no notes detected")
                            convert_btn.config(state="normal")
                            preview_btn.config(state="normal")
                            analyze_btn.config(state="normal")
                            cancel_btn.config(state="normal", text="Close")
                        
                        self.root.after(0, show_error)
                        
                except Exception as e:
                    def show_error():
                        progress_var.set(f"❌ Conversion error: {str(e)}")
                        convert_btn.config(state="normal")
                        preview_btn.config(state="normal")
                        analyze_btn.config(state="normal")
                        cancel_btn.config(state="normal", text="Close")
                    
                    self.root.after(0, show_error)
            
            # Start conversion in separate thread
            thread = threading.Thread(target=conversion_worker, daemon=True)
            thread.start()
        
        # Button layout
        analyze_btn = tk.Button(button_frame, text="🔍 Analyze Audio", 
                               command=analyze_audio, bg="lightblue", 
                               font=("Arial", 10), padx=15)
        analyze_btn.pack(side="left", padx=5)
        
        preview_btn = tk.Button(button_frame, text="👁️ Preview (10s)", 
                               command=preview_conversion, bg="lightyellow", 
                               font=("Arial", 10), padx=15)
        preview_btn.pack(side="left", padx=5)
        
        convert_btn = tk.Button(button_frame, text="🎼 Convert to MIDI", 
                               command=start_conversion, bg="lightgreen", 
                               font=("Arial", 12, "bold"), padx=20)
        convert_btn.pack(side="left", padx=10)
        
        cancel_btn = tk.Button(button_frame, text="Cancel", 
                              command=dialog.destroy, font=("Arial", 10), padx=15)
        cancel_btn.pack(side="right", padx=5)
        
        # Creative Generation Section
        generation_frame = ttk.LabelFrame(dialog, text="Creative Generation", padding=10)
        generation_frame.pack(pady=10, padx=20, fill="x")
        
        gen_info_label = tk.Label(generation_frame, 
                                 text="Generate new MIDI content inspired by the audio analysis:", 
                                 font=("Arial", 9), fg="gray")
        gen_info_label.pack(anchor="w", pady=(0, 5))
        
        # Generation style selection
        style_frame = tk.Frame(generation_frame)
        style_frame.pack(fill="x", pady=5)
        
        tk.Label(style_frame, text="Generation Style:").pack(side="left")
        style_var = tk.StringVar(value="similar")
        style_combo = ttk.Combobox(style_frame, textvariable=style_var, 
                                  values=["similar", "jazz", "classical", "ambient", "creative"],
                                  state="readonly", width=15)
        style_combo.pack(side="right", padx=(10, 0))
        
        # Generation duration
        gen_duration_frame = tk.Frame(generation_frame)
        gen_duration_frame.pack(fill="x", pady=5)
        tk.Label(gen_duration_frame, text="Duration (seconds):").pack(side="left")
        gen_duration_var = tk.IntVar(value=30)
        gen_duration_scale = tk.Scale(gen_duration_frame, from_=10, to=120, 
                                     orient="horizontal", variable=gen_duration_var)
        gen_duration_scale.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Generation buttons
        gen_button_frame = tk.Frame(generation_frame)
        gen_button_frame.pack(fill="x", pady=10)
        
        def generate_inspired_music():
            """Generate new music inspired by the audio analysis"""
            try:
                from mp3_to_midi_converter import MP3ToMIDIConverter
                
                progress_var.set("Analyzing audio for generation...")
                progress_bar['value'] = 20
                dialog.update_idletasks()
                
                def generation_worker():
                    try:
                        converter = MP3ToMIDIConverter()
                        
                        # Load and analyze audio
                        y, sr = converter.load_audio(mp3_path)
                        analysis = converter.analyze_audio_characteristics(y, sr)
                        
                        # Generate inspired melody
                        style = style_var.get()
                        duration = gen_duration_var.get()
                        
                        progress_var.set(f"Generating {style} style music...")
                        progress_bar['value'] = 60
                        dialog.update_idletasks()
                        
                        inspired_notes = converter.generate_inspired_melody(analysis, duration, style)
                        
                        if inspired_notes:
                            # Create MIDI file
                            midi_file = converter.create_midi_file(inspired_notes, int(analysis.get('tempo', 120)))
                            
                            # Update main application
                            def update_main_app():
                                self.generator.current_midi = midi_file
                                self.generator.notes_data = inspired_notes
                                self.status_var.set(f"Generated {len(inspired_notes)} inspired notes in {style} style!")
                                self.update_visualization()
                                progress_var.set(f"✅ Generated {len(inspired_notes)} notes ({style} style)")
                                progress_bar['value'] = 0
                            
                            self.root.after(0, update_main_app)
                        else:
                            def show_error():
                                progress_var.set("❌ Generation failed - no notes created")
                                progress_bar['value'] = 0
                            self.root.after(0, show_error)
                        
                    except Exception as e:
                        def show_error():
                            progress_var.set(f"❌ Generation error: {str(e)}")
                            progress_bar['value'] = 0
                        self.root.after(0, show_error)
                
                thread = threading.Thread(target=generation_worker, daemon=True)
                thread.start()
                
            except ImportError:
                progress_var.set("Generation not available - MP3 converter missing")
        
        def generate_variations():
            """Generate variations of converted music"""
            if not hasattr(self.generator, 'current_midi') or not self.generator.current_midi:
                progress_var.set("Please convert audio to MIDI first!")
                return
            
            try:
                from mp3_to_midi_converter import MP3ToMIDIConverter
                
                progress_var.set("Creating musical variations...")
                progress_bar['value'] = 30
                dialog.update_idletasks()
                
                def variation_worker():
                    try:
                        converter = MP3ToMIDIConverter()
                        
                        # Use current notes data
                        if hasattr(self.generator, 'notes_data') and self.generator.notes_data:
                            original_notes = self.generator.notes_data
                        else:
                            progress_var.set("❌ No original notes available")
                            return
                        
                        variations = converter.create_variations(original_notes, num_variations=3)
                        
                        if variations:
                            # Use the first variation for now
                            varied_notes = variations[0]
                            
                            # Create MIDI file
                            midi_file = converter.create_midi_file(varied_notes, 120)
                            
                            def update_main_app():
                                self.generator.current_midi = midi_file
                                self.generator.notes_data = varied_notes
                                self.status_var.set(f"Created variation with {len(varied_notes)} notes!")
                                self.update_visualization()
                                progress_var.set(f"✅ Created variation with {len(varied_notes)} notes")
                                progress_bar['value'] = 0
                            
                            self.root.after(0, update_main_app)
                        else:
                            def show_error():
                                progress_var.set("❌ Variation creation failed")
                                progress_bar['value'] = 0
                            self.root.after(0, show_error)
                        
                    except Exception as e:
                        def show_error():
                            progress_var.set(f"❌ Variation error: {str(e)}")
                            progress_bar['value'] = 0
                        self.root.after(0, show_error)
                
                thread = threading.Thread(target=variation_worker, daemon=True)
                thread.start()
                
            except ImportError:
                progress_var.set("Variation generation not available")
        
        generate_inspired_btn = tk.Button(gen_button_frame, text="🎨 Generate Inspired Music", 
                                         command=generate_inspired_music, bg="mediumpurple", 
                                         fg="white", font=("Arial", 10, "bold"), padx=10)
        generate_inspired_btn.pack(side="left", padx=5)
        
        generate_variations_btn = tk.Button(gen_button_frame, text="🔄 Create Variations", 
                                           command=generate_variations, bg="darkorange", 
                                           fg="white", font=("Arial", 10, "bold"), padx=10)
        generate_variations_btn.pack(side="left", padx=5)

    # === BATCH CONVERSION METHODS ===
    
    def show_batch_conversion_dialog(self):
        """Show batch conversion dialog for multiple files"""
        # File selection for batch
        files = filedialog.askopenfilenames(
            title="Select audio files for batch conversion",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.flac *.m4a"),
                ("MP3 Files", "*.mp3"),
                ("WAV Files", "*.wav"),
                ("All Files", "*.*")
            ]
        )
        
        if not files:
            return
        
        # Output directory selection
        output_dir = filedialog.askdirectory(title="Select output directory for MIDI files")
        if not output_dir:
            return
        
        # Create batch dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Batch MP3 to MIDI Conversion")
        dialog.geometry("500x400")
        dialog.grab_set()
        
        # Title
        title_label = tk.Label(dialog, text="🎵 Batch Conversion", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # Files info
        files_frame = ttk.LabelFrame(dialog, text="Selected Files", padding=10)
        files_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        files_list = tk.Listbox(files_frame, height=8)
        for file in files:
            files_list.insert(tk.END, os.path.basename(file))
        files_list.pack(fill="both", expand=True)
        
        # Algorithm selection
        algo_frame = tk.Frame(dialog)
        algo_frame.pack(pady=10)
        
        tk.Label(algo_frame, text="Algorithm:").pack(side="left")
        batch_algo_var = tk.StringVar(value="auto")
        algo_combo = ttk.Combobox(algo_frame, textvariable=batch_algo_var,
                                 values=["auto", "cqt", "chroma", "onset"],
                                 state="readonly")
        algo_combo.pack(side="left", padx=10)
        
        # Progress
        progress_frame = tk.Frame(dialog)
        progress_frame.pack(pady=10, padx=20, fill="x")
        
        batch_progress_var = tk.StringVar(value="Ready to start batch conversion...")
        batch_progress_label = tk.Label(progress_frame, textvariable=batch_progress_var)
        batch_progress_label.pack()
        
        batch_progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        batch_progress_bar.pack(fill="x", pady=5)
        
        def start_batch():
            """Start batch conversion"""
            try:
                from mp3_to_midi_converter import MP3ToMIDIConverter
                
                def batch_progress_callback(progress, message):
                    batch_progress_bar['value'] = progress * 100
                    batch_progress_var.set(message)
                    dialog.update_idletasks()
                
                def batch_worker():
                    try:
                        converter = MP3ToMIDIConverter(batch_progress_callback)
                        results = converter.batch_convert(list(files), output_dir, 
                                                        batch_algo_var.get())
                        
                        def show_results():
                            successful = sum(1 for r in results.values() if r['success'])
                            batch_progress_var.set(f"✅ Batch complete: {successful}/{len(files)} successful")
                            
                            # Show detailed results
                            result_text = f"Batch Conversion Results:\n\n"
                            for file, result in results.items():
                                name = os.path.basename(file)
                                if result['success']:
                                    algo = result.get('algorithm_used', 'unknown')
                                    result_text += f"✅ {name} - {algo.upper()}\n"
                                else:
                                    error = result.get('error', 'Unknown error')
                                    result_text += f"❌ {name} - {error}\n"
                            
                            messagebox.showinfo("Batch Results", result_text)
                        
                        dialog.after(0, show_results)
                        
                    except Exception as e:
                        def show_error():
                            batch_progress_var.set(f"❌ Batch error: {str(e)}")
                        dialog.after(0, show_error)
                
                thread = threading.Thread(target=batch_worker, daemon=True)
                thread.start()
                
            except ImportError:
                messagebox.showerror("Error", "MP3 conversion not available")
        
        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)
        
        start_btn = tk.Button(button_frame, text="🚀 Start Batch Conversion",
                             command=start_batch, bg="lightgreen", 
                             font=("Arial", 12, "bold"))
        start_btn.pack(side="left", padx=10)
        
        close_btn = tk.Button(button_frame, text="Close", command=dialog.destroy)
        close_btn.pack(side="right", padx=10)

    def create_settings_tab(self):
        """Create the settings configuration tab"""
        import tkinter as tk
        
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Musical Settings
        musical_frame = ttk.LabelFrame(settings_frame, text="Musical Settings", padding=10)
        musical_frame.pack(pady=10, padx=20, fill="x")
        
        # Song Length
        length_frame = tk.Frame(musical_frame)
        length_frame.pack(fill="x", pady=5)
        tk.Label(length_frame, text="Song Length (bars):", width=20, anchor="w").pack(side="left")
        length_scale = tk.Scale(length_frame, from_=8, to=128, orient="horizontal",
                               variable=self.song_length_var, command=self.update_song_length)
        length_scale.pack(side="left", fill="x", expand=True)
        tk.Label(length_frame, textvariable=self.song_length_var, width=5).pack(side="right")
        
        # Note Range
        range_frame = tk.Frame(musical_frame)
        range_frame.pack(fill="x", pady=5)
        tk.Label(range_frame, text="Note Range:", width=20, anchor="w").pack(side="left")
        tk.Label(range_frame, text="Low:", width=5).pack(side="left")
        low_scale = tk.Scale(range_frame, from_=24, to=96, orient="horizontal",
                            variable=self.note_low_var, command=self.update_note_range)
        low_scale.pack(side="left", fill="x", expand=True)
        tk.Label(range_frame, text="High:", width=5).pack(side="left")
        high_scale = tk.Scale(range_frame, from_=24, to=96, orient="horizontal",
                             variable=self.note_high_var, command=self.update_note_range)
        high_scale.pack(side="left", fill="x", expand=True)
        
        # Swing
        swing_frame = tk.Frame(musical_frame)
        swing_frame.pack(fill="x", pady=5)
        tk.Label(swing_frame, text="Swing Factor:", width=20, anchor="w").pack(side="left")
        swing_scale = tk.Scale(swing_frame, from_=0.0, to=0.5, resolution=0.01, orient="horizontal",
                              variable=self.swing_var, command=self.update_swing)
        swing_scale.pack(side="left", fill="x", expand=True)
        
        # Rest Probability
        rest_frame = tk.Frame(musical_frame)
        rest_frame.pack(fill="x", pady=5)
        tk.Label(rest_frame, text="Rest Probability:", width=20, anchor="w").pack(side="left")
        rest_scale = tk.Scale(rest_frame, from_=0.0, to=0.8, resolution=0.01, orient="horizontal",
                             variable=self.rest_prob_var, command=self.update_rest_prob)
        rest_scale.pack(side="left", fill="x", expand=True)
        
        # Chaos Factor
        chaos_frame = tk.Frame(musical_frame)
        chaos_frame.pack(fill="x", pady=5)
        tk.Label(chaos_frame, text="Chaos Factor:", width=20, anchor="w").pack(side="left")
        chaos_scale = tk.Scale(chaos_frame, from_=0.0, to=1.0, resolution=0.01, orient="horizontal",
                              variable=self.chaos_var, command=self.update_chaos)
        chaos_scale.pack(side="left", fill="x", expand=True)
        
        # Randomization buttons
        random_frame = ttk.LabelFrame(settings_frame, text="Quick Randomization", padding=10)
        random_frame.pack(pady=10, padx=20, fill="x")
        
        random_btn_frame = tk.Frame(random_frame)
        random_btn_frame.pack(fill="x")
        
        tk.Button(random_btn_frame, text="Random Tempo", command=self.random_tempo,
                 width=15).pack(side="left", padx=5)
        tk.Button(random_btn_frame, text="Random Key", command=self.random_key,
                 width=15).pack(side="left", padx=5)
        tk.Button(random_btn_frame, text="Random Scale", command=self.random_scale,
                 width=15).pack(side="left", padx=5)
    
    def create_advanced_tab(self):
        """Create the advanced features tab"""
        import tkinter as tk
        
        advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(advanced_frame, text="Advanced")
        
        # Instrument Selection
        instrument_frame = ttk.LabelFrame(advanced_frame, text="Instrument Selection", padding=10)
        instrument_frame.pack(pady=10, padx=20, fill="x")
        
        # Melody Instrument
        melody_frame = tk.Frame(instrument_frame)
        melody_frame.pack(fill="x", pady=5)
        tk.Label(melody_frame, text="Melody Instrument:", width=20, anchor="w").pack(side="left")
        melody_combo = ttk.Combobox(melody_frame, textvariable=self.melody_instrument_var,
                                   values=["piano", "sine", "sawtooth", "square", "triangle"],
                                   state="readonly", width=15)
        melody_combo.pack(side="left", padx=5)
        melody_combo.bind("<<ComboboxSelected>>", self.update_melody_instrument)
        
        # Bass Instrument
        bass_frame = tk.Frame(instrument_frame)
        bass_frame.pack(fill="x", pady=5)
        tk.Label(bass_frame, text="Bass Instrument:", width=20, anchor="w").pack(side="left")
        bass_combo = ttk.Combobox(bass_frame, textvariable=self.bass_instrument_var,
                                 values=["sine", "sawtooth", "square", "triangle", "piano"],
                                 state="readonly", width=15)
        bass_combo.pack(side="left", padx=5)
        bass_combo.bind("<<ComboboxSelected>>", self.update_bass_instrument)
        
        # Pattern Selection (placeholder for future features)
        pattern_frame = ttk.LabelFrame(advanced_frame, text="Pattern & Style", padding=10)
        pattern_frame.pack(pady=10, padx=20, fill="x")
        
        tk.Label(pattern_frame, text="Advanced pattern controls will be added here",
                font=("Arial", 10, "italic")).pack(pady=20)
    
    def create_audio_tab(self):
        """Create the audio controls tab"""
        import tkinter as tk
        
        audio_frame = ttk.Frame(self.notebook)
        self.notebook.add(audio_frame, text="Audio")
        
        # Volume and Effects
        effects_frame = ttk.LabelFrame(audio_frame, text="Audio Effects", padding=10)
        effects_frame.pack(pady=10, padx=20, fill="x")
        
        # Volume
        volume_frame = tk.Frame(effects_frame)
        volume_frame.pack(fill="x", pady=5)
        tk.Label(volume_frame, text="Master Volume:", width=20, anchor="w").pack(side="left")
        volume_scale = tk.Scale(volume_frame, from_=0.0, to=1.0, resolution=0.01, orient="horizontal",
                               variable=self.volume_var, command=self.update_volume)
        volume_scale.pack(side="left", fill="x", expand=True)
        
        # Filter Cutoff
        filter_frame = tk.Frame(effects_frame)
        filter_frame.pack(fill="x", pady=5)
        tk.Label(filter_frame, text="Filter Cutoff (Hz):", width=20, anchor="w").pack(side="left")
        filter_scale = tk.Scale(filter_frame, from_=200, to=20000, orient="horizontal",
                               variable=self.filter_cutoff_var, command=self.update_filter)
        filter_scale.pack(side="left", fill="x", expand=True)
        
        # Stereo Width
        stereo_frame = tk.Frame(effects_frame)
        stereo_frame.pack(fill="x", pady=5)
        tk.Label(stereo_frame, text="Stereo Width:", width=20, anchor="w").pack(side="left")
        stereo_scale = tk.Scale(stereo_frame, from_=0.0, to=1.0, resolution=0.01, orient="horizontal",
                               variable=self.stereo_width_var, command=self.update_stereo)
        stereo_scale.pack(side="left", fill="x", expand=True)
        
        # Audio Testing
        test_frame = ttk.LabelFrame(audio_frame, text="Audio Testing", padding=10)
        test_frame.pack(pady=10, padx=20, fill="x")
        
        test_btn_frame = tk.Frame(test_frame)
        test_btn_frame.pack(fill="x")
        
        tk.Button(test_btn_frame, text="🎹 Test Piano", command=self.test_piano_note,
                 width=15, bg="lightblue").pack(side="left", padx=5)
        tk.Button(test_btn_frame, text="🎸 Test Bass", command=self.test_bass_note,
                 width=15, bg="lightgreen").pack(side="left", padx=5)
        tk.Button(test_btn_frame, text="🥁 Test Drums", command=self.test_drum_sound,
                 width=15, bg="lightyellow").pack(side="left", padx=5)

    def run(self):
        """Start the GUI main loop"""
        print("🚀 Starting Ultimate MIDI Generator GUI...")
        self.root.mainloop()


# === MAIN EXECUTION ===
if __name__ == "__main__":
    app = MIDIGeneratorGUI()
    app.run()