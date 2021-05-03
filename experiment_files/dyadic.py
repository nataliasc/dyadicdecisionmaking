# 11 April 2021

'''
    Naming Convention:
        The subjects are either refered to as 'sone' or 'stwo'
        The variables for each are prepended with `sone_` or `stwo_`

    To Do:
        - There is significant delay in stimulus display. Need to test if it still applies on the lab computer
        - The data needs to be packaged properly using the experiment handler
        - There is a warning that a providing data file can prevent data loss in case of crash. Is it writing to the disk and should we have this?
        - Instruction, thank you and break screens are missing
        - There is no mechanism to input subject ids
        - How do we decide to alternate between act and obs conditions
        - There is only a blue dot denote the observation condition, needs and update based on what Artur says
        - Figure out the right way to traverse through the experiment handlers set of trials
        - How do we switch from dyadic to individual condition when both are acting
        - Figure out how to exactly fetch input form different button boxes. The rusocsci library seems promising
        - Do we have manually send the two screens to the two monitors or can this be automated
        - How do we send the same beep to two speakers which are far apart? Do we have a splitter at the lab computer? How do we feel about the lag introduced by the splitter?
        - In the individual trials, how do we send the beep to different headphones the two subjects have? We will need USB headphone and write to their USB directly.
        - Do we have speakers of headphones? Do we need headphones because the other subject might head the beep
'''
from typing import Any, Callable

import os
import sys
from subprocess import run
import numpy as np
import psychtoolbox as ptb
from psychopy import visual, event, core, gui, data, prefs

# setting PTB as our preferred sound library and then import sound

'''
To obtain your sounddevices run
from psychopy.sound.backend_sounddevice import getDevices
getDevices()
Copy the `name` attribute of your device to the audioDevice
'''

prefs.hardware['audioLib'] = ['PTB']

from psychopy import sound
sound.setDevice('Logitech USB Headset: Audio (hw:2,0)')

from psychopy.sound import Sound
from numpy.random import random

# subject ids global variables
if len(sys.argv) < 2:
    # for the testing phase we leave it like this
    pair_id = 1
    # later for the experiment the system will stop if no subject ids are given
    #print("Experiment was stopped! Please enter the pair id as command line argument!")
    #sys.exit()
else:
    pair_id = sys.argv[1]

# Gabor patch global variables
X = 512; # width of the gabor patch in pixels
sf = .02; # spatial frequency, cycles per pixel

gabortexture = (
    visual.filters.makeGrating(res=X, cycles=X * sf) *
    visual.filters.makeMask(matrixSize=X, shape="circle", range=[0, 1])
)

window = visual.Window(size=(2048, 768), units='pix', fullscr=False)

noisetexture = random([X,X])*2.-1. # a X-by-X array of random numbers in [-1,1]

class subject:
    def __init__(self, sid, state, threshold, inputdevice, xoffset, position, keys):
        '''
            state is either 0 or 1 for observing or acting conditions, respectively
            xoffset is the constant added to all stimuli rendered for the subject
            signal is the signal according to the subjects threshold
            inputdevice is the pyusb connector to the subject's buttonbox
            position is either left of right. it is used to determine the speaker of the subject
            keys is a list of keys expected from the user. it has to be in the order of yes and no
        '''
        self.id = sid
        self.state = state
        self.xoffset = xoffset
        self.response = None
        self.signal = visual.GratingStim(
            win = window, tex = gabortexture, mask = 'circle', pos=[0 + xoffset,0],
            size = X, contrast = 1.0, opacity = threshold,
        )
        self.inputdevice = inputdevice
        self.actingheadphonebalance = "100%,0%" if position == "left" else "0%,100%"

        self.buttons = {
                keys[0] : "yes",
                keys[1] : "no",
                None : "noresponse"
                }

        # the annulus is created by passing a matrix of zeros to the texture argument
        self.annulus = visual.GratingStim(
            win = window, mask='circle', tex=np.zeros((64,64)), pos=[0 + xoffset,0],
            size = 50, contrast = 1.0, opacity = 1.0,
        )

        # noise patch
        self.noise = visual.RadialStim(
            win = window, mask='none', tex = noisetexture, pos=[0 + xoffset,0],
            size = X, contrast = 1.0, opacity = 1.0,
        )

        # red fixation dot for decision phase
        self.reddot = visual.GratingStim(
            win = window, size=5, units='pix', pos=[0 + xoffset,0],
            sf=0, color='red', mask='circle'
        )

        # green fixation dot for pre trial and inter trial condition
        self.greendot = visual.GratingStim(
            win = window, size=5, units='pix', pos=[0 + xoffset,0],
            sf=0, color='green', mask='circle'
        )

        '''
        # a dot which indicates to the subject they are in the observation state
        self.obsindicator = visual.GratingStim(
            win = window, size=50, units='pix', pos=[250 + xoffset, 250],
            sf=0, color='blue', mask='circle'
        )
        '''

        # a dot which indicates to the subject they are in the observation state
        self.indicatordict = {
                "yes" : visual.TextStim(
                            win = window, text="Yes", units='pix', pos=[0 - xoffset, 0]
                        ),
                "no" : visual.TextStim(
                            win = window, text="No", units='pix', pos=[0 - xoffset, 0]
                        ),
                "noresponse" : visual.TextStim(
                            win = window, text="No Response", units='pix', pos=[0 - xoffset, 0]
                        ),
                }

    def __repr__ (self):
        return str(self.id)

### Global variables for rendering stimuli
sone = subject(1, 1, 0.3, None, window.size[0]/-4, "right", ["9", "0"])
stwo = subject(2, 0, 0.7, None, window.size[0]/4, "left", ["1", "2"])
subjects = [sone, stwo]

expinfo = {'date': data.getDateStr(), 'pair': pair_id, 'participant1': sone.id, 'participant2' : stwo.id}
#expinfo = {'participant1': sone.id}

blocks = range(2)
ntrials = 1

# create beep for decision interval
beep = Sound('A', secs=0.5)


def genstartscreen ():
    visual.TextStim(window,
                    text="Press spacebar to start.", pos=[0 + sone.xoffset,0],
                    color='black', height=20).draw()

    visual.TextStim(window,
                    text="Press spacebar to start.", pos=[0 + stwo.xoffset,0],
                    color='black', height=20).draw()

def geninstructions ():
    instructions = "Instructions:\n\
    Your task is to indicate if you see a vertical grating or not.\n\
    1. At the start of each trial, a red dot is shown in the middle of the screen.\n\
    2. When you hear a beep, you may press one of the buttons to indicate if you saw a vertical grating or not.\n\
    3. Press the left key for 'yes' and the right key for 'no'.\n\
    4. After a short break, the procedure will be repeated from step 1.\n\
    5. After 80 trials, you will have a break.\n\
    6. After the break, press the spacebar when ready to continue.\n\
    7. There will be a total of 6 blocks. \n\n\
    Press spacebar when ready."

    visual.TextStim(window,
                    text=instructions, pos=[0 + sone.xoffset,0],
                    color='black', height=20).draw()

    visual.TextStim(window,
                    text=instructions, pos=[0 + stwo.xoffset,0],
                    color='black', height=20).draw()

def genendscreen ():
    visual.TextStim(window,
                    text="Thank you for participating.", pos=[0 + stwo.xoffset,0],
                    color='black', height=20).draw()

    visual.TextStim(window,
                    text="Thank you for participating.", pos=[0 + stwo.xoffset,0],
                    color='black', height=20).draw()


def genbaseline (subjects):
    for s in subjects:
        s.noise.draw()
        s.annulus.draw()
        s.reddot.draw()

        '''
        if s.state == 0:
            s.obsindicator.draw()
        '''

def gendecisionint (subjects, condition):
    '''
        Generate the stimulus
        condition:
            's' for Signal
            'n' for Noise
    '''
    if condition == 'noise':
        genbaseline(subjects)
    elif condition == 'signal':
        for s in subjects:
            s.noise.draw()
            s.signal.draw()
            s.annulus.draw()
            s.reddot.draw()

            '''
            if s.state == 0:
                s.obsindicator.draw()
            '''
    else:
        raise NotImplementedError

def genintertrial (subjects):
    for s in subjects:
        s.noise.draw()
        s.annulus.draw()
        s.greendot.draw()

        '''
        if s.state == 0:
            s.obsindicator.draw()
        '''

    # if subject one/two is in an acting state, add their response to the response box of subject two/one
    if stwo.state == 1:
        sone.indicatordict[stwo.response].draw()
    if sone.state == 1:
        stwo.indicatordict[sone.response].draw()

def genbreakscreen (window):
    '''
        Generate the screen shown when the break is in progress
    '''
    instructions = "Instructions:\n\
    Enjoy your break. Press any key to resume."

    instructions = visual.TextStim(window,
                                    text=instructions,
                                    color='black', height=20)

def genendscreen (nextcondition):
    '''
        Generate the end screen
        Args:
            nextcondition:
                'd' : Go to the dyadic condition
                'i' : Go to the individual condition
                'e' : End the experiment
    '''
    instructions = "Thank you for your time."

    instructions = visual.TextStim(window,
                                    text=instructions,
                                    color='black', height=20)


def fetchbuttonpress (subjects, clock):
    '''
        Looks for input from a pyserial connector
        Args:
            connector: PySerial object of connection to button box
            clock: PsychoPy clock object
    '''
    for s in subjects:
        if s.state == 0:
            continue
        else:
            # How do I tell waitKeys to look for input from the specific subject input device and not the other?
            response = event.waitKeys(maxWait=2.5, timeStamped=clock, clearEvents=True, keyList=s.buttons.keys())

            keystroke = response[0][0] if response is not None else response
            s.response = s.buttons[keystroke]
            # waitButtons is from the rucosci library
            # https://github.com/wilberth/RuSocSci/blob/18569aa014ff7e4be5f4aa6ddd0aa4202f601393/rusocsci/buttonbox.py#L116
            # need to add a mechanism where both subjects are acting, in such a condition response variable will be overwritten
            # response = s.inputdevice.waitButtons(maxWait=2.5, timeStamped=clock, flush=True)
    return response

def updatespeakerbalance ():
    # we can a terminal command to shift the balance. it does not work if both the subject are acting (in the individual condition)
    # but it is a more efficient solution if we don't have a condition where both are acting
    for s in subjects:
        if s.state == 1:
            run(["amixer", "-D", "pulse", "sset", "Master", s.actingheadphonebalance, "quiet"])

def updatestate ():
    '''
        Which dyad makes the button box
    '''
    for s in subjects:
        if s.state == 1:
            s.state = 0
        else:
            s.state = 1

# generate file for storing data

# create trial handler
triallist = [
        {"condition": "signal"},
        {"condition": "noise"}
        ]


# preparing the clocks
responsetime = core.Clock()

# specifications of output file
_thisDir = os.path.dirname(os.path.abspath(__file__))
expName = 'DDM'
filename = _thisDir + os.sep + u'data/%s_pair%s_%s' % (expName, expinfo['pair'], data.getDateStr())

exphandler = data.ExperimentHandler(name=expName, extraInfo=expinfo, saveWideText=True, dataFileName=filename)
for b in blocks:
    exphandler.addLoop(data.TrialHandler(triallist, nReps=ntrials, method='random', originPath=-1, extraInfo=expinfo) )

# diplay "press space bar to start"
genstartscreen()
window.flip()
keys = event.waitKeys(keyList=['space'])

# display instructions
geninstructions()
window.flip()
keys = event.waitKeys(keyList=['space'])

# variables for data saving
block=0
trialInBlock=0

for trials in exphandler.loops:
    # variables for data saving
    block+=1
    trialInBlock=0
    # traverse through trials
    for trial in trials:

        # save trial data to file
        trialInBlock += 1
        exphandler.addData('block', block)
        exphandler.addData('trial', trialInBlock)
        exphandler.addData('totalTrials', (block-1)*2*ntrials+trialInBlock)
        exphandler.addData('condition', trials.thisTrial['condition'])
        exphandler.addData('s1_state', sone.state)
        exphandler.addData('s2_state', stwo.state)

        # display baseline
        genbaseline(subjects)
        window.flip()
        # wait for a random time between 2 to 4 seconds
        core.wait( np.random.uniform(2,4) )

        # preparing time for next window flip, to precisely co-ordinate window flip and beep
        nextflip = window.getFutureFlipTime(clock='ptb')
        beep.play(when=nextflip)
        # display stimulus
        gendecisionint(subjects, trials.thisTrial['condition'])
        window.flip()
        # we decided to reset the clock after flipping (redrawing) the window
        responsetime.reset()

        # fetch button press
        response = fetchbuttonpress(subjects, responsetime)
        print(response)
        # save response to file
        if response is not None:
            exphandler.addData('response', response[0][0])
            exphandler.addData('rt', response[0][1])
        else:
            exphandler.addData('response', 'None')
            exphandler.addData('rt', 'None')


        # need to explicity call stop() to go back to the beginning of the track
        # we reset after collecting a response, otherwise the beep is stopped too early
        beep.stop()

        # display inter trial interval
        genintertrial(subjects)
        window.flip()
        # inter trial interval is 2s
        core.wait(2)

        # state switch
        updatestate()

        # update the speaker balance to play the beep for the right subject
        updatespeakerbalance()

        # move to next row in output file
        exphandler.nextEntry()

    # decide between continuing with next block, take a break
genendscreen()


