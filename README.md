# Ultimate MIDI Generator - The Fun Tool 🎵

A comprehensive Python-based MIDI music generator with full emulation, real-time visualization, and 50+ customizable settings. Create amazing music with advanced randomization features!

## Features

### 🎼 Music Generation
- **Smart Melody Generation**: AI-driven melody creation with direction bias, interval preferences, and musical logic
- **Harmony Engine**: Multiple chord progression styles (Pop, Jazz, Classical, Blues, Rock)
- **Rhythm Patterns**: Swing, syncopation, triplets, dotted notes, and complex rhythmic variations
- **Bass Lines**: Root, walking, and alternating bass patterns
- **Drum Patterns**: Automatic drum track generation with kick, snare, and hi-hat

### 🎛️ 50+ Settings & Controls

#### Basic Settings (8 controls)
- Tempo (60-200 BPM)
- Key Signature (12 keys)
- Scale Type (Major, Minor, Dorian, Phrygian, Lydian, Mixolydian, Locrian, Blues, Pentatonic, Chromatic)
- Note Range (Low/High)
- Song Length (8-128 bars)
- Time Signature
- Lead/Bass/Drum/Pad Instruments

#### Rhythm Controls (10 controls)
- Swing Factor
- Syncopation Probability
- Rest Probability
- Triplet Probability
- Dotted Note Probability
- Note Length Range
- Accent Probability
- Ghost Note Probability
- Rhythmic Complexity
- Polyrhythm Settings

#### Harmony Controls (8 controls)
- Chord Progression Style
- Chord Complexity (Triads to Extended Chords)
- Bass Line Style
- Voice Leading
- Parallel Motion Avoidance
- Harmonic Rhythm
- Modal Interchange
- Secondary Dominants

#### Melody Controls (10 controls)
- Direction Bias
- Interval Preferences
- Leap Probability
- Repetition Factor
- Sequence Probability
- Motivic Development
- Phrase Structure
- Melodic Contour
- Range Constraints
- Note Duration Variety

#### Effects & Dynamics (8 controls)
- Velocity Range (Min/Max)
- Dynamic Range
- Crescendo/Diminuendo Probability
- Accent Patterns
- Ghost Notes
- Velocity Curves
- Expression Mapping
- Articulation Styles

#### Randomization (6+ controls)
- Chaos Factor (Global randomness)
- Mutation Rate (Genetic algorithm)
- Evolution Steps
- Random Seed Control
- Selective Randomization Buttons
- Probability Distributions

### 🎨 Advanced Visualization & Audio
- **Piano Roll Display**: Real-time MIDI note visualization
- **Color-Coded Tracks**: Different colors for melody, bass, drums
- **Animated Playback**: Visual playback with timeline cursor
- **Velocity Visualization**: Note intensity shown through transparency
- **Multi-Channel Display**: Separate visualization for each instrument
- **🎵 Built-in Software Synthesizer**: No external MIDI hardware needed!
  - Real-time audio synthesis
  - Multiple instrument sounds (Piano, Bass, Drums, Sine, Square, Sawtooth, Triangle)
  - Stereo output at 44.1kHz
  - Instant playback of generated music

### 🎲 Randomization Features
- **Smart Randomization**: Musically-aware random generation
- **Selective Randomizers**: Random buttons for specific aspects
- **Chaos Mode**: Add controlled randomness to any generation
- **Genetic Evolution**: Evolve musical ideas over generations
- **Mutation Engine**: Subtle variations on existing patterns

## Installation

### Option 1: Easy Setup (Recommended for Windows)
1. **Download/clone** this repository
2. **Double-click** `install_dependencies.bat` to automatically install all packages
3. **Double-click** `launch.bat` to start the application

### Option 2: Virtual Environment Setup (Advanced)
1. **Download/clone** this repository
2. **Double-click** `setup_venv.bat` to create a virtual environment and install packages
3. **Double-click** `launch_venv.bat` to start with virtual environment

### Option 3: Manual Installation
1. **Clone or download** this repository
2. **Install dependencies**:
```bash
pip install -r requirements.txt
```
3. **Run the application**:
```bash
python MIDI.PY
```

### Troubleshooting
- **Test your setup**: Run `test_dependencies.bat` to check if everything is installed correctly
- **Python not found**: Make sure Python 3.7+ is installed from [python.org](https://python.org)
- **Permission errors**: Try running batch files as administrator

## Batch Files (Windows Users)

For Windows users, several convenient batch files are provided:

- **`install_dependencies.bat`** - Automatically installs all required Python packages
- **`setup_venv.bat`** - Creates a virtual environment and installs packages (recommended)
- **`launch.bat`** - Starts the MIDI generator (system Python)
- **`launch_venv.bat`** - Starts the MIDI generator (virtual environment)
- **`test_dependencies.bat`** - Tests if all packages are installed correctly

Simply double-click any of these files to run them!

1. **Launch the app** - Run `python MIDI.PY`
2. **Adjust settings** - Use the tabbed interface to customize your music
3. **Generate music** - Click "Generate Music"
4. **Visualize** - Watch the piano roll visualization update
5. **Play** - Click "Play" to hear your creation (requires MIDI synthesizer)
6. **Save** - Export as MIDI file or save your settings

## Interface Overview

### Control Tabs
- **Basic**: Fundamental settings (tempo, key, scale, song length)
- **Rhythm**: Timing, swing, syncopation, note durations
- **Harmony**: Chord progressions, bass lines, harmonic complexity
- **Melody**: Melodic direction, intervals, phrasing
- **Effects**: Velocity, dynamics, accents, expression
- **Random**: Chaos controls and selective randomization
- **🎵 Synthesizer**: Built-in audio engine with instrument selection

### Quick Actions
- **Generate Music**: Create new composition with current settings
- **Play**: Start playback with built-in synthesizer and visual animation
- **Stop**: Stop playback and animation
- **Save MIDI**: Export as standard MIDI file
- **Load/Save Settings**: Preserve your favorite configurations
- **Randomize All**: Instantly randomize all parameters
- **Test Sounds**: Quick instrument tests in the Synthesizer tab

## Advanced Features

### Musical Intelligence
- **Scale Awareness**: All notes generated within selected scale/key
- **Voice Leading**: Smooth transitions between chords
- **Phrase Structure**: Logical musical phrases and sentences
- **Stylistic Consistency**: Maintains chosen musical style throughout

### Randomization Options
- **Controlled Chaos**: Add randomness while maintaining musicality
- **Evolutionary Generation**: Breed musical ideas over time
- **Selective Randomization**: Randomize only specific aspects
- **Probability-Based**: Use statistical models for natural variation

### Visualization Features
- **Real-Time Updates**: Visualization updates as you generate
- **Multi-Track Display**: See all instruments simultaneously
- **Color Coding**: Easy identification of different parts
- **Playback Animation**: Follow along with visual playback cursor

## Tips for Best Results

1. **Start Simple**: Begin with basic settings, then add complexity
2. **Use Presets**: Save settings combinations you like
3. **Experiment**: Try the random buttons for inspiration
4. **Layer Gradually**: Build complexity by adjusting one category at a time
5. **Study Output**: Use the visualization to understand what each setting does

## Technical Requirements

- **Python 3.7+**
- **Libraries**: mido, pygame, matplotlib, numpy, tkinter
- **Optional**: MIDI synthesizer for audio playback
- **System**: Windows/Mac/Linux compatible

## MIDI Output & Audio

### Built-in Software Synthesizer 🎵
**No external hardware needed!** The generator includes a complete software synthesizer:

- **Real-time Audio**: Instant playback of your generated music
- **Multiple Instruments**: Piano, Bass, Drums, Sine, Square, Sawtooth, Triangle waves
- **High Quality**: 44.1kHz stereo output with ADSR envelopes
- **Customizable**: Select different instruments for each channel
- **Test Sounds**: Quick buttons to test each instrument

### MIDI File Compatibility
The generated MIDI files are standard format and compatible with:
- Digital Audio Workstations (DAWs)
- MIDI synthesizers and keyboards
- Music notation software
- Online MIDI players
- Hardware MIDI devices

## Troubleshooting

**No Audio?** 
- The built-in synthesizer should work automatically
- Check your system volume and audio output
- Try the test buttons in the Synthesizer tab
- Make sure no other applications are blocking audio

**Performance Issues?**
- Reduce song length for faster generation
- Lower the chaos factor for smoother playback
- Close other audio applications

**Generation Errors?**
- Check that all settings are within valid ranges
- Try resetting to default settings
- Ensure adequate system resources

## Contributing

This is an open-source project! Feel free to:
- Add new musical styles
- Improve the visualization
- Enhance the randomization algorithms
- Add new instruments or effects
- Report bugs or suggest features

## License

Open source - feel free to use, modify, and distribute!

---

**Have fun creating music!** 🎵🎹🎸🥁

This tool is designed to be both powerful for serious music creation and fun for experimentation. Whether you're a professional composer or just love making music, the Ultimate MIDI Generator has something for everyone!
