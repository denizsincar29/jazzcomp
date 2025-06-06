from pydub import AudioSegment

class AudioCombiner:
    def __init__(self, tempo: int=120, ts: int=4):
        self.cache = {}
        self.main_audio = AudioSegment.silent(duration=0)
        self.set_tempo(tempo)
        self.ts=ts
    
    def set_tempo(self, tempo: int):
        self.tempo = tempo
        self.quarter_duration = 60000 / tempo  # in millis
    
    def place_at(self, file_path: str, measure: int, quarter: float, multiplet_num: int =0, multiplet_din: int=3, volume_step: float = 0.0):
        # Calculate start time in milliseconds
        start_time = int((measure * self.ts + quarter) * self.quarter_duration)
        if multiplet_num >0:
            start_time += int(self.quarter_duration * multiplet_num / multiplet_din)
        
        # Load audio file (use cache if available)
        if file_path not in self.cache:
            self.cache[file_path] = AudioSegment.from_file(file_path) + volume_step
        
        sound = self.cache[file_path]
        
        # add silence if needed:
        overlayed_sound_end_pos = start_time + len(sound)
        if len(self.main_audio) < overlayed_sound_end_pos:
            silence_duration = overlayed_sound_end_pos - len(self.main_audio)
            self.main_audio += AudioSegment.silent(duration=silence_duration)
        # Overlay the sound at calculated position
        self.main_audio = self.main_audio.overlay(
            sound,
            position=start_time
        )
    
    def export(self, output_file: str, format: str ="wav"):
        self.main_audio.export(output_file, format=format)