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
        """Extract pitch using chroma features with enhanced preprocessing"""
        self._update_progress(0.3, "Extracting enhanced chroma features...")
        
        # Preprocess audio for better chroma extraction
        y_processed = self.preprocess_audio(y, sr)
        
        # Extract chroma features with better parameters
        chroma = librosa.feature.chroma_stft(
            y=y_processed, sr=sr, 
            hop_length=self.hop_length,
            n_fft=self.frame_length,
            norm=2,  # L2 normalization
            center=True
        )
        
        # Apply enhancement to chroma features
        chroma_enhanced = librosa.util.normalize(chroma, axis=0)
        
        # Get time frames
        times = librosa.frames_to_time(
            np.arange(chroma_enhanced.shape[1]), 
            sr=sr, 
            hop_length=self.hop_length
        )
        
        return chroma_enhanced, times
    
    def extract_pitch_cqt(self, y: np.ndarray, sr: int) -> Tuple[np.ndarray, np.ndarray]:
        """Enhanced CQT extraction with better parameters for pitch detection"""
        self._update_progress(0.3, "Extracting enhanced CQT features...")
        
        # Preprocess audio for better results
        y_processed = self.preprocess_audio(y, sr)
        
        # Calculate safe frequency range based on sample rate
        nyquist = sr / 2
        fmin = librosa.note_to_hz('C2')  # ~65 Hz
        
        # Calculate maximum frequency and bins to avoid exceeding Nyquist
        max_freq = min(librosa.note_to_hz('C7'), nyquist * 0.9)  # Stay below Nyquist
        n_bins = int(12 * np.log2(max_freq / fmin))  # Calculate bins for this range
        n_bins = min(n_bins, 84)  # Cap at 7 octaves maximum
        
        # Use enhanced CQT with safe parameters
        cqt = np.abs(librosa.cqt(
            y=y_processed, sr=sr,
            hop_length=self.hop_length,  # Use standard hop length
            fmin=fmin,
            n_bins=n_bins,
            bins_per_octave=12,
            filter_scale=1,
            sparsity=0.01
        ))
        
        # Apply spectral normalization for consistent analysis
        cqt_norm = librosa.util.normalize(cqt, axis=0)
        
        # Apply temporal smoothing to reduce noise
        cqt_smooth = gaussian_filter(cqt_norm, sigma=(0.5, 1.0))
        
        # Get time frames
        times = librosa.frames_to_time(
            np.arange(cqt_smooth.shape[1]), 
            sr=sr, 
            hop_length=self.hop_length
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
        base_threshold = 0.001 + (1 - self.sensitivity) * 0.01
        adaptive_threshold = max(base_threshold, mean_energy * 0.1)  # Lower multiplier
        
        print(f"DEBUG Chroma: max={global_max:.4f}, mean={mean_energy:.4f}, threshold={adaptive_threshold:.4f}")
        
        frame_count = 0
        valid_frames = 0
        
        # Process each time frame
        for i, time in enumerate(times[:-1]):
            frame_chroma = chroma_smooth[:, i]
            duration = times[i+1] - time
            
            frame_count += 1
            
            if duration < self.min_duration:
                continue
            
            # Dynamic threshold for this frame
            max_chroma = np.max(frame_chroma)
            if max_chroma > adaptive_threshold:
                valid_frames += 1
                
                # Find peaks with very low adaptive height
                peak_threshold = max_chroma * (0.05 + self.sensitivity * 0.1)  # Much lower threshold
                peaks, properties = find_peaks(
                    frame_chroma, 
                    height=peak_threshold,
                    distance=1
                )
                
                if i < 10:  # Debug first 10 frames
                    print(f"DEBUG Frame {i}: max={max_chroma:.4f}, threshold={peak_threshold:.4f}, peaks={len(peaks)}")
                    if len(peaks) > 0:
                        print(f"  Peak values: {frame_chroma[peaks]}")
                        print(f"  Peak indices (notes): {peaks}")
                
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
        
        # Adaptive threshold based on signal characteristics
        global_max = np.max(cqt_filtered)
        mean_energy = np.mean(cqt_filtered)
        
        # Adjust sensitivity based on user setting
        base_threshold = 0.0001 + (1 - self.sensitivity) * 0.001  # Much lower base
        adaptive_threshold = max(base_threshold, mean_energy * 0.05)  # Lower multiplier
        
        print(f"DEBUG CQT: max={global_max:.4f}, mean={mean_energy:.4f}, threshold={adaptive_threshold:.4f}")
        
        # Process each time frame
        for i, time in enumerate(times[:-1]):
            frame_cqt = cqt_filtered[:, i]
            duration = times[i+1] - time
            
            if duration < self.min_duration:
                continue
            
            max_cqt = np.max(frame_cqt)
            if max_cqt > adaptive_threshold:
                # Find peaks in the CQT with very low adaptive thresholding
                peak_threshold = max_cqt * (0.05 + self.sensitivity * 0.1)  # Much lower threshold
                peaks, properties = find_peaks(
                    frame_cqt, 
                    height=peak_threshold,
                    distance=1
                )
                
                print(f"DEBUG CQT Frame {i}: max={max_cqt:.4f}, threshold={peak_threshold:.4f}, peaks={len(peaks)}")
                
                # Limit polyphony
                if len(peaks) > self.max_polyphony:
                    # Keep only the strongest peaks
                    peak_heights = frame_cqt[peaks]
                    top_indices = np.argsort(peak_heights)[-self.max_polyphony:]
                    peaks = peaks[top_indices]
                
                for peak in peaks:
                    # Convert CQT bin to MIDI note
                    # CQT starts at C2 (MIDI 36) with 12 bins per octave
                    midi_note = 36 + peak  # C2 is MIDI note 36
                    
                    if 21 <= midi_note <= 108:  # Valid piano range
                        # Calculate velocity based on peak height
                        relative_strength = frame_cqt[peak] / max_cqt
                        velocity = int(velocity_range[0] + 
                                      (velocity_range[1] - velocity_range[0]) * 
                                      relative_strength)
                        
                        notes.append({
                            'note': midi_note,
                            'start': time,
                            'duration': duration,
                            'velocity': max(20, min(127, velocity)),
                            'channel': 0,
                            'confidence': relative_strength
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
            
            # Store for onset detection
            self.y = y
            self.sr = sr
            
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
        else:
            total_duration = 0
            notes_per_second = 0
        
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
            'duration': total_duration,
            'issues': issues,
            'note_density': notes_per_second
        }
    
    def generate_inspired_melody(self, analysis: dict, duration: float = 30.0, 
                                style: str = 'similar') -> List[dict]:
        """Generate new melody inspired by audio analysis characteristics"""
        self._update_progress(0.1, f"Generating {style} melody based on audio analysis...")
        
        notes = []
        tempo = analysis.get('tempo', 120)
        key_signature = self._detect_key_signature(analysis)
        scale_notes = self._get_scale_notes(key_signature, style)
        
        # Calculate timing parameters
        beat_duration = 60.0 / tempo
        total_beats = duration / beat_duration
        
        # Generate note sequence based on audio characteristics
        current_time = 0.0
        
        while current_time < duration:
            # Note selection based on style and analysis
            if style == 'similar':
                note = self._generate_similar_note(analysis, scale_notes, current_time)
            elif style == 'jazz':
                note = self._generate_jazz_note(analysis, scale_notes, current_time)
            elif style == 'classical':
                note = self._generate_classical_note(analysis, scale_notes, current_time)
            elif style == 'ambient':
                note = self._generate_ambient_note(analysis, scale_notes, current_time)
            else:
                note = self._generate_creative_note(analysis, scale_notes, current_time)
            
            if note:
                notes.append(note)
                current_time = note['start'] + note['duration']
            else:
                current_time += beat_duration * 0.5  # Small step forward
        
        self._update_progress(1.0, f"Generated {len(notes)} notes in {style} style")
        return notes
    
    def _detect_key_signature(self, analysis: dict) -> str:
        """Detect likely key signature from audio analysis"""
        # Simple key detection based on chroma complexity and harmonic ratio
        complexity = analysis.get('chroma_complexity', 0.1)
        harmonic_ratio = analysis.get('harmonic_ratio', 0.5)
        
        # Major keys for simpler, more harmonic content
        if complexity < 0.1 and harmonic_ratio > 0.6:
            return random.choice(['C', 'G', 'D', 'A', 'F'])
        # Minor keys for more complex content
        elif complexity > 0.15:
            return random.choice(['Am', 'Em', 'Bm', 'Dm', 'Fm'])
        else:
            return random.choice(['C', 'Am', 'G', 'Em'])
    
    def _get_scale_notes(self, key: str, style: str) -> List[int]:
        """Get scale notes for given key and style"""
        # Base notes for different keys (MIDI note numbers)
        key_bases = {
            'C': 60, 'C#': 61, 'D': 62, 'D#': 63, 'E': 64, 'F': 65,
            'F#': 66, 'G': 67, 'G#': 68, 'A': 69, 'A#': 70, 'B': 71,
            'Am': 57, 'A#m': 58, 'Bm': 59, 'Cm': 60, 'C#m': 61, 'Dm': 62,
            'D#m': 63, 'Em': 64, 'Fm': 65, 'F#m': 66, 'Gm': 67, 'G#m': 68
        }
        
        base = key_bases.get(key, 60)
        
        # Scale patterns
        if style == 'jazz':
            # Jazz scales with extensions
            pattern = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16]  # Major with extensions
        elif style == 'ambient':
            # Pentatonic for ambient
            pattern = [0, 2, 5, 7, 9, 12, 14, 17, 19, 21]
        elif 'm' in key:
            # Natural minor scale
            pattern = [0, 2, 3, 5, 7, 8, 10, 12, 14, 15]
        else:
            # Major scale
            pattern = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16]
        
        # Generate notes across multiple octaves
        scale_notes = []
        for octave in [-12, 0, 12, 24]:
            for interval in pattern:
                note = base + octave + interval
                if 21 <= note <= 108:  # Valid MIDI range
                    scale_notes.append(note)
        
        return scale_notes
    
    def _generate_similar_note(self, analysis: dict, scale_notes: List[int], 
                              current_time: float) -> dict:
        """Generate note similar to original audio characteristics"""
        tempo = analysis.get('tempo', 120)
        onset_density = analysis.get('onset_density', 2.0)
        harmonic_ratio = analysis.get('harmonic_ratio', 0.5)
        
        # Duration based on onset density
        if onset_density > 3:
            duration = random.uniform(0.2, 0.5)  # Faster notes
        elif onset_density < 1:
            duration = random.uniform(1.0, 2.0)  # Slower notes
        else:
            duration = random.uniform(0.4, 0.8)  # Medium notes
        
        # Note selection weighted by harmonic content
        if harmonic_ratio > 0.7:
            # Prefer chord tones
            note = random.choice(scale_notes[::2])  # Every other note (chord tones)
        else:
            # More variety
            note = random.choice(scale_notes)
        
        velocity = random.randint(60, 100)
        
        return {
            'note': note,
            'start': current_time,
            'duration': duration,
            'velocity': velocity,
            'channel': 0
        }
    
    def _generate_jazz_note(self, analysis: dict, scale_notes: List[int], 
                           current_time: float) -> dict:
        """Generate jazz-style note"""
        # Jazz characteristics: swing, extended chords, syncopation
        duration = random.choice([0.25, 0.5, 0.75, 1.0, 1.5])  # Swing-like durations
        
        # Favor 7ths, 9ths, and chromatic approaches
        note = random.choice(scale_notes)
        if random.random() < 0.3:  # 30% chance of chromatic approach
            note += random.choice([-1, 1])
            note = max(21, min(108, note))
        
        velocity = random.randint(70, 110)  # Generally louder for jazz
        
        return {
            'note': note,
            'start': current_time,
            'duration': duration,
            'velocity': velocity,
            'channel': 0
        }
    
    def _generate_classical_note(self, analysis: dict, scale_notes: List[int], 
                                current_time: float) -> dict:
        """Generate classical-style note"""
        # Classical characteristics: structured, melodic, dynamic
        duration = random.choice([0.5, 1.0, 1.5, 2.0])  # More structured durations
        
        # Prefer stepwise motion
        note = random.choice(scale_notes[:len(scale_notes)//2])  # Middle range
        
        # Dynamic variety
        velocity = random.randint(50, 95)
        
        return {
            'note': note,
            'start': current_time,
            'duration': duration,
            'velocity': velocity,
            'channel': 0
        }
    
    def _generate_ambient_note(self, analysis: dict, scale_notes: List[int], 
                              current_time: float) -> dict:
        """Generate ambient-style note"""
        # Ambient characteristics: sustained, floating, sparse
        duration = random.uniform(2.0, 8.0)  # Long, sustained notes
        
        # Prefer higher register and consonant intervals
        note = random.choice(scale_notes[len(scale_notes)//2:])  # Upper range
        
        velocity = random.randint(40, 70)  # Softer dynamics
        
        return {
            'note': note,
            'start': current_time,
            'duration': duration,
            'velocity': velocity,
            'channel': 0
        }
    
    def _generate_creative_note(self, analysis: dict, scale_notes: List[int], 
                               current_time: float) -> dict:
        """Generate creative/experimental note"""
        # Creative characteristics: unexpected rhythms, wide intervals
        duration = random.choice([0.125, 0.25, 0.75, 1.5, 3.0])  # Varied durations
        
        # Allow wider range and more variety
        note = random.choice(scale_notes)
        if random.random() < 0.2:  # 20% chance of octave jump
            note += random.choice([-12, 12])
            note = max(21, min(108, note))
        
        velocity = random.randint(30, 120)  # Wide dynamic range
        
        return {
            'note': note,
            'start': current_time,
            'duration': duration,
            'velocity': velocity,
            'channel': 0
        }
    
    def generate_harmony(self, melody_notes: List[dict], analysis: dict) -> List[dict]:
        """Generate harmonic accompaniment for a melody"""
        self._update_progress(0.5, "Generating harmonic accompaniment...")
        
        harmony_notes = []
        key = self._detect_key_signature(analysis)
        chord_progression = self._generate_chord_progression(key, len(melody_notes))
        
        # Group melody notes by time segments for chord changes
        chord_duration = 2.0  # 2 seconds per chord
        current_chord_idx = 0
        
        for note in melody_notes:
            chord_idx = int(note['start'] // chord_duration) % len(chord_progression)
            chord = chord_progression[chord_idx]
            
            # Add chord tones as harmony
            for i, chord_tone in enumerate(chord):
                harmony_note = {
                    'note': chord_tone,
                    'start': note['start'],
                    'duration': min(note['duration'] * 2, chord_duration),
                    'velocity': max(30, note['velocity'] - 20 - i * 5),  # Softer than melody
                    'channel': 1  # Different channel for harmony
                }
                harmony_notes.append(harmony_note)
        
        return harmony_notes
    
    def _generate_chord_progression(self, key: str, num_chords: int) -> List[List[int]]:
        """Generate a chord progression in the given key"""
        # Common chord progressions
        progressions = {
            'major': [
                [0, 4, 7],      # I (major)
                [5, 9, 12],     # vi (minor)
                [2, 5, 9],      # ii (minor)
                [7, 11, 14]     # V (major)
            ],
            'minor': [
                [0, 3, 7],      # i (minor)
                [5, 8, 12],     # iv (minor)
                [7, 11, 14],    # V (major)
                [3, 7, 10]      # bIII (major)
            ]
        }
        
        key_base = {'C': 60, 'G': 67, 'D': 62, 'A': 69, 'F': 65, 
                    'Am': 57, 'Em': 64, 'Dm': 62, 'Bm': 59, 'Fm': 65}.get(key, 60)
        
        is_minor = 'm' in key
        chord_templates = progressions['minor' if is_minor else 'major']
        
        # Generate chord progression
        chords = []
        for i in range(max(4, num_chords // 10)):  # At least 4 chords
            template = chord_templates[i % len(chord_templates)]
            chord = [key_base + interval for interval in template]
            chords.append(chord)
        
        return chords
    
    def create_variations(self, original_notes: List[dict], num_variations: int = 3) -> List[List[dict]]:
        """Create musical variations of the original notes"""
        self._update_progress(0.3, f"Creating {num_variations} variations...")
        
        variations = []
        
        for i in range(num_variations):
            if i == 0:
                # Rhythmic variation
                varied_notes = self._apply_rhythmic_variation(original_notes)
            elif i == 1:
                # Melodic variation (transposition and intervals)
                varied_notes = self._apply_melodic_variation(original_notes)
            else:
                # Dynamic and articulation variation
                varied_notes = self._apply_dynamic_variation(original_notes)
            
            variations.append(varied_notes)
        
        return variations
    
    def _apply_rhythmic_variation(self, notes: List[dict]) -> List[dict]:
        """Apply rhythmic variation to notes"""
        varied = []
        for note in notes:
            new_note = note.copy()
            # Vary duration and timing slightly
            new_note['duration'] *= random.uniform(0.7, 1.4)
            new_note['start'] += random.uniform(-0.1, 0.1)
            varied.append(new_note)
        return varied
    
    def _apply_melodic_variation(self, notes: List[dict]) -> List[dict]:
        """Apply melodic variation to notes"""
        varied = []
        transpose = random.choice([-7, -5, -3, 3, 5, 7])  # Transpose by interval
        
        for note in notes:
            new_note = note.copy()
            new_note['note'] = max(21, min(108, note['note'] + transpose))
            # Occasionally add octave jumps
            if random.random() < 0.1:
                new_note['note'] += random.choice([-12, 12])
                new_note['note'] = max(21, min(108, new_note['note']))
            varied.append(new_note)
        return varied
    
    def _apply_dynamic_variation(self, notes: List[dict]) -> List[dict]:
        """Apply dynamic and articulation variation"""
        varied = []
        for note in notes:
            new_note = note.copy()
            # Vary velocity
            new_note['velocity'] = max(20, min(127, note['velocity'] + random.randint(-20, 20)))
            # Occasionally make staccato
            if random.random() < 0.2:
                new_note['duration'] *= 0.5
            varied.append(new_note)
        return varied
    

# Standalone conversion function
def convert_mp3_to_midi_simple(mp3_path: str, midi_path: str, algorithm: str = 'cqt') -> bool:
    """Simple function for MP3 to MIDI conversion"""
    converter = MP3ToMIDIConverter()
    return converter.convert_mp3_to_midi(mp3_path, midi_path, algorithm)


if __name__ == "__main__":
    import random
    
    print("🎵 MP3 to MIDI Converter Test")
    
    # Example usage
    converter = MP3ToMIDIConverter()
    
    # Test with a hypothetical MP3 file
    # converter.convert_mp3_to_midi("test.mp3", "output.mid", "cqt")
    
    print("✅ MP3 to MIDI Converter ready for use!")
