#!/usr/bin/env python3
"""
Test MP3 to MIDI Dialog Layout
"""

import tkinter as tk
from tkinter import ttk
import os

def test_dialog():
    """Test the MP3 to MIDI conversion dialog layout"""
    
    # Create root window (hidden)
    root = tk.Tk()
    root.withdraw()
    
    # Create test dialog
    conversion_dialog = tk.Toplevel(root)
    conversion_dialog.title("MP3 to MIDI Conversion - Layout Test")
    conversion_dialog.geometry("580x650")
    conversion_dialog.resizable(True, True)
    
    # Center on screen
    conversion_dialog.update_idletasks()
    x = (conversion_dialog.winfo_screenwidth() // 2) - (580 // 2)
    y = (conversion_dialog.winfo_screenheight() // 2) - (650 // 2)
    conversion_dialog.geometry(f"580x650+{x}+{y}")
    conversion_dialog.minsize(580, 600)
    
    # Title
    tk.Label(conversion_dialog, text="MP3 to MIDI Conversion", 
            font=("Arial", 16, "bold")).pack(pady=10)
    
    tk.Label(conversion_dialog, text="File: test-audio.mp3", 
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
    
    # Options
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
    
    # Duration
    duration_frame = tk.Frame(options_frame)
    duration_frame.pack(fill="x", pady=5)
    tk.Label(duration_frame, text="Min Note Duration (ms):").pack(side="left", padx=10)
    duration_var = tk.IntVar(value=100)
    duration_scale = tk.Scale(duration_frame, from_=50, to=500, resolution=10,
                            orient="horizontal", variable=duration_var)
    duration_scale.pack(side="right", fill="x", expand=True, padx=10)
    
    # Progress
    progress_frame = ttk.LabelFrame(conversion_dialog, text="Conversion Progress")
    progress_frame.pack(fill="x", padx=20, pady=10)
    
    progress_var = tk.DoubleVar(value=0.0)
    progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
    progress_bar.pack(fill="x", padx=10, pady=10)
    
    status_var = tk.StringVar(value="Ready to convert...")
    status_label = tk.Label(progress_frame, textvariable=status_var, font=("Arial", 9))
    status_label.pack(pady=5)
    
    # Analysis output
    analysis_frame = ttk.LabelFrame(conversion_dialog, text="Analysis Results")
    analysis_frame.pack(fill="both", expand=True, padx=20, pady=(10, 5))
    
    text_frame = tk.Frame(analysis_frame)
    text_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    analysis_text = tk.Text(text_frame, height=3, wrap=tk.WORD, font=("Consolas", 9))
    scrollbar_analysis = ttk.Scrollbar(text_frame, orient="vertical", command=analysis_text.yview)
    analysis_text.configure(yscrollcommand=scrollbar_analysis.set)
    
    analysis_text.pack(side="left", fill="both", expand=True)
    scrollbar_analysis.pack(side="right", fill="y")
    
    analysis_text.insert(tk.END, "📋 Click 'Preview Analysis' to analyze the audio file...\n")
    analysis_text.insert(tk.END, "🎵 Then click 'Convert to MIDI' to perform the conversion.\n")
    
    # ACTION BUTTONS - Fixed at bottom
    button_frame = tk.Frame(conversion_dialog, bg="#f0f0f0", relief="raised", bd=2, height=80)
    button_frame.pack(side="bottom", fill="x", padx=10, pady=10)
    button_frame.pack_propagate(False)
    
    # Instruction
    instruction_label = tk.Label(button_frame, text="🎯 Choose an action:", 
                               font=("Arial", 12, "bold"), bg="#f0f0f0", fg="#2c3e50")
    instruction_label.pack(pady=(10, 5))
    
    # Buttons
    buttons_container = tk.Frame(button_frame, bg="#f0f0f0")
    buttons_container.pack()
    
    def test_preview():
        status_var.set("Preview test - This would analyze the audio")
        analysis_text.delete(1.0, tk.END)
        analysis_text.insert(tk.END, "✅ Test preview analysis completed!\n")
        analysis_text.insert(tk.END, "Algorithm: Melodia\nNotes detected: 45\nTempo: 120 BPM\n")
        progress_var.set(100)
    
    def test_convert():
        status_var.set("Convert test - This would convert to MIDI")
        analysis_text.insert(tk.END, "\n✅ Test conversion completed!\n")
        analysis_text.insert(tk.END, "📁 MIDI would be saved here\n")
        progress_var.set(100)
    
    preview_btn = tk.Button(buttons_container, text="🔍 Preview Analysis", 
                          command=test_preview,
                          bg="#3498db", fg="white", font=("Arial", 11, "bold"),
                          relief="raised", bd=3, padx=15, pady=5,
                          cursor="hand2", width=18)
    preview_btn.pack(side="left", padx=8)
    
    convert_btn = tk.Button(buttons_container, text="🎵 Convert to MIDI", 
                          command=test_convert,
                          bg="#27ae60", fg="white", font=("Arial", 11, "bold"),
                          relief="raised", bd=3, padx=15, pady=5,
                          cursor="hand2", width=18)
    convert_btn.pack(side="left", padx=8)
    
    close_btn = tk.Button(buttons_container, text="❌ Close", 
                        command=conversion_dialog.destroy,
                        font=("Arial", 10), bg="#e74c3c", fg="white",
                        relief="raised", bd=2, cursor="hand2", width=10)
    close_btn.pack(side="left", padx=8)
    
    print("🎯 Dialog test launched!")
    print("✅ All buttons should be visible at the bottom")
    print("✅ Dialog should be properly sized and centered")
    
    # Run the dialog
    conversion_dialog.mainloop()

if __name__ == "__main__":
    test_dialog()
