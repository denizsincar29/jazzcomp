from harmony import Chord, Parser, generate_bass_bar
from notes_with_octaves import NoteWithOctave

class ProgressionItem:
    def __init__(self, chord: Chord | None = None, duration: int = 0, event_data: str | None = None):
        if chord is not None and event_data is not None:
            raise ValueError("ProgressionItem cannot be both a chord and an event simultaneously.")
        if chord is None and event_data is None:
            raise ValueError("ProgressionItem must be either a chord or an event.")

        self.chord: Chord | None = chord
        self.duration: int = duration if chord is not None else 0
        self.event_data: str | None = event_data

    def __repr__(self):
        if self.is_chord:
            return f"ProgressionItem(chord: {self.chord}, duration: {self.duration}q)"
        elif self.event_data:
            return f"ProgressionItem(event: '{self.event_data}')"
        return "ProgressionItem(invalid)" # Should be unreachable

    @property
    def is_chord(self) -> bool:
        """Returns True if this item represents a chord."""
        return self.chord is not None

    @property
    def is_event(self) -> bool:
        """Returns True if this item represents an event (and not a chord)."""
        return self.event_data is not None and self.chord is None

    @property
    def section_name(self) -> str:
        """
        If this item's event_data is a section definition (*Name) or reference (**Name),
        returns the section name (e.g., "Name"). Otherwise, returns an empty string.
        """
        if self.is_event and self.event_data:
            if self.event_data.startswith("**"):
                return self.event_data[2:].strip()
            if self.event_data.startswith("*"):
                return self.event_data[1:].strip()
        return ""

    @property
    def is_section_definition_marker(self) -> bool:
        """True if this item is an event like '*SectionName'."""
        return self.is_event and \
               self.event_data is not None and \
               self.event_data.startswith("*") and \
               not self.event_data.startswith("**")

    @property
    def is_section_reference_marker(self) -> bool:
        """True if this item is an event like '**SectionName'."""
        return self.is_event and \
               self.event_data is not None and \
               self.event_data.startswith("**")

class ChordProgression:
    def __init__(self, items: list[ProgressionItem] = None):
        self.items: list[ProgressionItem] = items if items is not None else []

    def __repr__(self):
        return f"ChordProgression(raw_items_count={len(self.items)})" # Keep it concise

    def __len__(self):
        # Returns the length of the raw, unexpanded items.
        # For the length of the expanded sequence, one would do `len(list(prog_obj))`.
        return len(self.items)

    @classmethod
    def from_string(cls, string: str, default_bar_length_quarters: int = 4) -> "ChordProgression":
        p = Parser()
        progression = cls()

        for line_num, raw_line in enumerate(string.splitlines()):
            line = raw_line.strip()

            if not line or line.startswith("@"):
                continue

            if line.startswith("#"):
                event_text = line[1:].strip()
                progression.items.append(ProgressionItem(event_data=event_text))
            elif line.startswith("**"):
                progression.items.append(ProgressionItem(event_data=line))
            elif line.startswith("*"):
                progression.items.append(ProgressionItem(event_data=line))
            else:
                chord_strings = line.split()
                if not chord_strings:
                    continue

                num_chords_in_bar = len(chord_strings)
                current_bar_len = default_bar_length_quarters
                if current_bar_len <= 0:
                    current_bar_len = 1

                base_duration = current_bar_len // num_chords_in_bar
                remainder_quarters = current_bar_len % num_chords_in_bar

                durations = [(base_duration + 1) if i < remainder_quarters else base_duration
                             for i in range(num_chords_in_bar)]

                for i, chord_str in enumerate(chord_strings):
                    chord_obj = None
                    try:
                        chord_obj = p.create_chord(chord_str)
                    except Exception as e:
                        print(f"Warning: Chord parsing error for '{chord_str}' on line {line_num+1}: {e}. Treating as rest.")

                    progression.items.append(ProgressionItem(chord=chord_obj, duration=durations[i]))
        return progression

    def _get_section_content_items(self, target_section_name: str) -> list[ProgressionItem]:
        content: list[ProgressionItem] = []
        in_section_definition = False
        for item in self.items: # Iterate over raw, unexpanded items
            if item.is_section_definition_marker:
                defined_name = item.section_name
                if defined_name == target_section_name:
                    if in_section_definition:
                        break
                    in_section_definition = True
                    continue
                elif in_section_definition:
                    break
            if in_section_definition:
                content.append(item)
        return content


    def __iter__(self):
        for item in self.items:
            if item.is_section_reference_marker:
                section_name = item.section_name
                section_content = self._get_section_content_items(section_name)
                if not section_content:
                    print(f"Warning: Section '{section_name}' referenced but not defined or empty.")
                yield from section_content
            else:
                yield item

    def generate_bass_line(self) -> list[NoteWithOctave]:
        final_bass_line: list[NoteWithOctave] = []
        expanded_items = list(self) # Uses the __iter__ method for expansion

        for i, item in enumerate(expanded_items):
            if not item.is_chord or item.duration == 0:
                continue

            current_actual_chord = item.chord

            next_chord_for_generator: Chord | None = None
            for j in range(i + 1, len(expanded_items)):
                future_item = expanded_items[j]
                if future_item.is_chord and future_item.duration > 0:
                    next_chord_for_generator = future_item.chord
                    break

            if next_chord_for_generator is None:
                first_playable_chord_item = next((it for it in expanded_items if it.is_chord and it.duration > 0), None)
                next_chord_for_generator = first_playable_chord_item.chord if first_playable_chord_item else current_actual_chord

            last_note_obj_for_generator: NoteWithOctave | None = final_bass_line[-1] if final_bass_line else None

            bass_segment = generate_bass_bar(item.duration, current_actual_chord, next_chord_for_generator, last_note_obj_for_generator)

            if not bass_segment:
                continue

            if final_bass_line:
                
                if last_note_obj_for_generator is None or bass_segment[0] != last_note_obj_for_generator:
                    print(f"Warning: Bass line connection issue for chord {current_actual_chord}. "
                          f"Expected start: {last_note_obj_for_generator}, Got: {bass_segment[0]}. Appending full segment.")
                    final_bass_line.extend(bass_segment)
                else:
                    final_bass_line.extend(bass_segment[1:] if bass_segment else []) # Ensure bass_segment[1:] is safe
            else:
                final_bass_line.extend(bass_segment)
        return final_bass_line

