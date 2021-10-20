from __future__ import division
from __future__ import print_function

from psychopy import visual, event, core
from math import tan, pi

# monitor specs global variables
M_WIDTH = 1920
M_WIDTH_CM = 51.84
M_HEIGHT = 1200
REFRESH_RATE = 60

my_dpi = 96 # dpi of the lab monitor
distance = 60 # distance to screen in cm

dotsSpeed = 0.01

def degrees_to_pix(degrees):
    cm = tan(degrees * pi / 180) * distance
    pix = cm * M_WIDTH / M_WIDTH_CM
    print(pix)
    return pix

class stim:
    def __init__(self, window, xoffset):
        #size of the fixation cross
        self.fixationSize = degrees_to_pix(0.36)
        
        # dot patch
        self.dotPatch = visual.DotStim(window, color=(1.0, 1.0, 1.0), dir=180, units="pix",
                                       nDots=328, fieldShape='circle', fieldPos=[0 + xoffset, 0], fieldSize=199,
                                       dotLife=5,  # number of frames for each dot to be drawn
                                       signalDots='same',  # are signal dots 'same' on each frame? (see Scase et al)
                                       noiseDots='direction',
                                       # do the noise dots follow random- 'walk', 'direction', or 'position'
                                       speed=dotsSpeed, coherence=0.9)

        # light blue fixation cross for pretrial & decision interval
        self.bluecross = visual.GratingStim(
            win=window, size=self.fixationSize, units='pix', pos=[0 + xoffset, 0],
            sf=0, color='blue', mask='cross'
        )

        # red fixation cross for feedback interval
        self.redcross = visual.GratingStim(
            win=window, size=self.fixationSize, units='pix', pos=[0 + xoffset, 0],
            sf=0, color='red', mask='cross'
        )

        # green fixation cross for feedback interval
        self.greencross = visual.GratingStim(
            win=window, size=self.fixationSize, units='pix', pos=[0 + xoffset, 0],
            sf=0, color='green', mask='cross'
        )
        
        """
        For response time related warning to be shown on top of fixation cross
        a. if response time < 100 ms: Too Fast
        b. response time > 1500 ms: Too Slow
        """
        self.indicatordict = {
            "slow": visual.TextStim(
                win=window, text="Too Slow", units='pix', pos=[0 + xoffset, 0], color='red'
            ),
            "fast": visual.TextStim(
                win=window, text="Too Fast", units='pix', pos=[0 + xoffset, 0], color='red'
            )
        }
