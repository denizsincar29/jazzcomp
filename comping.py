# comping.py
from bass import ChordProgression
from notes_with_octaves import NoteWithOctave
from harmony import Chord
from chordparser import Note

class JazzComping:
    def __init__(self, progression: ChordProgression):
        self.progression = progression
        self.comping_result: list[list[NoteWithOctave]] = []

    def _get_chord_tones(self, chord: Chord, duration: int, base_octave: int = 3) -> list[NoteWithOctave]:
        """
        Generates a basic voicing (root, 3rd, 5th, 7th) for a given chord
        with adjusted octave placement for better spread.
        Sets the length attribute of each NoteWithOctave to the given duration.
        """
        tones = []

        if not chord.root:
            return []

        # Root
        current_octave_for_root = base_octave
        root_note_obj = NoteWithOctave(chord.root, current_octave_for_root, length=duration)
        tones.append(root_note_obj)

        last_note_abs_value = chord.root.num_value() # Absolute note value (0-11) for octave decisions
        current_max_octave = current_octave_for_root

        # Third
        quality_str = str(chord.quality).lower()
        if "sus" not in quality_str:
            third_note_base = None
            if hasattr(chord, 'third') and isinstance(chord.third, Note):
                third_note_base = chord.third
            else:
                is_minor_quality = hasattr(chord.quality, 'is_minor') and chord.quality.is_minor
                is_major_quality = ((hasattr(chord.quality, 'quality_str') and chord.quality.quality_str == "" and not is_minor_quality) or
                                    ("maj" in quality_str and "maj7" not in quality_str))
                if is_major_quality or ("maj" in quality_str and "m" not in quality_str):
                    third_note_base = chord.root.transpose(4)
                elif "min" in quality_str or "dim" in quality_str or is_minor_quality:
                    third_note_base = chord.root.transpose(3)
                elif "7" in quality_str and "sus" not in quality_str and "m" not in quality_str and "dim" not in quality_str:
                    third_note_base = chord.root.transpose(4)
                else:
                    third_note_base = chord.root.transpose(4)

            if third_note_base:
                current_octave_for_third = current_max_octave
                if third_note_base.num_value() < last_note_abs_value:
                    current_octave_for_third += 1

                tones.append(NoteWithOctave(third_note_base, current_octave_for_third, length=duration))
                last_note_abs_value = third_note_base.num_value()
                current_max_octave = max(current_max_octave, current_octave_for_third)

        # Fifth
        fifth_note_base = None
        is_dim_quality = "dim" in quality_str or "ø" in quality_str or                          (hasattr(chord.quality, 'quality_str') and chord.quality.quality_str == "o")

        if hasattr(chord, 'fifth') and isinstance(chord.fifth, Note):
            fifth_note_base = chord.fifth
        elif is_dim_quality:
            fifth_note_base = chord.root.transpose(6) # b5 for diminished
        else:
            fifth_note_base = chord.root.transpose(7) # Perfect 5th otherwise

        if fifth_note_base:
            current_octave_for_fifth = current_max_octave
            # Try to place 5th above or same octave as last note (root or 3rd)
            if fifth_note_base.num_value() < last_note_abs_value and current_octave_for_fifth == base_octave : # if third was in base_octave
                 current_octave_for_fifth = base_octave + 1 # try pushing 5th higher
            elif fifth_note_base.num_value() < last_note_abs_value : # if third was already an octave higher
                 current_octave_for_fifth +=1


            # Ensure it's not too low compared to root if 3rd was skipped (sus)
            if "sus" in quality_str and fifth_note_base.num_value() < chord.root.num_value():
                 current_octave_for_fifth = base_octave + 1


            tones.append(NoteWithOctave(fifth_note_base, current_octave_for_fifth, length=duration))
            last_note_abs_value = fifth_note_base.num_value()
            current_max_octave = max(current_max_octave, current_octave_for_fifth)

        # Seventh
        quality_str_for_check = str(chord.quality)
        seventh_exists_in_quality = ("7" in quality_str_for_check or "dim" in quality_str_for_check or
                                     "ø" in quality_str_for_check or
                                     (hasattr(chord.quality, 'quality_str') and chord.quality.quality_str == "o"))

        if seventh_exists_in_quality:
            seventh_note_base = None
            if hasattr(chord, 'seventh') and isinstance(chord.seventh, Note):
                seventh_note_base = chord.seventh
            else:
                if "maj7" in quality_str_for_check:
                    seventh_note_base = chord.root.transpose(11)
                elif "dim7" in quality_str_for_check or                      (hasattr(chord.quality, 'quality_str') and chord.quality.quality_str == "o7"):
                    seventh_note_base = chord.root.transpose(9)
                elif (("dim" in quality_str_for_check and "dim7" not in quality_str_for_check and "ø" not in quality_str_for_check and                        not (hasattr(chord.quality, 'quality_str') and chord.quality.quality_str == "o")) or                       (hasattr(chord.quality, 'quality_str') and chord.quality.quality_str == "o" and "7" not in quality_str_for_check)):
                    pass # No 7th for simple dim triad
                else:
                    seventh_note_base = chord.root.transpose(10)

            if seventh_note_base:
                current_octave_for_seventh = current_max_octave # Start from highest octave so far
                # Generally place 7th higher
                if seventh_note_base.num_value() < last_note_abs_value :
                    current_octave_for_seventh += 1
                elif current_octave_for_seventh == base_octave: # If all notes so far are in base_octave
                    current_octave_for_seventh = base_octave + 1


                tones.append(NoteWithOctave(seventh_note_base, current_octave_for_seventh, length=duration))

        # Sort by MIDI value to ensure notes are in ascending pitch order in the final voicing list (optional)
        # tones.sort(key=lambda n: n.to_midi())
        return tones

    def generate_comping(self) -> list[list[NoteWithOctave]]:
        """
        Generates jazz comping with varied rhythms.
        """
        self.comping_result = []

        try:
            expanded_items = list(self.progression)
        except Exception as e:
            print(f"Error expanding progression in JazzComping: {e}")
            return []

        if not expanded_items:
            return []

        for item in expanded_items:
            if item.is_chord and item.chord is not None:
                original_duration = item.duration

                if original_duration <= 0:
                    continue

                # Get the basic voicing using the original duration for context if needed by _get_chord_tones,
                # though _get_chord_tones primarily uses duration to set the length on the notes it returns.
                base_voicing = self._get_chord_tones(item.chord, original_duration, octave=3)

                if not base_voicing:
                    continue

                if original_duration == 4.0:
                    # Hit 1 (e.g., on beat 1, duration 2.5)
                    voicing_hit1 = []
                    for note_template in base_voicing:
                        note_copy = NoteWithOctave(note_template.note, note_template.octave, length=2.5)
                        voicing_hit1.append(note_copy)
                    self.comping_result.append(voicing_hit1)

                    # Hit 2 (e.g., on 'and' of beat 3, duration 1.5)
                    voicing_hit2 = []
                    for note_template in base_voicing:
                        note_copy = NoteWithOctave(note_template.note, note_template.octave, length=1.5)
                        voicing_hit2.append(note_copy)
                    self.comping_result.append(voicing_hit2)

                elif original_duration == 3.0: # Example: dotted half
                    # Hit 1 (e.g., on beat 1, duration 2.0)
                    voicing_hit1 = []
                    for note_template in base_voicing:
                        note_copy = NoteWithOctave(note_template.note, note_template.octave, length=2.0) # Could be 1.5
                        voicing_hit1.append(note_copy)
                    self.comping_result.append(voicing_hit1)

                    # Hit 2 (e.g., on beat 3, duration 1.0)
                    voicing_hit2 = []
                    for note_template in base_voicing:
                        note_copy = NoteWithOctave(note_template.note, note_template.octave, length=1.0) # Could be 1.5
                        voicing_hit2.append(note_copy)
                    self.comping_result.append(voicing_hit2)

                elif original_duration == 2.0:
                    # Hit 1 (on beat 1, duration 1.0)
                    voicing_hit1 = []
                    for note_template in base_voicing:
                        note_copy = NoteWithOctave(note_template.note, note_template.octave, length=1.0)
                        voicing_hit1.append(note_copy)
                    self.comping_result.append(voicing_hit1)

                    # Hit 2 (on beat 2, duration 1.0)
                    voicing_hit2 = []
                    for note_template in base_voicing:
                        note_copy = NoteWithOctave(note_template.note, note_template.octave, length=1.0)
                        voicing_hit2.append(note_copy)
                    self.comping_result.append(voicing_hit2)

                else: # Default: one hit with original duration (covers 1.0, 1.5, 0.5, etc.)
                    final_voicing = []
                    for note_template in base_voicing:
                        note_copy = NoteWithOctave(note_template.note, note_template.octave, length=original_duration)
                        final_voicing.append(note_copy)
                    self.comping_result.append(final_voicing)

        return self.comping_result
