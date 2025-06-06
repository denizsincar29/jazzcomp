import pytest

from chordparser import Parser
from notes_with_octaves import NoteWithOctave

midi_values_to_each_octave = [
    (0, "C", -1),
    (12, "C", 0),
    (24, "C", 1),
    (36, "C", 2),
    (48, "C", 3),
    (60, "C", 4),
    (72, "C", 5),
    (84, "C", 6),
    (96, "C", 7),
    (108, "C", 8),
    (120, "C", 9),
]

from_c_values_to_notes = [
    (0, "C"),
    (1, "D♭"),
    (2, "D"),
    (3, "E♭"),
    (4, "E"),
    (5, "F"),
    (6, "G♭"),
    (7, "G"),
    (8, "A♭"),
    (9, "A"),
    (10, "B♭"),
    (11, "B"),
]

# All MIDI notes and their corresponding octaves
# from 0 to 127
all_midi_notes_and_octaves = [
    (i, from_c_values_to_notes[i % 12][1], (i // 12) - 1) for i in range(128)
]

f_major_scale = [
    Parser().create_note("F"),
    Parser().create_note("G"),
    Parser().create_note("A"),
    Parser().create_note("B♭"),
    Parser().create_note("C"),
    Parser().create_note("D"),
    Parser().create_note("E"),
]

@pytest.mark.parametrize("midi, expected_note, expected_octave", midi_values_to_each_octave)
def test_from_midi(midi, expected_note, expected_octave):
    note_with_octave = NoteWithOctave.from_midi(midi)
    assert str(note_with_octave) == f"{expected_note}{expected_octave}"
    assert note_with_octave.note.letter == expected_note
    assert note_with_octave.octave == expected_octave

@pytest.mark.parametrize("midi, note, octave", all_midi_notes_and_octaves)
def test_to_midi(midi, note, octave):
    note = Parser().create_note(note)
    note_with_octave = NoteWithOctave(note=note, octave=octave)
    assert note_with_octave.to_midi() == midi

# test transpose
@pytest.mark.parametrize("midi, semitones, expected_midi", [
    (60, 0, 60),  # C4
    (60, 12, 72),  # C5
    (60, -12, 48),  # C3
    (60, 1, 61),  # C#4
    (60, -1, 59),  # B3
])
def test_transpose(midi, semitones, expected_midi):
    note_with_octave = NoteWithOctave.from_midi(midi)
    transposed = note_with_octave.transpose(semitones)
    assert transposed.to_midi() == expected_midi

# test move in f major scale
@pytest.mark.parametrize("note, octave, steps, expected_note, expected_octave", [
    ("F", 4, 0, "F", 4),  # F4 stays F4
    ("F", 4, 1, "G", 4),  # F4 goes to G4
    ("F", 4, -1, "E", 4),  # F4 goes to E4
    ("F", 4, 2, "A", 4),  # F4 goes to A4
    ("F", 4, -2, "D", 4),  # F4 goes to D4
    ("G", 4, 10, "C", 6)
])
def test_go_in_scale(note, octave, steps, expected_note, expected_octave):
    note_with_octave = NoteWithOctave(note=Parser().create_note(note), octave=octave)
    new_note_with_octave = note_with_octave.go_in_scale(f_major_scale, steps)
    assert str(new_note_with_octave) == f"{expected_note}{expected_octave}"
    assert new_note_with_octave.note.letter == expected_note
    assert new_note_with_octave.octave == expected_octave