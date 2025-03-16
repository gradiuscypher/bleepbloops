from bleeps import (
    SineOscillator,
    SquareOscillator,
    TriangleOscillator,
    Filter,
    Mixer,
    AudioOutput,
    VCA,
    FilterType,
)


def example_1_waveforms():
    """Demonstrate basic waveforms with different modulation types."""
    # Create base oscillators at different frequencies
    sine = SineOscillator(frequency=440)  # A4 note
    square = SquareOscillator(
        frequency=220, duty_cycle=0.3
    )  # A3 note with narrow pulse
    triangle = TriangleOscillator(frequency=110)  # A2 note

    # Create modulators
    lfo1 = SineOscillator(frequency=2, amplitude=0.3)  # 2 Hz amplitude modulation
    lfo2 = SineOscillator(frequency=0.5, amplitude=0.2)  # 0.5 Hz duty cycle modulation
    lfo3 = TriangleOscillator(frequency=4, amplitude=0.1)  # 4 Hz frequency modulation

    # Set up modulation
    sine.set_amplitude_modulation(lfo1)  # Tremolo effect on sine
    square.set_duty_cycle_modulation(lfo2)  # Pulse width modulation
    triangle.set_frequency_modulation(lfo3)  # Vibrato effect on triangle

    # Create a mixer and add all oscillators
    mixer = Mixer()
    mixer.add_input(sine, gain=0.3)
    mixer.add_input(square, gain=0.3)
    mixer.add_input(triangle, gain=0.3)

    # Create a filter for the final output
    filter_module = Filter(FilterType.LOWPASS, cutoff_freq=2000)
    filter_module.set_input(mixer)

    # Create audio output
    output = AudioOutput(filter_module)

    # Play for 10 seconds
    print("Playing demonstration of sine, square, and triangle waves...")
    print("- Sine wave (440 Hz) with tremolo effect")
    print("- Square wave (220 Hz) with pulse width modulation")
    print("- Triangle wave (110 Hz) with vibrato effect")
    output.start(duration=10)


def example_2_chord():
    """Demonstrate a major chord with evolving texture."""
    # Create a C major chord (C4-E4-G4) with different waveforms
    root = SineOscillator(frequency=261.63)  # C4 - fundamental
    third = TriangleOscillator(frequency=329.63)  # E4 - adds warmth
    fifth = SquareOscillator(frequency=392.00, duty_cycle=0.6)  # G4 - adds brightness

    # Add subtle modulation for movement
    vibrato = SineOscillator(frequency=5, amplitude=0.02)  # Gentle frequency vibrato
    shimmer = TriangleOscillator(
        frequency=0.5, amplitude=0.1
    )  # Slow amplitude variation

    # Apply modulation
    root.set_frequency_modulation(vibrato)
    third.set_amplitude_modulation(shimmer)
    fifth.set_duty_cycle_modulation(shimmer)  # Use same LFO for coherence

    # Mix the chord
    chord_mixer = Mixer()
    chord_mixer.add_input(root, gain=0.4)  # Stronger fundamental
    chord_mixer.add_input(third, gain=0.3)  # Balanced third
    chord_mixer.add_input(fifth, gain=0.2)  # Softer fifth for harmony

    # Add gentle filtering
    chord_filter = Filter(FilterType.LOWPASS, cutoff_freq=3000)
    chord_filter.set_input(chord_mixer)

    # Create audio output
    chord_output = AudioOutput(chord_filter)

    print("Playing C major chord with evolving texture...")
    print("- C4 (261.63 Hz) sine wave with subtle vibrato")
    print("- E4 (329.63 Hz) triangle wave with amplitude shimmer")
    print("- G4 (392.00 Hz) square wave with pulse width modulation")
    chord_output.start(duration=10)


def example_3_vca():
    """Demonstrate VCA capabilities with tremolo and envelope effects."""
    # Create a base tone with two oscillators
    base_tone = SineOscillator(frequency=440)  # A4
    harmonic = TriangleOscillator(frequency=880)  # A5 (first harmonic)

    # Mix the two tones
    tone_mixer = Mixer()
    tone_mixer.add_input(base_tone, gain=0.6)
    tone_mixer.add_input(harmonic, gain=0.4)

    # Create two different CV modulators for the VCA
    # 1. Fast tremolo effect
    tremolo = SineOscillator(frequency=6, amplitude=0.5)

    # 2. Slow envelope for overall volume shape
    envelope = TriangleOscillator(frequency=0.1, amplitude=0.8)

    # Create two VCAs in series
    vca1 = VCA(tone_mixer)  # First VCA for tremolo
    vca1.set_cv_input(tremolo)

    vca2 = VCA(vca1)  # Second VCA for envelope
    vca2.set_cv_input(envelope)

    # Add some filtering
    vca_filter = Filter(FilterType.LOWPASS, cutoff_freq=2000)
    vca_filter.set_input(vca2)

    # Create audio output
    vca_output = AudioOutput(vca_filter)

    print("Playing VCA demonstration...")
    print("- Base tone: 440 Hz sine + 880 Hz triangle")
    print("- Fast tremolo effect at 6 Hz")
    print("- Slow volume envelope at 0.1 Hz")
    vca_output.start(duration=10)


def example_4_beeper():
    """Demonstrate VCA as an on/off gate to create a beeping sound."""
    # Create a simple tone using a square wave
    tone = SquareOscillator(frequency=500, amplitude=0.7)  # A5 note

    # Create a square LFO at a very low frequency to act as a gate
    # 1 Hz = one beep per second
    gate = SquareOscillator(frequency=2, amplitude=1.0)  # 2 beeps per second

    # Use VCA as a gate
    vca = VCA(tone)
    vca.set_cv_input(gate)

    # Add a bit of filtering to smooth out the clicks
    filter_module = Filter(FilterType.LOWPASS, cutoff_freq=4000)
    filter_module.set_input(vca)

    # Create audio output
    output = AudioOutput(filter_module)

    print("Playing beeper demonstration...")
    print("- 880 Hz square wave")
    print("- Gated on/off at 2 Hz (2 beeps per second)")
    output.start(duration=5)


def example_5_morse_code():
    """Demonstrate VCA as a gate to create morse code pattern for 'SOS'."""
    # Create a simple tone
    tone = SineOscillator(frequency=660, amplitude=0.7)  # E5 note

    # Create a square LFO with a pattern that represents "SOS" in Morse code
    # ... --- ...
    # Dot = 1/4 second, Dash = 3/4 second, Gap = 1/4 second
    # We'll create this by modulating the duty cycle of a very slow square wave

    # Base frequency for timing (4 Hz gives us 1/4 second units)
    timing_base = 4

    # Create separate oscillators for S and O patterns
    s_pattern = SquareOscillator(
        frequency=timing_base / 9,  # Complete S pattern takes 9 quarter-seconds
        duty_cycle=0.33,  # 3/9 = 0.33 duty cycle for three short pulses
    )

    o_pattern = SquareOscillator(
        frequency=timing_base / 9,  # Complete O pattern takes 9 quarter-seconds
        duty_cycle=0.66,  # 6/9 = 0.66 duty cycle for three long pulses
    )

    # Mix the patterns
    pattern_mixer = Mixer()
    pattern_mixer.add_input(s_pattern, gain=1.0)
    # Delay the O pattern by adding silence at the start
    pattern_mixer.add_input(o_pattern, gain=1.0)

    # Use VCA as a gate
    vca = VCA(tone)
    vca.set_cv_input(pattern_mixer)

    # Add a bit of filtering to smooth out the clicks
    filter_module = Filter(FilterType.LOWPASS, cutoff_freq=4000)
    filter_module.set_input(vca)

    # Create audio output
    output = AudioOutput(filter_module)

    print("Playing Morse code demonstration...")
    print("- 660 Hz sine wave")
    print("- Gated to produce SOS pattern")
    print("- ... --- ...")
    output.start(duration=10)
