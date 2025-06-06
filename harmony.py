from chordparser import Chord, Scale, Note, Quality, Parser
from notes_with_octaves import NoteWithOctave
import random
from copy import deepcopy as dc

# This chord parser thingy is a bit of a mess, but it works for now
FLAT = '♭'
SHARP = '♯'
LOWER_BOUND = 30  # lower than this, bass notes are not supposed to be played
UPPER_BOUND = 55  # same for upper bound

def get_semitone_of_degree(c: Chord, degree: int) -> int:
    natural_degree_semis = [0, 2, 4, 5, 7, 9, 11]  # if we asume major scale
    degs = [i % 7 for i in c.degrees if i in [9, 11, 13]]  # 9, 11 etc converted to 2, 4 etc
    if degree in degs:
        deg_idx = degs.index(degree)
        sym = c.symbols[deg_idx]
        if sym == FLAT:
            return natural_degree_semis[degree-1] - 1
        elif sym == SHARP:
            return natural_degree_semis[degree-1] + 1
        else:
            return natural_degree_semis[degree-1]
    # but, sometimes we have this degree not specified, so we assume it's default
    return natural_degree_semis[degree-1]

# i guess we need to manually convert the chord to a scale
def chord_to_scale(p: Parser, c: Chord) -> list[Note]:  # built-in scales are not so versatile
    root: Note = c.root
    q = str(c.quality)
    if "dim" in q:
        d = [0, 2, 3, 5, 6, 8, 9, 11]
        return [dc(root).transpose_simple(i, True) for i in d]
    # in suses we're not supposed to play 3rd!
    degree_range = [1, 2, 3, 4, 5, 6, 7] if not "sus" in q else [1, 2, 4, 5, 6, 7]
    s = [get_semitone_of_degree(c, i) for i in degree_range]
    return [dc(root).transpose_simple(i, True) for i in s]  # this stupid thing modifies the root even if returning!

def degree_string_to_semitone(degree: str) -> int:
    natural_degree_semis = [0, 2, 4, 5, 7, 9, 11]  # if we asume major scale
    accidental = 0
    if "#" in degree:
        accidental = 1
    elif "b" in degree:
        accidental = -1
    degree = degree.replace("#", "").replace("b", "")
    if degree.isdigit():
        return int(degree) - 1 + accidental
    return natural_degree_semis[int(degree) - 1] + accidental

def get_gravitating_notes(c: Chord) -> list[Note]:
    qualstr = str(c.quality)
    is_dominant = qualstr in ["7", "9", "11", "13"]
    is_maj = "maj" in qualstr
    is_min = "m7" in qualstr and "m7b5" not in qualstr
    #is_hdim = "m7b5" in qualstr
    #is_dim = "dim" in qualstr
    # print all properties we got:
    #print(f"Chord: {c}, is_dominant: {is_dominant}, is_maj: {is_maj}, is_min: {is_min}")
    notes = []
    # in 7, major7 and minor7 without b5 we use -1th semitone from root and 7th semitone from root:
    if is_dominant or is_maj or is_min:
        notes.append(dc(c.root).transpose_simple(-1, True))
        notes.append(dc(c.root).transpose_simple(7, True))
    # in 7, we can use +1 semitone from root:
    if is_dominant:
        notes.append(dc(c.root).transpose_simple(1, True))
        print(f"root: {c.root}, notes: {notes}")
    # in major7, we can use 2nd and 4th semitones
    if is_maj:
        notes.append(dc(c.root).transpose_simple(2, True))
        notes.append(dc(c.root).transpose_simple(4, True))
    # in minor7, we can use -2nd semitone
    if is_min:
        notes.append(dc(c.root).transpose_simple(-2, True))
    #return list(set(notes))  # unhashable!
    return_res = []
    for note in notes:
        if note not in return_res:
            return_res.append(note)
    return return_res


def generate_bass_bar(quarters: int, c: Chord, d: Chord, n: NoteWithOctave = None) -> list[Note]:
    scale = chord_to_scale(Parser(), c)
    notes = [NoteWithOctave(c.root, 2) if n is None else n]
    # we need to have quarters number of notes
    while len(notes) < quarters-1:
        current_note = notes[-1]
        next_note = current_note
        while next_note==current_note or not next_note.is_in_bounds(LOWER_BOUND, UPPER_BOUND):
            # we can use the scale to generate the next note
            next_note = current_note.go_in_scale(scale, random.randint(-2, 2))
            # if the next note is way too low or too high, we need to go in scale until we find a valid note
            while not next_note.is_in_upper_bound(UPPER_BOUND):
                next_note = next_note.go_in_scale(scale, -1)
            while not next_note.is_in_lower_bound(LOWER_BOUND):
                next_note = next_note.go_in_scale(scale, 1)

        notes.append(next_note)
        print(f"Number of notes: {len(notes)}, current note: {current_note}, next note: {next_note}")

    current_note = notes[-1]  # because local variable went out of scope
    gravinotes_to_next_root = get_gravitating_notes(d)
    closest_gravinote = current_note.get_closest_note(gravinotes_to_next_root, LOWER_BOUND,UPPER_BOUND)
    if closest_gravinote is None:
        # print the code, all gravinotes and the current note
        print(f"Current note: {current_note}, gravinotes: {gravinotes_to_next_root}, current chord: {c}, next chord: {d}")
        raise ValueError("No gravitating notes found for the next chord root.")
    # lets append it to notes list
    notes.append(closest_gravinote)
    # and lets append the root of the next chord:
    next_root = closest_gravinote.get_closest_note([d.root])  # to not make jumps e.g. from b3 to c3, just because it's same octave
    notes.append(next_root)
    print(f"Notes length: {len(notes)}, quarters: {quarters}, current note: {current_note}, next root: {next_root}")
    return notes  # it's non sense to continue, we already have enough notes