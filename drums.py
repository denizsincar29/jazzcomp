import math
import random
import drum_sounds as ds
import sound_combiner as sc  # for sound combining functionality

class DrumPattern:
    def __init__(self, tempo=120, num_quarters=4):
        self.tempo = tempo
        self.num_quarters = num_quarters  # Quarters per measure (e.g., 4 for 4/4)
        self.quarter_length = 1.0 / (self.tempo / 60)
        self.swing_factor = 0.67  # Not directly used in this create_pattern, but combiner might use it
        self.combiner = sc.AudioCombiner(self.tempo, self.num_quarters)

    def add(self, file_path, measure, quarter, multiplet_num=0, multiplet_din=3):
        """
        Adds a sound to the pattern.
        measure: 1-indexed measure number.
        quarter: 1-indexed quarter note within the measure.
        multiplet_num: The Nth note in a group of 'multiplet_din' notes dividing the quarter.
                       e.g., for 8th notes (2 per quarter):
                       - (quarter, 0, 2) for the first 8th (on the beat)
                       - (quarter, 1, 2) for the second 8th (the 'and')
                       Default (0,3) is for the first note of a triplet.
        """
        self.combiner.place_at(file_path, measure, quarter, multiplet_num, multiplet_din)

    def _get_placement_params(self, eighth_note_index_song):
        """
        Calculates measure, quarter, and multiplet parameters for self.add
        based on a global 8th note index.
        """
        # barlen_8th: number of 8th notes in a bar.
        barlen_8th = self.num_quarters * 2
        
        measure = eighth_note_index_song // barlen_8th
        
        eighth_note_in_bar = eighth_note_index_song % barlen_8th
        
        # Convert 8th note position in bar to quarter note and 8th note within quarter
        quarter = (eighth_note_in_bar / 2)
        return measure, quarter

    def create_pattern(self, bars=4):
        # barlen_8th: number of 8th notes in a bar.
        # Assumes self.num_quarters defines the measure (e.g., 4 for 4/4 time).
        barlen_8th = self.num_quarters * 2 
        songlen_8th = bars * barlen_8th  # Total number of 8th notes in the song

        # Define sound generating functions from drum_sounds module
        bass_sound = ds.big_drum
        ride_sound = ds.ride1 
        hihat_sound = ds.c_hihats # Using c_hihats for typical closed hi-hat sounds
        snare_sound = ds.small_buzzle
        for i in range(songlen_8th):  # i is the global 8th note index, 0-indexed
            # Get placement parameters for the current 8th note i
            m, q = self._get_placement_params(i)
            mn = 0  # Multiplet number, default to 0
            md = 3
            
            # eighth_note_in_bar_0idx: 0-indexed 8th note position within the current bar
            eighth_note_in_bar_0idx = i % barlen_8th

            is_odd_beat_start = (eighth_note_in_bar_0idx % 4 == 0) 
            is_even_beat_start = (eighth_note_in_bar_0idx % 4 == 2)
            is_first_syncopation = (eighth_note_in_bar_0idx % 4 == 1)
            is_second_syncopation = (eighth_note_in_bar_0idx % 4 == 3)
            if is_first_syncopation or is_second_syncopation:
                q += self.swing_factor - 0.5  # Adjust for swing on syncopated beats

            if eighth_note_in_bar_0idx == 0: # Very first 8th note of the bar
                self.add(bass_sound(), m, q, mn, md)
            if is_odd_beat_start: # Start of Q1, Q3
                self.add(ride_sound(), m, q, mn, md)
            
            if is_even_beat_start: # Start of Q2, Q4
                self.add(ride_sound(), m, q, mn, md)
                self.add(hihat_sound(), m, q, mn, md)
            
            if is_second_syncopation and random.random() < 0.9: # 'And' of Q2, 'And' of Q4
                self.add(ride_sound(), m, q, mn, md)

            # Snare on syncopated beats (general probability)
            if (is_first_syncopation or is_second_syncopation) and random.random() < 0.2:
                self.add(snare_sound(), m, q, mn, md)
            
            # Specific snare probabilities based on a new random roll
            rprob = random.random()
            if (is_first_syncopation or is_second_syncopation) and rprob < 0.05: # Double hit
                qq = math.ceil(q)
                self.add(snare_sound(), m, q, mn, md)
                self.add(snare_sound(), m, qq, mn, md) # Add snare twice

            if (is_first_syncopation or is_second_syncopation) and 0.20 <= rprob <= 0.30:
                self.add(snare_sound(), m, q, mn, md) 

def main():
    pattern = DrumPattern(tempo=180, num_quarters=4) 
    pattern.create_pattern(bars=16)
    pattern.combiner.export("drum_pattern.wav", format="wav")

if __name__ == "__main__":
    main()