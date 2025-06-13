from bass import ChordProgression
from music21 import stream, note as m21_note, chord as m21_chord, instrument, environment, dynamics
import subprocess
import os
from drums import DrumPattern

msc_path = environment.get("musicxmlPath")

test_song = """
@title Test Song with Sections and Events
*a
F7
Bb7 Bdim7
F7
F7b9
Bb7
Bdim7
F7
D7b9
G7
C7b9
F7 D7b9
G7 C7b9
"""
prog = ChordProgression.from_string(test_song)
print("\n--- Generating Bass Line ---")
bassline = prog.generate_bass_line()

# Comping generation and stream creation completely removed.

# Convert to a music21 stream for further processing or playback
bass_stream = stream.Stream()
# do bass instrument for the score
bass = instrument.AcousticBass()
fortissimo = dynamics.Dynamic("fff")
bass_stream.insert(0, fortissimo)
bass_stream.insert(0, bass)

for note in bassline:
    midi_number = note.to_midi()
    duration = note.length  # in quarters
    dur_name = "half" if duration == 4 else "quarter"
    bass_stream.append(m21_note.Note(midi_number, type=dur_name))
print(f"Generated bass line with {len(bassline)} notes.")
# write musicxml
bass_stream.write('musicxml', fp='test_bass_line.xml')
# call musescore to convert to wav
subprocess.run([msc_path, 'test_bass_line.xml', '-o', 'test_bass_line.wav'], check=True)

# Comping MusicXML/WAV conversion completely removed.

drums = DrumPattern(tempo=120, num_quarters=4)
drums.create_pattern(12)
drums.combiner.place_at('test_bass_line.wav', 0, 0, volume_step=10.0)  # Place bass line in measure 1, quarter 1
# Comping WAV addition to combiner completely removed.
drums.combiner.export('test_song_with_drums.wav')