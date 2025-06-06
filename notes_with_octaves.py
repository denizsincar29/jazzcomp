from chordparser import Note
from dataclasses import dataclass
from typing import Self

SHARP = '♯'
FLAT = '♭'

@dataclass
class NoteWithOctave:
    note: Note
    octave: int
    length: int = 2  # default length of the note, can be used for rhythm purposes

    def __str__(self):
        return f"{self.note}{self.octave}"

    def to_midi(self) -> int:
        note_number = self.note.num_value()
        # C4 is 12*5, so note C of N = 12*(n+1)
        return note_number + 12 * (self.octave + 1)

    @classmethod
    def from_midi(cls, midi: int) -> Self:
        note_number = midi % 12
        octave = (midi // 12) - 1
        notes = [Note("C", ""), Note("D", FLAT), Note("D", ""), Note("E", FLAT), 
                 Note("E", ""), Note("F", ""), Note("G", FLAT), Note("G", ""), 
                 Note("A", FLAT), Note("A", ""), Note("B", FLAT), Note("B", "")]
        return cls(note=notes[note_number], octave=octave)
    
    def transpose(self, semitones: int) -> Self:
        new_midi = self.to_midi() + semitones
        result = self.from_midi(new_midi)
        result.length = self.length  # keep the length of the note
        return result

    def go_in_scale(self, scale: list[Note], steps: int) -> Self:
        scale.sort(key=lambda n: n.num_value())  # because e.g. the f major scale starts with F, not C
        # scale is a list of notes, we need to find the index of the current note
        current_note = self.note
        current_index = scale.index(current_note)
        # calculate the new index
        target = (current_index + steps)
        octave_change = target // len(scale)
        new_index = target % len(scale)
        new_note = scale[new_index]
        return NoteWithOctave(note=new_note, octave=self.octave + octave_change, length=self.length)

    def semitone_distance(self, other: Note, lower_bound: int=-1, upper_bound: int=-1) -> int:
        # find the closest (other) note for the current note in this or neighboring octave
        current_midi = self.to_midi()
        others = [NoteWithOctave(other, self.octave)]
        # if current octave is >0, we append the note in the previous octave
        if self.octave > 0:
            others.append(NoteWithOctave(other, self.octave - 1))
        # if current octave is <10, we append the note in the next octave
        if self.octave < 10:
            others.append(NoteWithOctave(other, self.octave + 1))
        # find the closest note in terms of midi value
        others.sort(key=lambda n: abs(n.to_midi() - current_midi))
        # check bounds and return the one that is in bounds
        closest_note = others[0]
        if lower_bound>-1 or upper_bound>-1:
            for note in others:
                if (lower_bound == -1 or note.to_midi() >= lower_bound) and \
                    (upper_bound == -1 or note.to_midi() <= upper_bound):
                    closest_note = note
                    break
        return closest_note.to_midi() - current_midi

    def get_closest_note(self, notes: list[Note], lower_bound: int = -1, upper_bound: int = -1) -> Self | None:
        closest_notes = []
        for note in notes:
            semi_distance = self.semitone_distance(note, lower_bound, upper_bound)
            if semi_distance ==0:
                continue  # don't want repeating notes, thanks!
            closest_note = self.transpose(semi_distance)
            closest_notes.append((closest_note, semi_distance))
        closest_notes.sort(key=lambda x: abs(x[1]))
        # if bounds are set, return the first note that is in bounds
        if lower_bound != -1 or upper_bound != -1:
            for note, distance in closest_notes:
                if (lower_bound == -1 or note.to_midi() >= lower_bound) and \
                    (upper_bound == -1 or note.to_midi() <= upper_bound):
                    return note
            return None
        # otherwise return the closest note
        return closest_notes[0][0]


    def is_in_upper_bound(self, upper_bound: int) -> bool:
        return self.to_midi() <= upper_bound
    
    def is_in_lower_bound(self, lower_bound: int) -> bool:
        return self.to_midi() >= lower_bound
    
    def is_in_bounds(self, lower_bound: int, upper_bound: int) -> bool:
        return lower_bound <= self.to_midi() <= upper_bound
    
    def __eq__(self, other: 'NoteWithOctave') -> bool:
        return self.note == other.note and self.octave == other.octave