from bass import ChordProgression
from comping import JazzComping
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

print("\n--- Generating Jazz Comping ---")
comping_generator = JazzComping(prog)
comping_voicings = comping_generator.generate_comping()

comping_stream = stream.Stream()
piano = instrument.Piano()
comping_stream.insert(0, piano) # Add piano instrument
# Optionally, add dynamics like for bass
# comping_stream.insert(0, dynamics.Dynamic("mf"))

for voicing in comping_voicings:
    if not voicing: # Skip if the voicing is empty
        continue

    # Extract MIDI numbers for the chord
    midi_numbers = [note.to_midi() for note in voicing]
    # Get duration from the first note in the voicing (all should be same)
    # music21 duration is in quarter notes, which note.length already is.
    duration_quarters = voicing[0].length

    if not midi_numbers: # Skip if no MIDI numbers (e.g. empty voicing somehow)
        continue

    m21_chord_obj = m21_chord.Chord(midi_numbers)
    m21_chord_obj.duration.quarterLength = duration_quarters
    comping_stream.append(m21_chord_obj)

print(f"Generated comping with {len(comping_voicings)} voicings.")
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

if comping_stream.hasMeasures(): # music21 might create empty streams otherwise
    comping_stream.write('musicxml', fp='test_comping_line.xml')
    print("Wrote comping to test_comping_line.xml")
    # Call MuseScore to convert to WAV
    try:
        subprocess.run([msc_path, 'test_comping_line.xml', '-o', 'test_comping_line.wav'], check=True)
        print("Converted comping XML to test_comping_line.wav")
    except FileNotFoundError:
        print(f"Error: MuseScore path '{msc_path}' not found. Please ensure MuseScore is installed and msc_path is correct.")
    except subprocess.CalledProcessError as e:
        print(f"Error during MuseScore conversion for comping: {e}")
else:
    print("Comping stream is empty or invalid, skipping XML/WAV generation.")
drums = DrumPattern(tempo=120, num_quarters=4)
drums.create_pattern(12)
drums.combiner.place_at('test_bass_line.wav', 0, 0, volume_step=10.0)  # Place bass line in measure 1, quarter 1
if os.path.exists('test_comping_line.wav'):
    drums.combiner.place_at('test_comping_line.wav', 0, 0, volume_step=8.0) # Using a slightly lower volume for comping initially
    print("Added comping WAV to the mix.")
else:
    print("Comping WAV file not found, skipping its addition to the mix.")
drums.combiner.export('test_song_with_drums.wav')