"""
Advanced MP3 to MIDI Converter
Supports multiple conversion algorithms for optimal results
"""

import numpy as np
import librosa
import mido
from scipy.signal import find_peaks
from scipy.ndimage import median_filter, gaussian_filter
import os
import threading
import random
import glob
from typing import List, Tuple, Optional, Callable

class MP3ToMIDIConverter:
    """Advanced MP3 to MIDI converter with multiple algorithms"""
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback
        self.sample_rate = 22050
        self.hop_length = 512
        self.frame_length = 2048
        
        # Advanced settings with defaults
        self.sensitivity = 0.5
        self.min_duration = 0.05
        self.max_polyphony = 3  # Maximum simultaneous notes
        self.note_smoothing = True
        self.tempo_tracking = True
        
        # Note frequency mapping (MIDI notes 21-108 covering piano range)
        self.midi_frequencies = {}
        for midi_note in range(21, 109):
            freq = 440.0 * (2.0 ** ((midi_note - 69) / 12.0))
            self.midi_frequencies[midi_note] = freq
        
        print("✅ Advanced MP3 to MIDI Converter initialized")
    
    def _update_progress(self, progress: float, message: str = ""):
        """Update progress if callback is provided"""
        if self.progress_callback:
            self.progress_callback(progress, message)
    
    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Load audio file and return audio data and sample rate"""
        try:
            self._update_progress(0.1, "Loading audio file...")
            
            # Load with librosa
            y, sr = librosa.load(file_path, sr=self.sample_rate, mono=True)
            
            # Normalize audio
            y = librosa.util.normalize(y)
            
            self._update_progress(0.2, f"Audio loaded: {len(y)/sr:.1f}s duration")
            return y, sr
            
        except Exception as e:
            raise Exception(f"Failed to load audio file: {str(e)}")
    
    def extract_pitch_chroma(self, y: np.ndarray, sr: int) -> Tuple[np.ndarray, np.ndarray]:
        """Extract pitch using chroma features (good for harmonic content)"""
        self._update_progress(0.3, "Extracting chroma features...")
        
        # Extract chroma features
        chroma = librosa.feature.chroma_stft(
            y=y, sr=sr, 
            hop_length=self.hop_length,
            n_fft=self.frame_length
        )
        
        # Get time frames
        times = librosa.frames_to_time(
            np.arange(chroma.shape[1]), 
            sr=sr, 
            hop_length=self.hop_length
        )
        
        return chroma, times
    
    def extract_pitch_cqt(self, y: np.ndarray, sr: int) -> Tuple[np.ndarray, np.ndarray]:
        """Enhanced CQT extraction with better parameters for pitch detection"""
        self._update_progress(0.3, "Extracting enhanced CQT features...")
        
        # Preprocess audio for better results
        y_processed = self.preprocess_audio(y, sr)
        
        # Use enhanced CQT with better parameters
        cqt = np.abs(librosa.cqt(
            y=y_processed, sr=sr,
            hop_length=self.hop_length // 2,  # Better time resolution
            fmin=librosa.note_to_hz('C2'),    # Start from C2 (65.4 Hz)
            n_bins=96,                        # 8 octaves for better range
            bins_per_octave=12,
            filter_scale=1,                   # Better frequency resolution
            sparsity=0.01                     # Reduce noise
        ))
        
        # Apply spectral normalization for consistent analysis
        cqt_norm = librosa.util.normalize(cqt, axis=0)
        
        # Apply temporal smoothing to reduce noise
        cqt_smooth = gaussian_filter(cqt_norm, sigma=(0.5, 1.0))
        
        # Get time frames with higher resolution
        times = librosa.frames_to_time(
            np.arange(cqt_smooth.shape[1]), 
            sr=sr, 
            hop_length=self.hop_length // 2
        )
        
        return cqt_smooth, times
    
    def extract_pitch_onset(self, y: np.ndarray, sr: int) -> Tuple[List[float], List[float]]:
        """Extract pitch using onset detection and pitch tracking"""
        self._update_progress(0.3, "Detecting onsets and pitch...")
        
        # Detect note onsets
        onset_frames = librosa.onset.onset_detect(
            y=y, sr=sr,
            hop_length=self.hop_length,
            units='time'
        )
        
        # Extract fundamental frequencies
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y, fmin=librosa.note_to_hz('C2'), 
            fmax=librosa.note_to_hz('C7'),
            sr=sr,
            hop_length=self.hop_length
        )
        
        # Get time frames for f0
        f0_times = librosa.frames_to_time(
            np.arange(len(f0)), 
            sr=sr, 
            hop_length=self.hop_length
        )
        
        return onset_frames, f0_times, f0, voiced_flag
    
    def chroma_to_midi_notes(self, chroma: np.ndarray, times: np.ndarray, 
                           min_duration: float = 0.1, velocity_range: Tuple[int, int] = (60, 100)) -> List[dict]:
        """Enhanced chroma to MIDI conversion with adaptive thresholding"""
        self._update_progress(0.5, "Converting chroma to MIDI notes with advanced processing...")
        
        notes = []
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Apply temporal smoothing to reduce noise
        chroma_smooth = gaussian_filter(chroma, sigma=(0.5, 1.0))
        
        # Adaptive threshold based on signal characteristics
        global_max = np.max(chroma_smooth)
        mean_energy = np.mean(chroma_smooth)
        
        # Adjust sensitivity based on user setting
        base_threshold = 0.01 + (1 - self.sensitivity) * 0.05
        adaptive_threshold = max(base_threshold, mean_energy * 0.3)
        
        # Process each time frame
        for i, time in enumerate(times[:-1]):
            frame_chroma = chroma_smooth[:, i]
            duration = times[i+1] - time
            
            if duration < self.min_duration:
                continue
            
            # Dynamic threshold for this frame
            max_chroma = np.max(frame_chroma)
            if max_chroma > adaptive_threshold:
                # Find peaks with adaptive height
                peaks, properties = find_peaks(
                    frame_chroma, 
                    height=max_chroma * (0.1 + self.sensitivity * 0.3),
                    distance=1
                )
                
                # Limit polyphony
                if len(peaks) > self.max_polyphony:
                    # Keep only the strongest peaks
                    peak_heights = frame_chroma[peaks]
                    top_indices = np.argsort(peak_heights)[-self.max_polyphony:]
                    peaks = peaks[top_indices]
                
                for note_class in peaks:
                    # Smart octave selection based on spectral centroid
                    best_octave = 4  # Default
                    if max_chroma > 0.3:  # Strong signal
                        best_octave = 5 if note_class < 6 else 4  # Higher for lower notes
                    elif max_chroma < 0.1:  # Weak signal
                        best_octave = 3  # Lower octave for weak signals
                    
                    base_midi = 12 + note_class + (best_octave * 12)
                    
                    if 21 <= base_midi <= 108:  # Valid piano range
                        # Enhanced velocity calculation
                        relative_strength = frame_chroma[note_class] / max_chroma
                        velocity = int(velocity_range[0] + 
                                      (velocity_range[1] - velocity_range[0]) * 
                                      relative_strength)
                        
                        notes.append({
                            'note': base_midi,
                            'start': time,
                            'duration': duration,
                            'velocity': max(20, min(127, velocity)),
                            'channel': 0,
                            'confidence': relative_strength
                        })
        
        return notes
    
    def cqt_to_midi_notes(self, cqt: np.ndarray, times: np.ndarray,
                         min_duration: float = 0.1, velocity_range: Tuple[int, int] = (60, 100)) -> List[dict]:
        """Convert CQT features to MIDI notes with better pitch accuracy"""
        self._update_progress(0.5, "Converting CQT to MIDI notes...")
        
        notes = []
        
        # Apply median filter to reduce noise
        cqt_filtered = median_filter(cqt, size=(1, 3))
        
        # Process each time frame
        for i, time in enumerate(times[:-1]):
            frame_cqt = cqt_filtered[:, i]
            duration = times[i+1] - time
            
            if duration < min_duration:
                continue
            
            max_cqt = np.max(frame_cqt)
            if max_cqt > 0.001:  # Very low threshold
                # Find peaks in the CQT
                peaks, properties = find_peaks(
                    frame_cqt, 
                    height=max_cqt * 0.1,  # Lower threshold
                    distance=1  # Allow closer peaks
                )
                
                for peak in peaks:
                    # Convert CQT bin to MIDI note
                    # CQT starts at C1 (MIDI 24) with 12 bins per octave
                    midi_note = 24 + peak
                    
                    if 21 <= midi_note <= 108:  # Valid piano range
                        # Calculate velocity based on peak height
                        velocity = int(velocity_range[0] + 
                                      (velocity_range[1] - velocity_range[0]) * 
                                      (frame_cqt[peak] / max_cqt))
                        
                        notes.append({
                            'note': midi_note,
                            'start': time,
                            'duration': duration,
                            'velocity': max(30, min(127, velocity)),
                            'channel': 0
                        })
        
        return notes
    
    def onset_to_midi_notes(self, onset_times: List[float], f0_times: np.ndarray, 
                           f0: np.ndarray, voiced_flag: np.ndarray,
                           velocity_range: Tuple[int, int] = (60, 100)) -> List[dict]:
        """Enhanced onset-based conversion with better pitch tracking and adaptive parameters"""
        self._update_progress(0.5, "Converting onset/pitch data to MIDI notes with advanced processing...")
        
        notes = []
        
        # Filter out weak onsets based on sensitivity
        if hasattr(self, 'y') and hasattr(self, 'sr'):
            # Calculate onset strengths for filtering
            onset_envelope = librosa.onset.onset_strength(y=self.y, sr=self.sr)
            onset_frames = librosa.onset.onset_detect(onset_envelope=onset_envelope, sr=self.sr, units='frames')
            onset_strengths = onset_envelope[onset_frames] if len(onset_frames) > 0 else []
            
            # Adaptive threshold based on sensitivity
            if len(onset_strengths) > 0:
                strength_threshold = np.percentile(onset_strengths, (1 - self.sensitivity) * 80)
                filtered_onsets = []
                for i, strength in enumerate(onset_strengths):
                    if strength >= strength_threshold and i < len(onset_times):
                        filtered_onsets.append(onset_times[i])
                onset_times = filtered_onsets[:len(onset_times)]  # Safety check
        
        for i, onset_time in enumerate(onset_times[:-1]):
            # Smart duration calculation
            next_onset = onset_times[i+1] if i+1 < len(onset_times) else onset_time + 1.0
            duration = min(next_onset - onset_time, 2.0)  # Cap at 2 seconds
            
            # Skip very short notes unless high sensitivity
            if duration < self.min_duration:
                continue
            
            # Find f0 values around this onset with larger window for better accuracy
            onset_idx = np.argmin(np.abs(f0_times - onset_time))
            
            # Adaptive window size based on note duration
            window_size = max(3, int(duration * 10))  # Larger window for longer notes
            start_idx = max(0, onset_idx - window_size//2)
            end_idx = min(len(f0), onset_idx + window_size//2)
            
            # Get f0 values in this window that are voiced
            window_f0 = f0[start_idx:end_idx]
            window_voiced = voiced_flag[start_idx:end_idx]
            
            valid_f0 = window_f0[window_voiced]
            
            if len(valid_f0) > 0:
                # Use median f0 for stability, but consider confidence
                median_f0 = np.median(valid_f0)
                f0_std = np.std(valid_f0)
                confidence = 1.0 / (1.0 + f0_std)  # Higher confidence for stable pitch
                
                # Convert frequency to MIDI note
                if median_f0 > 0:
                    midi_note = round(69 + 12 * np.log2(median_f0 / 440.0))
                    
                    if 21 <= midi_note <= 108:  # Valid range
                        # Enhanced velocity calculation based on confidence and onset strength
                        base_velocity = random.randint(*velocity_range)
                        velocity = int(base_velocity * confidence)
                        velocity = max(20, min(127, velocity))
                        
                        notes.append({
                            'note': midi_note,
                            'start': onset_time,
                            'duration': duration,
                            'velocity': velocity,
                            'channel': 0,
                            'confidence': confidence
                        })
        
        return notes
    
    def post_process_notes(self, notes: List[dict]) -> List[dict]:
        """Post-process notes to remove overlaps and improve timing"""
        self._update_progress(0.7, "Post-processing notes...")
        
        if not notes:
            return notes
        
        # Sort notes by start time
        notes.sort(key=lambda n: n['start'])
        
        processed_notes = []
        
        for i, note in enumerate(notes):
            # Skip very short notes (reduced threshold)
            if note['duration'] < 0.02:  # 20ms minimum instead of 50ms
                continue
            
            # Check for overlapping notes of the same pitch (more permissive)
            overlapping = False
            for prev_note in processed_notes:
                if (prev_note['note'] == note['note'] and 
                    abs(prev_note['start'] - note['start']) < 0.1):  # Within 100ms
                    overlapping = True
                    break
            
            if not overlapping:
                processed_notes.append(note)
        
        self._update_progress(0.8, f"Processed {len(processed_notes)} notes")
        return processed_notes
    
    def create_midi_file(self, notes: List[dict], tempo: int = 120) -> mido.MidiFile:
        """Create a MIDI file from note data"""
        self._update_progress(0.9, "Creating MIDI file...")
        
        mid = mido.MidiFile(ticks_per_beat=480)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        # Add tempo
        track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo), time=0))
        
        # Sort notes by start time
        notes.sort(key=lambda n: n['start'])
        
        # Convert to MIDI messages
        events = []
        
        for note in notes:
            start_ticks = int(note['start'] * 480)  # Convert to ticks
            duration_ticks = int(note['duration'] * 480)
            
            # Note on event
            events.append({
                'time': start_ticks,
                'type': 'note_on',
                'note': note['note'],
                'velocity': note['velocity'],
                'channel': note.get('channel', 0)
            })
            
            # Note off event
            events.append({
                'time': start_ticks + duration_ticks,
                'type': 'note_off',
                'note': note['note'],
                'velocity': 0,
                'channel': note.get('channel', 0)
            })
        
        # Sort events by time
        events.sort(key=lambda e: e['time'])
        
        # Add events to track with proper delta times
        current_time = 0
        for event in events:
            delta_time = event['time'] - current_time
            
            if event['type'] == 'note_on':
                track.append(mido.Message('note_on', 
                                        channel=event['channel'],
                                        note=event['note'], 
                                        velocity=event['velocity'],
                                        time=delta_time))
            else:  # note_off
                track.append(mido.Message('note_off', 
                                        channel=event['channel'],
                                        note=event['note'], 
                                        velocity=0,
                                        time=delta_time))
            
            current_time = event['time']
        
        return mid
    
    def convert_mp3_to_midi(self, mp3_path: str, output_path: str, 
                           algorithm: str = 'cqt', tempo: int = 120) -> bool:
        """
        Convert MP3 to MIDI using specified algorithm
        
        Args:
            mp3_path: Path to input MP3 file
            output_path: Path for output MIDI file
            algorithm: 'chroma', 'cqt', or 'onset' 
            tempo: Tempo for output MIDI file
        """
        try:
            self._update_progress(0.0, f"Starting conversion using {algorithm} algorithm...")
            
            # Load audio
            y, sr = self.load_audio(mp3_path)
            
            # Choose algorithm
            if algorithm == 'chroma':
                chroma, times = self.extract_pitch_chroma(y, sr)
                notes = self.chroma_to_midi_notes(chroma, times)
                
            elif algorithm == 'cqt':
                cqt, times = self.extract_pitch_cqt(y, sr)
                notes = self.cqt_to_midi_notes(cqt, times)
                
            elif algorithm == 'onset':
                onset_times, f0_times, f0, voiced_flag = self.extract_pitch_onset(y, sr)
                notes = self.onset_to_midi_notes(onset_times, f0_times, f0, voiced_flag)
                
            else:
                raise ValueError(f"Unknown algorithm: {algorithm}")
            
            # Post-process notes
            notes = self.post_process_notes(notes)
            
            if not notes:
                raise Exception("No notes detected in audio file")
            
            # Create MIDI file
            midi_file = self.create_midi_file(notes, tempo)
            
            # Save MIDI file
            midi_file.save(output_path)
            
            self._update_progress(1.0, f"Conversion complete! Generated {len(notes)} notes")
            return True
            
        except Exception as e:
            self._update_progress(1.0, f"Conversion failed: {str(e)}")
            return False
    
    def convert_with_all_algorithms(self, mp3_path: str, output_dir: str, 
                                   tempo: int = 120) -> dict:
        """Convert using all algorithms and return results"""
        results = {}
        algorithms = ['chroma', 'cqt', 'onset']
        
        for algorithm in algorithms:
            try:
                output_file = os.path.join(output_dir, f"converted_{algorithm}.mid")
                success = self.convert_mp3_to_midi(mp3_path, output_file, algorithm, tempo)
                results[algorithm] = {
                    'success': success,
                    'output_file': output_file if success else None
                }
            except Exception as e:
                results[algorithm] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    def analyze_audio_characteristics(self, y: np.ndarray, sr: int) -> dict:
        """Analyze audio to suggest best conversion algorithm and settings"""
        self._update_progress(0.15, "Analyzing audio characteristics...")
        
        # Spectral analysis
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        
        # Tempo and beat analysis
        try:
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        except:
            tempo = 120  # Default if detection fails
            
        # Harmonic/percussive separation
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        harmonic_ratio = np.mean(np.abs(y_harmonic)) / (np.mean(np.abs(y)) + 1e-10)
        
        # Onset detection for rhythmic analysis
        onset_envelope = librosa.onset.onset_strength(y=y, sr=sr)
        onset_times = librosa.onset.onset_detect(onset_envelope=onset_envelope, sr=sr, units='time')
        
        # Spectral features
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_var = np.var(chroma, axis=1)
        
        # Analysis results
        analysis = {
            'tempo': float(tempo),
            'avg_spectral_centroid': float(np.mean(spectral_centroids)),
            'avg_spectral_bandwidth': float(np.mean(spectral_bandwidth)),
            'avg_zero_crossing': float(np.mean(zero_crossing_rate)),
            'harmonic_ratio': float(harmonic_ratio),
            'percussive_ratio': 1.0 - float(harmonic_ratio),
            'onset_density': len(onset_times) / (len(y) / sr),  # onsets per second
            'chroma_complexity': float(np.mean(chroma_var)),
            'dynamic_range': float(np.std(librosa.amplitude_to_db(np.abs(y)))),
            'duration': len(y) / sr
        }
        
        # Algorithm recommendation based on analysis
        if analysis['harmonic_ratio'] > 0.7 and analysis['chroma_complexity'] < 0.1:
            analysis['recommended_algorithm'] = 'cqt'
            analysis['reason'] = 'High harmonic content with simple harmony - excellent for melodies'
            analysis['recommended_sensitivity'] = 0.3
        elif analysis['percussive_ratio'] > 0.6 or analysis['onset_density'] > 3:
            analysis['recommended_algorithm'] = 'onset'
            analysis['reason'] = 'High percussive content or dense onsets - perfect for rhythm'
            analysis['recommended_sensitivity'] = 0.7
        elif analysis['chroma_complexity'] > 0.15:
            analysis['recommended_algorithm'] = 'chroma'
            analysis['reason'] = 'Complex harmonic content - good for chord progressions'
            analysis['recommended_sensitivity'] = 0.4
        else:
            analysis['recommended_algorithm'] = 'cqt'
            analysis['reason'] = 'Mixed content - CQT provides good balance'
            analysis['recommended_sensitivity'] = 0.5
        
        # Suggest optimal parameters
        if analysis['duration'] > 60:  # Long audio
            analysis['suggested_min_duration'] = 0.1
        else:
            analysis['suggested_min_duration'] = 0.05
            
        return analysis
    
    def preprocess_audio(self, y: np.ndarray, sr: int) -> np.ndarray:
        """Advanced audio preprocessing for better conversion results"""
        self._update_progress(0.25, "Preprocessing audio...")
        
        # Normalize audio
        y = librosa.util.normalize(y)
        
        # Remove silence from beginning and end
        y_trimmed, _ = librosa.effects.trim(y, top_db=20)
        
        # Apply gentle high-pass filter to remove rumble
        y_filtered = librosa.effects.preemphasis(y_trimmed)
        
        # Harmonic-percussive separation for cleaner analysis
        y_harmonic, y_percussive = librosa.effects.hpss(y_filtered)
        
        # Combine with emphasis on harmonic content for pitch detection
        y_processed = 0.8 * y_harmonic + 0.2 * y_percussive
        
        return y_processed

    def auto_select_algorithm(self, y: np.ndarray, sr: int) -> str:
        """Automatically select the best algorithm based on audio analysis"""
        analysis = self.analyze_audio_characteristics(y, sr)
        return analysis['recommended_algorithm']
    
    def convert_with_auto_algorithm(self, mp3_path: str, output_path: str, tempo: int = 120) -> dict:
        """Convert using automatically selected algorithm"""
        try:
            # Load and analyze audio
            y, sr = self.load_audio(mp3_path)
            
            # Store for use in onset detection
            self.y = y
            self.sr = sr
            
            # Get analysis and recommended algorithm
            analysis = self.analyze_audio_characteristics(y, sr)
            recommended_algo = analysis['recommended_algorithm']
            
            # Update settings based on analysis
            self.sensitivity = analysis.get('recommended_sensitivity', 0.5)
            self.min_duration = analysis.get('suggested_min_duration', 0.05)
            
            # Convert using recommended algorithm
            success = self.convert_mp3_to_midi(mp3_path, output_path, recommended_algo, tempo)
            
            return {
                'success': success,
                'algorithm_used': recommended_algo,
                'analysis': analysis,
                'output_file': output_path if success else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'algorithm_used': None,
                'analysis': None
            }
    
    def batch_convert(self, input_files: List[str], output_dir: str, 
                     algorithm: str = 'auto', tempo: int = 120) -> dict:
        """Convert multiple files in batch"""
        results = {}
        total_files = len(input_files)
        
        for i, input_file in enumerate(input_files):
            self._update_progress(i / total_files, f"Processing {os.path.basename(input_file)}...")
            
            try:
                # Generate output filename
                base_name = os.path.splitext(os.path.basename(input_file))[0]
                output_file = os.path.join(output_dir, f"{base_name}_converted.mid")
                
                if algorithm == 'auto':
                    # Use auto-selection
                    result = self.convert_with_auto_algorithm(input_file, output_file, tempo)
                else:
                    # Use specified algorithm
                    success = self.convert_mp3_to_midi(input_file, output_file, algorithm, tempo)
                    result = {
                        'success': success,
                        'algorithm_used': algorithm,
                        'output_file': output_file if success else None
                    }
                
                results[input_file] = result
                
            except Exception as e:
                results[input_file] = {
                    'success': False,
                    'error': str(e)
                }
        
        self._update_progress(1.0, f"Batch conversion complete: {len(input_files)} files processed")
        return results
    
    def preview_conversion(self, mp3_path: str, algorithm: str = 'auto', 
                          preview_duration: float = 10.0) -> dict:
        """Generate a preview of the conversion (first N seconds)"""
        try:
            # Load full audio
            y, sr = self.load_audio(mp3_path)
            
            # Trim to preview duration
            preview_samples = int(preview_duration * sr)
            y_preview = y[:preview_samples] if len(y) > preview_samples else y
            
            # Store for onset detection
            self.y = y_preview
            self.sr = sr
            
            # Select algorithm
            if algorithm == 'auto':
                analysis = self.analyze_audio_characteristics(y_preview, sr)
                selected_algorithm = analysis['recommended_algorithm']
                self.sensitivity = analysis.get('recommended_sensitivity', 0.5)
            else:
                selected_algorithm = algorithm
                analysis = None
            
            # Convert preview
            if selected_algorithm == 'chroma':
                chroma, times = self.extract_pitch_chroma(y_preview, sr)
                notes = self.chroma_to_midi_notes(chroma, times)
            elif selected_algorithm == 'cqt':
                cqt, times = self.extract_pitch_cqt(y_preview, sr)
                notes = self.cqt_to_midi_notes(cqt, times)
            elif selected_algorithm == 'onset':
                onset_times, f0_times, f0, voiced_flag = self.extract_pitch_onset(y_preview, sr)
                notes = self.onset_to_midi_notes(onset_times, f0_times, f0, voiced_flag)
            
            # Post-process
            notes = self.post_process_notes(notes)
            
            return {
                'success': True,
                'notes': notes,
                'algorithm_used': selected_algorithm,
                'preview_duration': len(y_preview) / sr,
                'estimated_full_notes': int(len(notes) * (len(y) / len(y_preview))),
                'analysis': analysis
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_conversion_quality_score(self, notes: List[dict]) -> dict:
        """Analyze the quality of converted notes"""
        if not notes:
            return {'score': 0, 'issues': ['No notes detected']}
        
        issues = []
        score = 100
        
        # Check note density (notes per second)
        if len(notes) > 0:
            total_duration = max(note['start'] + note['duration'] for note in notes)
            notes_per_second = len(notes) / total_duration
            
            if notes_per_second > 10:
                issues.append('Very high note density - may be noisy')
                score -= 20
            elif notes_per_second < 0.5:
                issues.append('Low note density - may have missed notes')
                score -= 10
        
        # Check for very short notes
        short_notes = [n for n in notes if n['duration'] < 0.05]
        if len(short_notes) > len(notes) * 0.3:
            issues.append('Many very short notes detected')
            score -= 15
        
        # Check velocity distribution
        velocities = [n['velocity'] for n in notes]
        if len(set(velocities)) < 3:
            issues.append('Limited velocity variation')
            score -= 10
        
        # Check pitch range
        pitches = [n['note'] for n in notes]
        pitch_range = max(pitches) - min(pitches)
        if pitch_range < 12:  # Less than one octave
            issues.append('Limited pitch range')
            score -= 10
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }

    def auto_select_algorithm(self, y: np.ndarray, sr: int) -> str:
        """Automatically select the best algorithm based on audio analysis"""
        analysis = self.analyze_audio_characteristics(y, sr)
        return analysis['recommended_algorithm']
    
    def convert_with_auto_algorithm(self, mp3_path: str, output_path: str, tempo: int = 120) -> dict:
        """Convert using automatically selected algorithm"""
        try:
            # Load and analyze audio
            y, sr = self.load_audio(mp3_path)
            
            # Store for use in onset detection
            self.y = y
            self.sr = sr
            
            # Get analysis and recommended algorithm
            analysis = self.analyze_audio_characteristics(y, sr)
            recommended_algo = analysis['recommended_algorithm']
            
            # Update settings based on analysis
            self.sensitivity = analysis.get('recommended_sensitivity', 0.5)
            self.min_duration = analysis.get('suggested_min_duration', 0.05)
            
            # Convert using recommended algorithm
            success = self.convert_mp3_to_midi(mp3_path, output_path, recommended_algo, tempo)
            
            return {
                'success': success,
                'algorithm_used': recommended_algo,
                'analysis': analysis,
                'output_file': output_path if success else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'algorithm_used': None,
                'analysis': None
            }
    
    def batch_convert(self, input_files: List[str], output_dir: str, 
                     algorithm: str = 'auto', tempo: int = 120) -> dict:
        """Convert multiple files in batch"""
        results = {}
        total_files = len(input_files)
        
        for i, input_file in enumerate(input_files):
            self._update_progress(i / total_files, f"Processing {os.path.basename(input_file)}...")
            
            try:
                # Generate output filename
                base_name = os.path.splitext(os.path.basename(input_file))[0]
                output_file = os.path.join(output_dir, f"{base_name}_converted.mid")
                
                if algorithm == 'auto':
                    # Use auto-selection
                    result = self.convert_with_auto_algorithm(input_file, output_file, tempo)
                else:
                    # Use specified algorithm
                    success = self.convert_mp3_to_midi(input_file, output_file, algorithm, tempo)
                    result = {
                        'success': success,
                        'algorithm_used': algorithm,
                        'output_file': output_file if success else None
                    }
                
                results[input_file] = result
                
            except Exception as e:
                results[input_file] = {
                    'success': False,
                    'error': str(e)
                }
        
        self._update_progress(1.0, f"Batch conversion complete: {len(input_files)} files processed")
        return results
    
    def preview_conversion(self, mp3_path: str, algorithm: str = 'auto', 
                          preview_duration: float = 10.0) -> dict:
        """Generate a preview of the conversion (first N seconds)"""
        try:
            # Load full audio
            y, sr = self.load_audio(mp3_path)
            
            # Trim to preview duration
            preview_samples = int(preview_duration * sr)
            y_preview = y[:preview_samples] if len(y) > preview_samples else y
            
            # Store for onset detection
            self.y = y_preview
            self.sr = sr
            
            # Select algorithm
            if algorithm == 'auto':
                analysis = self.analyze_audio_characteristics(y_preview, sr)
                selected_algorithm = analysis['recommended_algorithm']
                self.sensitivity = analysis.get('recommended_sensitivity', 0.5)
            else:
                selected_algorithm = algorithm
                analysis = None
            
            # Convert preview
            if selected_algorithm == 'chroma':
                chroma, times = self.extract_pitch_chroma(y_preview, sr)
                notes = self.chroma_to_midi_notes(chroma, times)
            elif selected_algorithm == 'cqt':
                cqt, times = self.extract_pitch_cqt(y_preview, sr)
                notes = self.cqt_to_midi_notes(cqt, times)
            elif selected_algorithm == 'onset':
                onset_times, f0_times, f0, voiced_flag = self.extract_pitch_onset(y_preview, sr)
                notes = self.onset_to_midi_notes(onset_times, f0_times, f0, voiced_flag)
            
            # Post-process
            notes = self.post_process_notes(notes)
            
            return {
                'success': True,
                'notes': notes,
                'algorithm_used': selected_algorithm,
                'preview_duration': len(y_preview) / sr,
                'estimated_full_notes': int(len(notes) * (len(y) / len(y_preview))),
                'analysis': analysis
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_conversion_quality_score(self, notes: List[dict]) -> dict:
        """Analyze the quality of converted notes"""
        if not notes:
            return {'score': 0, 'issues': ['No notes detected']}
        
        issues = []
        score = 100
        
        # Check note density (notes per second)
        if len(notes) > 0:
            total_duration = max(note['start'] + note['duration'] for note in notes)
            notes_per_second = len(notes) / total_duration
            
            if notes_per_second > 10:
                issues.append('Very high note density - may be noisy')
                score -= 20
            elif notes_per_second < 0.5:
                issues.append('Low note density - may have missed notes')
                score -= 10
        
        # Check for very short notes
        short_notes = [n for n in notes if n['duration'] < 0.05]
        if len(short_notes) > len(notes) * 0.3:
            issues.append('Many very short notes detected')
            score -= 15
        
        # Check velocity distribution
        velocities = [n['velocity'] for n in notes]
        if len(set(velocities)) < 3:
            issues.append('Limited velocity variation')
            score -= 10
        
        # Check pitch range
        pitches = [n['note'] for n in notes]
        pitch_range = max(pitches) - min(pitches)
        if pitch_range < 12:  # Less than one octave
            issues.append('Limited pitch range')
            score -= 10
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,
            'note_density': notes_per_second if 'notes_per_second' in locals() else 0
        }
        
        return {
            'score': max(0, score),
            'total_notes': len(notes),
            'duration': total_duration if 'total_duration' in locals() else 0,
            'issues': issues,