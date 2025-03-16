# bleepbloops

Tinkering project for understanding sound synthesis fundamentals

# Summary

I want to build a system that lets me explore sound synthesis. The first thing I'd like to start with is a sine wave generator that can be sent to an output function that plays the sound through my speakers at a set volume.

The system should be designed in a modular way so that in the future, for example, I could send the sine wave generator through a low pass filter and then send that filtered output to the output system.
Additionally the modularity should allow for modifying the frequency, amplitude and other paramters of the sine wave generator. For example, if I connect one sine wave generator output to the amplitude parameter input of another sine wave generator, the amplitude should be modified by the input of the first sine wave generator.

Lastly, I want a mixer module that allows me to combine multiple signals together into a single output that I can then send to the output module for playing sound.

Also I want to consider the most efficent way to simulate timesteps so that all the modules can be synced properly, even if someone is running this code on a different system.

To summarize, I want to start with these modules:

- Sine wave module: Has input to modulate it's frequency and amplitude and outputs the resulting sine wave
- Filter module: Has input for the signal it's modulating and has settings to either be a low pass, high pass, or band pass filter.
- Mixer module: Allows combination of sound signals to a single output to send to the output module
- Output module: Has input for the final sound wave and plays the resulting sounds through the PC speakers.
