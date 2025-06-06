# Algorithm to generate a swing jazz bass line for a given chord progression

Bass line is usually a quarter note sequence that is nearly always deterministic and requires just a few things to be randomized.
This algorithm generates a bass line for a given chord progression using the following steps:
1. pairwise iterate over the chords in the progression and get first chord's bit length (The length in quarters).
2. Play the first note, usually the root note, or rarer the third or fifth note of the chord
3. Now play the note that's the closest in the scale, more rarely play a note in an arpegio, and more rarely a random note in the scale.
4. If it's the last note in the chord's time, search and play one of the most gravitating notes to the next chords root, or rarer the third or fifth note of the next chord.
5. Go to the next chord and repeat from step 2.

In step 3, Sometimes if there is an enough bit space, we can play a note that's gravitating to the root or the third or fifth note of the next chord. This is a rare case, but it can be used to create a more interesting bass line.
If the chord is not changing for 2 or more bars, we can randomly (5% chance) play a 3/8 ostinato on the root note. (todo, only if the rest algorithm works well, we can consider this)
There must be an octave limit for the next note generation to omit too high or too low notes from the random generation. The lowest note is f1 and the highest note is g3. Implement octave movements correctly.
rarely (10% chance) we can make a jump to more than a fifth or a sixth, but this is not common.
In 20% cases we can add an eight sinkop but only if this note is one of 1, 3 or 5.
In 20% cases we can play a half note, but only if this note is one of 1, 3 or 5.

## notes:
- Gravitating notes are not just the chromatically closest notes, but sometimes next notes in the scale. And the fifth note gravitates to the root of the same chord.
- Arpegio is usually an 1 3 5 sequence.