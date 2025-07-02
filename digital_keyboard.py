"""
Interactive Digital Keyboard for MIDI Generator
Features clickable piano keys and keyboard shortcuts with live MIDI playback
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time
import threading
import mido
import string
import os
import random

class DigitalKeyboard:
    """Interactive piano keyboard with MIDI playback and recording"""
    
    def __init__(self, parent, synthesizer, octaves=3, start_octave=4):
        """
        Initialize digital keyboard UI
        
        Args:
            parent: Parent Tkinter frame/window
            synthesizer: SoftwareSynthesizer instance for audio playback
            octaves: Number of octaves to display (default 3)
            start_octave: Starting octave (default 4 - middle C)
        """
        self.parent = parent
        self.synthesizer = synthesizer
        self.octaves = octaves
        self.start_octave = start_octave
        
        # Key mappings (computer keyboard to MIDI notes)
        self.key_mappings = {}
        
        # Currently pressed keys
        self.pressed_keys = set()
        
        # Selected instrument
        self.instrument = "Acoustic Grand Piano"
        self.channel = 0
        
        # Recording state
        self.recording = False
        self.recorded_notes = []
        self.record_start_time = None
        
        # Arpeggiator state
        self.arpeggiator_active = False
        self.arpeggiator_thread = None
        self.arpeggiator_stop_event = threading.Event()
        
        # Create the UI
        self.create_keyboard_ui()
        self.setup_key_bindings()
        self.setup_controls()
        
        # Initialize focus for keyboard events
        self.parent.focus_set()
        self.parent.bind("<FocusIn>", self.on_focus_in)
        
        print("✅ Digital Keyboard initialized successfully")
    
    def create_keyboard_ui(self):
        """Create the piano keyboard UI"""
        self.frame = tk.Frame(self.parent, bg="#f0f0f0")
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title and main controls
        self.control_frame = tk.Frame(self.frame, bg="#f0f0f0")
        self.control_frame.pack(fill="x", pady=5)
        
        title_label = tk.Label(self.control_frame, text="🎹 Digital Keyboard", 
                              font=("Arial", 16, "bold"), bg="#f0f0f0")
        title_label.pack(side="left")
        
        # Keyboard canvas for drawing piano keys
        self.canvas_height = 200
        self.canvas = tk.Canvas(self.frame, height=self.canvas_height, 
                              bg="white", highlightthickness=1, bd=2, relief="sunken")
        self.canvas.pack(fill="x", expand=True, pady=10)
        
        # Bind resize event to redraw keyboard
        self.canvas.bind("<Configure>", self.draw_keyboard)
        
        # Key binding display frame
        binding_frame = tk.Frame(self.frame, bg="#f0f0f0")
        binding_frame.pack(fill="x", pady=5)
        
        tk.Label(binding_frame, text="Keyboard Shortcuts:", 
               font=("Arial", 10, "bold"), bg="#f0f0f0").pack(anchor="w")
        
        self.binding_label = tk.Label(binding_frame, 
                                    text="Default shortcuts: a,s,d,f,g,h,j,k for white keys | w,e,t,y,u for black keys", 
                                    font=("Arial", 9), justify="left", bg="#f0f0f0", fg="blue")
        self.binding_label.pack(anchor="w", pady=5)
        
        # Store canvas references
        self.white_keys = []
        self.black_keys = []
        
        # Initialize assignment mode
        self.assigning_shortcut = False
        self.note_to_assign = None
    
    def setup_controls(self):
        """Set up instrument and recording controls"""
        # Instrument selection
        instrument_frame = tk.Frame(self.control_frame, bg="#f0f0f0")
        instrument_frame.pack(side="right", padx=10)
        
        tk.Label(instrument_frame, text="Instrument:", bg="#f0f0f0").pack(side="left")
        
        instrument_list = ["Acoustic Grand Piano", "Electric Piano", "Harpsichord", 
                          "Xylophone", "Organ", "Guitar", "Bass", "Strings", "Choir", "Flute"]
        self.instrument_var = tk.StringVar(value=self.instrument)
        instrument_menu = ttk.Combobox(instrument_frame, textvariable=self.instrument_var,
                                      values=instrument_list, width=20, state="readonly")
        instrument_menu.pack(side="left", padx=5)
        instrument_menu.bind("<<ComboboxSelected>>", self.change_instrument)
        
        # Octave controls
        octave_frame = tk.Frame(self.control_frame, bg="#f0f0f0")
        octave_frame.pack(side="right", padx=20)
        
        oct_down_btn = tk.Button(octave_frame, text="◀ Oct", command=self.decrease_octave,
                                bg="#e0e0e0", relief="raised", bd=1)
        oct_down_btn.pack(side="left")
        
        self.octave_label = tk.Label(octave_frame, text=f"Octave: {self.start_octave}", 
                                   width=10, bg="#f0f0f0", font=("Arial", 9, "bold"))
        self.octave_label.pack(side="left", padx=5)
        
        oct_up_btn = tk.Button(octave_frame, text="Oct ▶", command=self.increase_octave,
                              bg="#e0e0e0", relief="raised", bd=1)
        oct_up_btn.pack(side="left")
        
        # Channel selection
        channel_frame = tk.Frame(self.frame, bg="#f0f0f0")
        channel_frame.pack(fill="x", pady=5)
        
        tk.Label(channel_frame, text="MIDI Channel:", 
               font=("Arial", 10, "bold"), bg="#f0f0f0").pack(side="left")
        
        self.channel_var = tk.IntVar(value=0)
        channel_spin = tk.Spinbox(channel_frame, from_=0, to=15, width=2,
                                textvariable=self.channel_var, bg="white")
        channel_spin.pack(side="left", padx=5)
        
        # Update channel when changed
        self.channel_var.trace_add("write", 
                                 lambda *args: setattr(self, "channel", self.channel_var.get()))
        
        # Recording controls
        record_frame = tk.Frame(self.frame, bg="#f0f0f0")
        record_frame.pack(fill="x", pady=5)
        
        tk.Label(record_frame, text="Recording:", 
               font=("Arial", 10, "bold"), bg="#f0f0f0").pack(side="left")
        
        self.record_button = tk.Button(record_frame, text="⚫ Record", 
                                     command=self.record_toggle, width=10,
                                     bg="#ff6b6b", fg="white", font=("Arial", 9, "bold"))
        self.record_button.pack(side="left", padx=10)
        
        export_button = tk.Button(record_frame, text="💾 Export MIDI", 
                                command=self.export_midi, width=12,
                                bg="#4ecdc4", fg="white", font=("Arial", 9, "bold"))
        export_button.pack(side="left", padx=5)
        
        clear_button = tk.Button(record_frame, text="🗑 Clear", 
                               command=self.clear_recording, width=8,
                               bg="#95a5a6", fg="white", font=("Arial", 9, "bold"))
        clear_button.pack(side="left", padx=5)
        
        # Add chord buttons
        self.setup_chord_buttons()
        
        # Add arpeggiator controls
        self.setup_arpeggiator()
        
        # Add velocity and sustain controls
        self.setup_performance_controls()
    
    def setup_chord_buttons(self):
        """Add buttons for common chords"""
        chord_frame = tk.Frame(self.frame, bg="#f0f0f0")
        chord_frame.pack(fill="x", pady=5)
        
        tk.Label(chord_frame, text="Quick Chords:", 
               font=("Arial", 10, "bold"), bg="#f0f0f0").pack(side="left")
        
        # Common chord types
        chords = [
            ("Major", [0, 4, 7]),
            ("Minor", [0, 3, 7]),
            ("7th", [0, 4, 7, 10]),
            ("m7", [0, 3, 7, 10]),
            ("Maj7", [0, 4, 7, 11]),
            ("Sus4", [0, 5, 7])
        ]
        
        for name, intervals in chords:
            btn = tk.Button(chord_frame, text=name, width=6,
                          command=lambda i=intervals, n=name: self.play_chord(i, n),
                          bg="#3498db", fg="white", font=("Arial", 8, "bold"))
            btn.pack(side="left", padx=2)
    
    def setup_arpeggiator(self):
        """Add arpeggiator controls"""
        arp_frame = tk.Frame(self.frame, bg="#f0f0f0")
        arp_frame.pack(fill="x", pady=5)
        
        tk.Label(arp_frame, text="Arpeggiator:", 
               font=("Arial", 10, "bold"), bg="#f0f0f0").pack(side="left")
        
        # Pattern selection
        self.pattern_var = tk.StringVar(value="Up")
        patterns = ["Up", "Down", "UpDown", "Random"]
        
        for name in patterns:
            rb = tk.Radiobutton(arp_frame, text=name, variable=self.pattern_var, 
                              value=name, bg="#f0f0f0", font=("Arial", 8))
            rb.pack(side="left", padx=3)
        
        # Speed control
        tk.Label(arp_frame, text="Speed:", bg="#f0f0f0", font=("Arial", 9)).pack(side="left", padx=(10, 0))
        self.speed_var = tk.DoubleVar(value=0.2)
        speed_scale = tk.Scale(arp_frame, from_=0.05, to=0.5, resolution=0.05,
                             orient="horizontal", variable=self.speed_var,
                             length=100, bg="#f0f0f0", font=("Arial", 8))
        speed_scale.pack(side="left")
        
        # Activate button
        self.arp_button = tk.Button(arp_frame, text="Arpeggiator Off", 
                                  command=self.toggle_arpeggiator,
                                  bg="#e74c3c", fg="white", font=("Arial", 9, "bold"))
        self.arp_button.pack(side="left", padx=10)
    
    def setup_performance_controls(self):
        """Add performance controls for velocity and sustain"""
        perf_frame = tk.Frame(self.frame, bg="#f0f0f0")
        perf_frame.pack(fill="x", pady=5)
        
        tk.Label(perf_frame, text="Performance:", 
               font=("Arial", 10, "bold"), bg="#f0f0f0").pack(side="left")
        
        # Velocity control
        tk.Label(perf_frame, text="Velocity:", bg="#f0f0f0", font=("Arial", 9)).pack(side="left", padx=(10, 0))
        self.velocity_var = tk.IntVar(value=100)
        velocity_scale = tk.Scale(perf_frame, from_=30, to=127, orient="horizontal",
                                variable=self.velocity_var, length=120,
                                bg="#f0f0f0", font=("Arial", 8))
        velocity_scale.pack(side="left", padx=5)
        
        # Sustain pedal
        self.sustain_var = tk.BooleanVar(value=False)
        sustain_check = tk.Checkbutton(perf_frame, text="Sustain Pedal",
                                     variable=self.sustain_var, bg="#f0f0f0",
                                     font=("Arial", 9, "bold"), fg="darkgreen")
        sustain_check.pack(side="left", padx=10)
        
        # Panic button
        panic_btn = tk.Button(perf_frame, text="🚨 All Notes Off", 
                            command=self.panic_stop, width=12,
                            bg="#e74c3c", fg="white", font=("Arial", 9, "bold"))
        panic_btn.pack(side="right", padx=5)
    
    def draw_keyboard(self, event=None):
        """Draw the piano keyboard on the canvas"""
        # Clear canvas
        self.canvas.delete("all")
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 1:  # Canvas not ready yet
            self.parent.after(100, self.draw_keyboard)
            return
        
        # Calculate key dimensions
        white_key_width = canvas_width / (7 * self.octaves)
        white_key_height = self.canvas_height
        black_key_width = white_key_width * 0.6
        black_key_height = self.canvas_height * 0.65
        
        # White key positions (offsets) within an octave
        white_key_positions = [0, 1, 2, 3, 4, 5, 6]  # C, D, E, F, G, A, B
        
        # Black key positions (offsets) within an octave
        black_key_positions = [0.7, 1.3, 3.7, 4.3, 5.3]  # C#, D#, F#, G#, A#
        
        # Draw white keys
        self.white_keys = []
        for octave in range(self.octaves):
            for i, pos in enumerate(white_key_positions):
                x1 = (octave * 7 + pos) * white_key_width
                y1 = 0
                x2 = x1 + white_key_width
                y2 = white_key_height
                
                # Calculate MIDI note number
                note = 12 * (self.start_octave + octave) + [0, 2, 4, 5, 7, 9, 11][i]
                
                # Create key with tag
                key_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill="white", 
                                                    outline="black", width=2,
                                                    tags=(f"key_{note}", "white_key"))
                
                # Store key info
                self.white_keys.append({
                    'id': key_id,
                    'note': note,
                    'rect': (x1, y1, x2, y2),
                    'pressed': False
                })
        
        # Draw black keys (on top of white keys)
        self.black_keys = []
        for octave in range(self.octaves):
            for i, pos in enumerate(black_key_positions):
                x1 = (octave * 7 + pos) * white_key_width - black_key_width/2
                y1 = 0
                x2 = x1 + black_key_width
                y2 = black_key_height
                
                # Calculate MIDI note number
                note = 12 * (self.start_octave + octave) + [1, 3, 6, 8, 10][i]
                
                # Create key with tag
                key_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill="black", 
                                                    outline="gray", width=1,
                                                    tags=(f"key_{note}", "black_key"))
                
                # Store key info
                self.black_keys.append({
                    'id': key_id,
                    'note': note,
                    'rect': (x1, y1, x2, y2),
                    'pressed': False
                })
        
        # Draw note labels
        for octave in range(self.octaves):
            x = (octave * 7) * white_key_width + white_key_width/2
            y = white_key_height - 20
            self.canvas.create_text(x, y, text=f"C{self.start_octave + octave}", 
                                  font=("Arial", 8), fill="gray")
        
        # Draw key bindings if assigned
        self.draw_key_bindings()
        
        # Bind click events
        self.canvas.bind("<Button-1>", self.on_key_click)
        self.canvas.bind("<ButtonRelease-1>", self.on_key_release)
        self.canvas.bind("<B1-Motion>", self.on_key_drag)
    
    def draw_key_bindings(self):
        """Draw keyboard shortcuts on piano keys"""
        for key in self.white_keys + self.black_keys:
            note = key['note']
            if note in self.key_mappings.values():
                # Find keyboard key for this note
                for kb_key, midi_note in self.key_mappings.items():
                    if midi_note == note:
                        # Place text on key
                        x1, y1, x2, y2 = key['rect']
                        is_white = note in [k['note'] for k in self.white_keys]
                        self.canvas.create_text((x1 + x2) / 2, y2 - 15, 
                                              text=kb_key.upper(), font=("Arial", 8, "bold"),
                                              fill="blue" if is_white else "white")
                        break
    
    def setup_key_bindings(self):
        """Set up default computer keyboard bindings"""
        # Default key mappings (middle row of keyboard to white keys of middle octave)
        base_note = 12 * self.start_octave  # Start from current octave
        
        default_mappings = {
            'a': base_note + 0,   # C
            's': base_note + 2,   # D
            'd': base_note + 4,   # E
            'f': base_note + 5,   # F
            'g': base_note + 7,   # G
            'h': base_note + 9,   # A
            'j': base_note + 11,  # B
            'k': base_note + 12,  # C (next octave)
            
            # Black keys on row above
            'w': base_note + 1,   # C#
            'e': base_note + 3,   # D#
            't': base_note + 6,   # F#
            'y': base_note + 8,   # G#
            'u': base_note + 10   # A#
        }
        
        self.key_mappings = default_mappings
        
        # Bind keyboard events to parent window
        self.parent.bind("<KeyPress>", self.on_key_press)
        self.parent.bind("<KeyRelease>", self.on_key_release_kb)
    
    def on_focus_in(self, event):
        """Handle focus events"""
        self.parent.focus_set()
    
    def on_key_click(self, event):
        """Handle mouse click on piano key"""
        # Find which key was clicked
        overlapping = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        if not overlapping:
            return
            
        # Find the topmost key (black keys are drawn on top)
        key_id = overlapping[-1]
        tags = self.canvas.gettags(key_id)
        
        # Extract note number from tag
        for tag in tags:
            if tag.startswith("key_"):
                note = int(tag.split("_")[1])
                
                # Visual feedback
                if "white_key" in tags:
                    self.canvas.itemconfig(key_id, fill="#87CEEB")  # Light blue
                else:
                    self.canvas.itemconfig(key_id, fill="#4169E1")  # Royal blue
                
                # Determine velocity
                velocity = self.velocity_var.get()
                
                # Play the note
                self.play_note(note, velocity)
                
                # Save for release
                self.clicked_key = key_id
                self.clicked_note = note
                
                break
    
    def on_key_release(self, event):
        """Handle mouse release from piano key"""
        if hasattr(self, "clicked_key") and hasattr(self, "clicked_note"):
            # Visual feedback
            tags = self.canvas.gettags(self.clicked_key)
            if "white_key" in tags:
                self.canvas.itemconfig(self.clicked_key, fill="white")
            else:
                self.canvas.itemconfig(self.clicked_key, fill="black")
            
            # Stop the note (unless sustain is on)
            if not self.sustain_var.get():
                self.stop_note(self.clicked_note)
            
            # Clear references
            del self.clicked_key
            del self.clicked_note
    
    def on_key_drag(self, event):
        """Handle mouse drag over keys"""
        # This allows for gliding over keys
        self.on_key_click(event)
    
    def on_key_press(self, event):
        """Handle computer keyboard key press"""
        key = event.char.lower()
        
        # Regular note playing
        if key in self.key_mappings:
            note = self.key_mappings[key]
            
            # Avoid duplicate note triggers
            if note not in self.pressed_keys:
                self.pressed_keys.add(note)
                self.play_note(note, self.velocity_var.get())
                
                # Visual feedback
                self.highlight_key(note, True)
    
    def on_key_release_kb(self, event):
        """Handle computer keyboard key release"""
        key = event.char.lower()
        
        if key in self.key_mappings:
            note = self.key_mappings[key]
            
            if note in self.pressed_keys:
                self.pressed_keys.remove(note)
                
                # Stop note unless sustain is on
                if not self.sustain_var.get():
                    self.stop_note(note)
                
                # Visual feedback
                self.highlight_key(note, False)
    
    def highlight_key(self, note, is_pressed):
        """Highlight or unhighlight a key for the given note"""
        key_id = self.canvas.find_withtag(f"key_{note}")
        if key_id:
            tags = self.canvas.gettags(key_id[0])
            
            if is_pressed:
                # Highlight
                if "white_key" in tags:
                    self.canvas.itemconfig(key_id, fill="#87CEEB")  # Light blue
                else:
                    self.canvas.itemconfig(key_id, fill="#4169E1")  # Royal blue
            else:
                # Unhighlight
                if "white_key" in tags:
                    self.canvas.itemconfig(key_id, fill="white")
                else:
                    self.canvas.itemconfig(key_id, fill="black")
    
    def play_note(self, note, velocity=100):
        """Play a MIDI note using the synthesizer"""
        try:
            self.synthesizer.note_on(self.channel, note, velocity)
            
            # Record if recording is active
            if self.recording:
                self.record_note_on(note, velocity)
                
        except Exception as e:
            print(f"Error playing note {note}: {e}")
    
    def stop_note(self, note):
        """Stop a MIDI note"""
        try:
            self.synthesizer.note_off(self.channel, note)
            
            # Record if recording is active
            if self.recording:
                self.record_note_off(note)
                
        except Exception as e:
            print(f"Error stopping note {note}: {e}")
    
    def play_chord(self, intervals, chord_name=""):
        """Play a chord using the root note and intervals"""
        # Use middle C as default root if no key is pressed
        root_note = list(self.pressed_keys)[0] if self.pressed_keys else 60
        
        chord_notes = []
        
        # Play all notes in the chord
        for interval in intervals:
            note = root_note + interval
            if 21 <= note <= 108:  # Valid MIDI range
                chord_notes.append(note)
                self.play_note(note, self.velocity_var.get())
                
                # Highlight key
                self.highlight_key(note, True)
        
        # Schedule note-off for all chord notes
        chord_duration = 1000  # 1 second
        for note in chord_notes:
            self.parent.after(chord_duration, lambda n=note: self.stop_chord_note(n))
        
        print(f"Played {chord_name} chord: {chord_notes}")
    
    def stop_chord_note(self, note):
        """Stop a chord note and unhighlight it"""
        if not self.sustain_var.get():
            self.stop_note(note)
        self.highlight_key(note, False)
    
    def toggle_arpeggiator(self):
        """Toggle arpeggiator on/off"""
        if self.arpeggiator_active:
            # Stop arpeggiator
            self.arpeggiator_active = False
            self.arpeggiator_stop_event.set()
            if self.arpeggiator_thread and self.arpeggiator_thread.is_alive():
                self.arpeggiator_thread.join(timeout=1.0)
            self.arp_button.config(text="Arpeggiator Off", bg="#e74c3c")
        else:
            # Start arpeggiator
            if self.pressed_keys:
                self.arpeggiator_active = True
                self.arpeggiator_stop_event.clear()
                self.arpeggiator_thread = threading.Thread(target=self.run_arpeggiator)
                self.arpeggiator_thread.daemon = True
                self.arpeggiator_thread.start()
                self.arp_button.config(text="Arpeggiator On", bg="#27ae60")
    
    def run_arpeggiator(self):
        """Run the arpeggiator in a separate thread"""
        pattern = self.pattern_var.get()
        speed = self.speed_var.get()
        base_notes = sorted(list(self.pressed_keys))
        
        if not base_notes:
            return
        
        # Create arpeggio pattern
        if pattern == "Up":
            arp_notes = base_notes
        elif pattern == "Down":
            arp_notes = list(reversed(base_notes))
        elif pattern == "UpDown":
            arp_notes = base_notes + list(reversed(base_notes[1:-1]))
        elif pattern == "Random":
            arp_notes = base_notes.copy()
        
        note_index = 0
        
        while self.arpeggiator_active and not self.arpeggiator_stop_event.is_set():
            if pattern == "Random":
                note = random.choice(arp_notes)
            else:
                note = arp_notes[note_index % len(arp_notes)]
                note_index += 1
            
            # Play note
            self.play_note(note, self.velocity_var.get())
            
            # Visual feedback
            self.parent.after(0, lambda n=note: self.highlight_key(n, True))
            
            # Wait
            time.sleep(speed)
            
            # Stop note and unhighlight
            if not self.sustain_var.get():
                self.stop_note(note)
            self.parent.after(0, lambda n=note: self.highlight_key(n, False))
    
    def change_instrument(self, event=None):
        """Change the current instrument"""
        self.instrument = self.instrument_var.get()
        # Map instrument names to synthesizer types
        instrument_map = {
            "Acoustic Grand Piano": "piano",
            "Electric Piano": "electric_piano",
            "Harpsichord": "harpsichord",
            "Xylophone": "xylophone",
            "Organ": "organ",
            "Guitar": "guitar",
            "Bass": "bass",
            "Strings": "strings",
            "Choir": "choir",
            "Flute": "flute"
        }
        
        synth_instrument = instrument_map.get(self.instrument, "piano")
        if hasattr(self.synthesizer, 'set_instrument'):
            self.synthesizer.set_instrument(self.channel, synth_instrument)
        
        print(f"Changed instrument to: {self.instrument}")
    
    def increase_octave(self):
        """Increase the keyboard's octave range"""
        if self.start_octave < 7:  # Prevent going too high
            self.start_octave += 1
            self.octave_label.config(text=f"Octave: {self.start_octave}")
            self.setup_key_bindings()  # Update key mappings
            self.draw_keyboard()  # Redraw keyboard
    
    def decrease_octave(self):
        """Decrease the keyboard's octave range"""
        if self.start_octave > 0:  # Prevent going too low
            self.start_octave -= 1
            self.octave_label.config(text=f"Octave: {self.start_octave}")
            self.setup_key_bindings()  # Update key mappings
            self.draw_keyboard()  # Redraw keyboard
    
    def record_toggle(self):
        """Toggle recording on/off"""
        if self.recording:
            # Stop recording
            self.recording = False
            self.record_button.config(text="⚫ Record", bg="#ff6b6b")
            print(f"Recording stopped. Captured {len(self.recorded_notes)} events.")
        else:
            # Start recording
            self.recording = True
            self.recorded_notes = []
            self.record_start_time = time.time()
            self.record_button.config(text="⏺ Recording...", bg="#ff0000")
            print("Recording started...")
    
    def record_note_on(self, note, velocity):
        """Record a note-on event"""
        if self.recording and self.record_start_time:
            timestamp = time.time() - self.record_start_time
            self.recorded_notes.append({
                'type': 'note_on',
                'note': note,
                'velocity': velocity,
                'time': timestamp,
                'channel': self.channel
            })
    
    def record_note_off(self, note):
        """Record a note-off event"""
        if self.recording and self.record_start_time:
            timestamp = time.time() - self.record_start_time
            self.recorded_notes.append({
                'type': 'note_off',
                'note': note,
                'velocity': 0,
                'time': timestamp,
                'channel': self.channel
            })
    
    def export_midi(self):
        """Export recorded notes to MIDI file"""
        if not self.recorded_notes:
            messagebox.showwarning("No Recording", "No recorded notes to export!")
            return
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".mid",
            filetypes=[("MIDI files", "*.mid"), ("All files", "*.*")],
            title="Export Recording as MIDI"
        )
        
        if filename:
            try:
                # Create MIDI file
                mid = mido.MidiFile(ticks_per_beat=480)
                track = mido.MidiTrack()
                mid.tracks.append(track)
                
                # Sort events by time
                events = sorted(self.recorded_notes, key=lambda x: x['time'])
                
                current_time = 0
                for event in events:
                    # Calculate delta time in ticks
                    delta_time = int((event['time'] - current_time) * 480)  # Convert to ticks
                    current_time = event['time']
                    
                    # Create MIDI message
                    if event['type'] == 'note_on':
                        msg = mido.Message('note_on', 
                                         channel=event['channel'],
                                         note=event['note'], 
                                         velocity=event['velocity'],
                                         time=delta_time)
                    else:  # note_off
                        msg = mido.Message('note_off', 
                                         channel=event['channel'],
                                         note=event['note'], 
                                         velocity=0,
                                         time=delta_time)
                    
                    track.append(msg)
                
                # Save file
                mid.save(filename)
                messagebox.showinfo("Export Successful", 
                                  f"Recording exported to {filename}\n"
                                  f"Exported {len(self.recorded_notes)} MIDI events.")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export MIDI file: {e}")
    
    def clear_recording(self):
        """Clear the current recording"""
        self.recorded_notes = []
        self.record_start_time = None
        if self.recording:
            self.record_toggle()  # Stop recording if active
        print("Recording cleared.")
    
    def panic_stop(self):
        """Stop all notes immediately"""
        try:
            # Stop all notes on all channels
            for channel in range(16):
                for note in range(128):
                    self.synthesizer.note_off(channel, note)
            
            # Clear pressed keys
            self.pressed_keys.clear()
            
            # Stop arpeggiator
            if self.arpeggiator_active:
                self.toggle_arpeggiator()
            
            # Reset key highlights
            for key in self.white_keys + self.black_keys:
                note = key['note']
                self.highlight_key(note, False)
            
            print("Panic stop: All notes stopped")
            
        except Exception as e:
            print(f"Error in panic stop: {e}")


class DigitalKeyboardWindow:
    """Standalone window for the digital keyboard"""
    
    def __init__(self, synthesizer=None):
        """Create a standalone digital keyboard window"""
        self.root = tk.Toplevel() if synthesizer else tk.Tk()
        self.root.title("Digital Keyboard")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        
        # Import synthesizer if not provided
        if synthesizer is None:
            try:
                from software_synthesizer import SoftwareSynthesizer
                self.synthesizer = SoftwareSynthesizer()
            except ImportError:
                print("Warning: SoftwareSynthesizer not available. Audio may not work.")
                self.synthesizer = None
        else:
            self.synthesizer = synthesizer
        
        # Create digital keyboard
        if self.synthesizer:
            self.keyboard = DigitalKeyboard(self.root, self.synthesizer)
        else:
            tk.Label(self.root, text="Digital Keyboard\n(Audio synthesizer not available)", 
                    font=("Arial", 16)).pack(expand=True)
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def on_close(self):
        """Handle window close event"""
        if hasattr(self, 'keyboard') and self.keyboard.arpeggiator_active:
            self.keyboard.toggle_arpeggiator()  # Stop arpeggiator
        
        if hasattr(self, 'keyboard'):
            self.keyboard.panic_stop()  # Stop all notes
        
        self.root.destroy()
    
    def run(self):
        """Run the standalone keyboard application"""
        if not hasattr(self.root, 'master') or self.root.master is None:
            self.root.mainloop()


if __name__ == "__main__":
    # Run as standalone application
    print("🎹 Starting Digital Keyboard...")
    app = DigitalKeyboardWindow()
    app.run()
