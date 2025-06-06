import random
import os

class Drum:
    def __init__(self, sound_spec):
        self.sound_spec = sound_spec

    def get(self):
        if isinstance(self.sound_spec, int):
            return f"sounds/{self.sound_spec}.wav"

        parts = []
        for element in self.sound_spec:
            if isinstance(element, int):
                parts.append(str(element))
            elif isinstance(element, tuple):
                parts.append(str(random.randint(element[0], element[1])))
            elif isinstance(element, list):
                parts.append(str(random.choice(element)))
        return "sounds/" + "_".join(parts) + ".wav"

    def __call__(self):
        fn = self.get()
        if os.path.exists(fn):
            return fn
        else:
            raise FileNotFoundError(f"Sound file {fn} does not exist.")

# Constants for drum sounds
big_drum = Drum([(1, 2)])
loud_clap = Drum([9, 1])
clap = Drum([9, 1, [1, 7]])
big_crash = Drum([[11, 12]])
t1 = Drum(15)
t2 = Drum(16)
t3 = Drum(17)
t4 = Drum(18)
t5 = Drum(19)
t6 = Drum(20)

pedal_hihat_close = Drum(22)
pedal_hihat_open = Drum(23)
quieter_hihats = Drum([[31, 32]])
c_hihats = Drum([[41, 46]])
o_hihats = Drum([[51, 54]])
small_buzzle = Drum([(61, 62)])
mid_buzzle = Drum([(71, 76)])
bam_bam = Drum([(81, 86)])
drum_side = Drum([(131, 138)])
sticks = Drum([(141, 145)])
sticks2 = Drum([(261, 267)])
ride1 = Drum([(211, 215)])
half_closed_hat = Drum([(231, 234)])