import numpy as np
import sounddevice as sd
from typing import Optional
from enum import Enum


class FilterType(Enum):
    LOWPASS = "lowpass"
    HIGHPASS = "highpass"
    BANDPASS = "bandpass"


class Module:
    def __init__(self):
        self.sample_rate = 44100  # Standard sample rate
        self.inputs = {}
        self.output = None

    def process(self, time_array: np.ndarray) -> np.ndarray:
        """Process the input and return output for the given time array"""
        raise NotImplementedError


class SineOscillator(Module):
    def __init__(self, frequency: float = 440.0, amplitude: float = 1.0):
        super().__init__()
        self.base_frequency = frequency
        self.base_amplitude = amplitude
        self.freq_mod_input = None
        self.amp_mod_input = None

    def set_frequency_modulation(self, module: Module):
        self.freq_mod_input = module

    def set_amplitude_modulation(self, module: Module):
        self.amp_mod_input = module

    def process(self, time_array: np.ndarray) -> np.ndarray:
        # Get modulation values if connected
        freq_mod = 1.0
        amp_mod = 1.0

        if self.freq_mod_input:
            freq_mod = self.freq_mod_input.process(time_array)

        if self.amp_mod_input:
            amp_mod = self.amp_mod_input.process(time_array)

        frequency = self.base_frequency * (1 + freq_mod)
        amplitude = self.base_amplitude * amp_mod

        return amplitude * np.sin(2 * np.pi * frequency * time_array)


class SquareOscillator(Module):
    def __init__(
        self, frequency: float = 440.0, amplitude: float = 1.0, duty_cycle: float = 0.5
    ):
        super().__init__()
        self.base_frequency = frequency
        self.base_amplitude = amplitude
        self.duty_cycle = max(0.0, min(1.0, duty_cycle))  # Clamp between 0 and 1
        self.freq_mod_input = None
        self.amp_mod_input = None
        self.duty_mod_input = None

    def set_frequency_modulation(self, module: Module):
        self.freq_mod_input = module

    def set_amplitude_modulation(self, module: Module):
        self.amp_mod_input = module

    def set_duty_cycle_modulation(self, module: Module):
        self.duty_mod_input = module

    def process(self, time_array: np.ndarray) -> np.ndarray:
        freq_mod = 1.0
        amp_mod = 1.0
        duty_mod = 0.0

        if self.freq_mod_input:
            freq_mod = self.freq_mod_input.process(time_array)
        if self.amp_mod_input:
            amp_mod = self.amp_mod_input.process(time_array)
        if self.duty_mod_input:
            duty_mod = self.duty_mod_input.process(time_array)

        frequency = self.base_frequency * (1 + freq_mod)
        amplitude = self.base_amplitude * amp_mod
        duty = np.clip(self.duty_cycle + duty_mod, 0.0, 1.0)

        # Generate square wave using sign of sine wave and duty cycle
        phase = 2 * np.pi * frequency * time_array
        square = np.where(np.mod(phase, 2 * np.pi) / (2 * np.pi) < duty, 1.0, -1.0)
        return amplitude * square


class TriangleOscillator(Module):
    def __init__(self, frequency: float = 440.0, amplitude: float = 1.0):
        super().__init__()
        self.base_frequency = frequency
        self.base_amplitude = amplitude
        self.freq_mod_input = None
        self.amp_mod_input = None

    def set_frequency_modulation(self, module: Module):
        self.freq_mod_input = module

    def set_amplitude_modulation(self, module: Module):
        self.amp_mod_input = module

    def process(self, time_array: np.ndarray) -> np.ndarray:
        freq_mod = 1.0
        amp_mod = 1.0

        if self.freq_mod_input:
            freq_mod = self.freq_mod_input.process(time_array)
        if self.amp_mod_input:
            amp_mod = self.amp_mod_input.process(time_array)

        frequency = self.base_frequency * (1 + freq_mod)
        amplitude = self.base_amplitude * amp_mod

        # Generate triangle wave using arcsin of sine wave
        phase = 2 * np.pi * frequency * time_array
        triangle = (2 / np.pi) * np.arcsin(np.sin(phase))
        return amplitude * triangle


class VCA(Module):
    def __init__(
        self, input_module: Optional[Module] = None, cv_input: Optional[Module] = None
    ):
        super().__init__()
        self.input_module = input_module
        self.cv_input = cv_input
        self.base_gain = 1.0

    def set_input(self, module: Module):
        self.input_module = module

    def set_cv_input(self, module: Module):
        self.cv_input = module

    def process(self, time_array: np.ndarray) -> np.ndarray:
        if not self.input_module:
            return np.zeros_like(time_array)

        input_signal = self.input_module.process(time_array)

        # Get CV (control voltage) signal, default to 1.0 if no CV input
        if self.cv_input:
            # Normalize CV to [0, 1] range and apply as gain
            cv_signal = self.cv_input.process(time_array)
            cv_signal = (cv_signal + 1) * 0.5  # Convert from [-1, 1] to [0, 1]
            gain = cv_signal * self.base_gain
        else:
            gain = self.base_gain

        return input_signal * gain


class Filter(Module):
    def __init__(
        self, filter_type: FilterType = FilterType.LOWPASS, cutoff_freq: float = 1000
    ):
        super().__init__()
        self.filter_type = filter_type
        self.cutoff_freq = cutoff_freq
        self.input_module = None
        self.resonance = 1.0  # Q factor

    def set_input(self, module: Module):
        self.input_module = module

    def process(self, time_array: np.ndarray) -> np.ndarray:
        if not self.input_module:
            return np.zeros_like(time_array)

        input_signal = self.input_module.process(time_array)

        # Simple IIR filter implementation
        dt = 1 / self.sample_rate
        alpha = dt / (1 / (2 * np.pi * self.cutoff_freq) + dt)

        filtered = np.zeros_like(input_signal)
        filtered[0] = input_signal[0]

        if self.filter_type == FilterType.LOWPASS:
            for i in range(1, len(input_signal)):
                filtered[i] = alpha * input_signal[i] + (1 - alpha) * filtered[i - 1]
        elif self.filter_type == FilterType.HIGHPASS:
            for i in range(1, len(input_signal)):
                filtered[i] = alpha * (
                    filtered[i - 1] + input_signal[i] - input_signal[i - 1]
                )

        return filtered


class Mixer(Module):
    def __init__(self):
        super().__init__()
        self.input_modules: list[tuple[Module, float]] = []  # (module, gain) pairs

    def add_input(self, module: Module, gain: float = 1.0):
        self.input_modules.append((module, gain))

    def process(self, time_array: np.ndarray) -> np.ndarray:
        if not self.input_modules:
            return np.zeros_like(time_array)

        # Mix all inputs with their respective gains
        output = np.zeros_like(time_array)
        for module, gain in self.input_modules:
            output += gain * module.process(time_array)

        # Normalize to prevent clipping
        max_val = np.max(np.abs(output))
        if max_val > 1.0:
            output /= max_val

        return output


class Sequencer(Module):
    """A sequencer module that plays a sequence of notes with proper timing."""

    # Standard MIDI note frequencies
    NOTE_FREQUENCIES = {
        "C": 261.63,
        "C#": 277.18,
        "D": 293.66,
        "D#": 311.13,
        "E": 329.63,
        "F": 349.23,
        "F#": 369.99,
        "G": 392.00,
        "G#": 415.30,
        "A": 440.00,
        "A#": 466.16,
        "B": 493.88,
    }

    def __init__(self, bpm=120.0):
        """Initialize the sequencer.

        Args:
            bpm (float): Beats per minute for the sequence
        """
        super().__init__()
        self.bpm = bpm
        self.step_duration = 60.0 / bpm  # Duration of one beat in seconds
        self.sequence = []  # List of (frequency, duration) tuples
        self.output_module = None

    def set_output(self, module):
        """Set the output module that will receive the sequence."""
        self.output_module = module

    def add_note(self, note_name, duration):
        """Add a note to the sequence.

        Args:
            note_name (str): Note name (e.g., 'C4', 'A#3')
            duration (float): Duration in beats
        """
        # Parse note name (e.g., 'C4' -> 'C' and 4)
        note = note_name[:-1]
        octave = int(note_name[-1])

        # Calculate frequency based on octave
        base_freq = self.NOTE_FREQUENCIES[note]
        frequency = base_freq * (2 ** (octave - 4))  # A4 is our reference octave

        # Add to sequence
        self.sequence.append((frequency, duration))

    def process(self, t):
        """Process the sequence for the given time array.

        Args:
            t (np.ndarray): Time array in seconds

        Returns:
            np.ndarray: Output signal
        """
        if not self.output_module:
            return np.zeros_like(t)

        # Calculate total sequence duration
        total_duration = sum(
            duration * self.step_duration for _, duration in self.sequence
        )

        # Initialize output array
        output = np.zeros_like(t)

        # Current time in sequence
        current_time = 0

        # Process each note
        for frequency, duration in self.sequence:
            note_duration = duration * self.step_duration

            # Find indices for this note
            note_start = current_time
            note_end = current_time + note_duration

            # Get the time indices for this note
            note_indices = (t >= note_start) & (t < note_end)

            if np.any(note_indices):
                # Set frequency for this note
                if isinstance(
                    self.output_module,
                    (SineOscillator, SquareOscillator, TriangleOscillator),
                ):
                    self.output_module.base_frequency = frequency
                elif hasattr(self.output_module, "input_modules"):
                    # If it's a mixer, update all input oscillators
                    for module, _ in self.output_module.input_modules:
                        if isinstance(
                            module,
                            (SineOscillator, SquareOscillator, TriangleOscillator),
                        ):
                            module.base_frequency = frequency

                # Process the note
                note_output = self.output_module.process(t[note_indices])

                # Apply amplitude envelope
                note_time = t[note_indices] - note_start
                envelope = np.exp(-note_time / 0.1)  # Quick attack, natural decay
                note_output = note_output * envelope

                # Add to output
                output[note_indices] = note_output

            current_time += note_duration

        return output


class AudioOutput:
    def __init__(self, input_module: Optional[Module] = None):
        self.sample_rate = 44100
        self.input_module = input_module
        self.is_playing = False
        self.stream = None

    def set_input(self, module: Module):
        self.input_module = module

    def start(self, duration: float = 0):
        if not self.input_module:
            raise ValueError("No input module connected")

        if duration == 0:
            # Run indefinitely
            def callback(outdata, frames, time, status):
                if status:
                    print(status)
                if self.input_module:  # Add type check
                    t = np.arange(frames) / self.sample_rate + self.current_time
                    outdata[:] = self.input_module.process(t).reshape(-1, 1)
                    self.current_time += frames / self.sample_rate

            self.current_time = 0
            self.stream = sd.OutputStream(
                channels=1, callback=callback, samplerate=self.sample_rate
            )
            self.stream.start()
        else:
            # Play for specified duration
            t = np.arange(int(duration * self.sample_rate)) / self.sample_rate
            if self.input_module:  # Add type check
                audio_data = self.input_module.process(t)
                sd.play(audio_data, self.sample_rate)
                sd.wait()

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None


# Example usage:
if __name__ == "__main__":
    from examples import (
        example_1_waveforms,
        example_2_chord,
        example_3_vca,
        example_4_beeper,
        example_5_morse_code,
        example_6_drum_and_lead,
        example_7_sequencer,
    )

    # Uncomment the examples you want to run
    # example_1_waveforms()
    # example_2_chord()
    # example_3_vca()
    # example_4_beeper()
    # example_5_morse_code()
    # example_6_drum_and_lead()
    example_7_sequencer()
