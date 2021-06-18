# 11 April 2021

'''
    Naming Convention:
        The subjects are either refered to as 'sone' or 'stwo'
        The variables for each are prepended with `sone_` or `stwo_`

    To Do:
        - There is a warning that a providing data file can prevent data loss in case of crash. Is it writing to the disk and should we have this?
'''

import ctypes
xlib = ctypes.cdll.LoadLibrary("libX11.so")
xlib.XInitThreads()

from typing import Any, Callable

import os
import sys
from subprocess import run
import numpy as np
import psychtoolbox as ptb
from psychopy import visual, event, core, gui, data, prefs, monitors
from psychopy.hardware import keyboard
from stimuli import stimulus
from random import choice, shuffle
import json

# setting PTB as our preferred sound library and then import sound

'''
To obtain your sounddevices run the following line on the terminal
python3 -c "from psychopy.sound.backend_sounddevice import getDevices;print(getDevices())"
Copy the `name` attribute of your device to the audioDevice
'''

prefs.hardware['audioLib'] = ['PTB']

from psychopy import sound
sound.setDevice('USB Audio Device: - (hw:3,0)')

from psychopy.sound import Sound
from numpy.random import random


# get pair id via GUI
#name = 'Experiment: Dyadic Decision Making'
#info = {'pair ID':''}
#while (info['pair ID']==''):
#    dlg = gui.DlgFromDict(dictionary=info, sortKeys=False, title=name)
#    if dlg.OK == False:
#        core.quit()
#pair_id = int(info['pair ID'])

# get pair id via command-line argument
try:
    pair_id = int(sys.argv[1])
except:
    print('Please enter a number as pair id as command-line argument!')
    sys.exit(0)
    #pair_id=2

# button <> finger mapping
if pair_id < 13:
    instrmapping = ['right', 'left'] # variable for instructions - first element is 'yes'
else:
    instrmapping = ['left', 'right']

# monitor specs global variables
M_WIDTH = 1920*2
M_HEIGHT = 1200
REFRESH_RATE = 60

myMon = monitors.Monitor('DellU2412M', width=M_WIDTH, distance=65)
myMon.save()

# Gabor patch global variables
CYCLES = 10 # required cycles for the whole patch
X = 395; # size of texture in pixels, needs to be to the power of 2!
sf = CYCLES/X; # spatial frequency for texture, cycles per pixel

gabortexture = (
    visual.filters.makeGrating(res=X, cycles=X * sf) *
    visual.filters.makeMask(matrixSize=X, shape="circle", range=[0, 1])
)

window = visual.Window(size=(M_WIDTH, M_HEIGHT), monitor=myMon, units='pix', blendMode='add', fullscr=False, useFBO=True, allowGUI=False, pos=(0,0))
window.mouseVisible = False # hide cursor

noisetexture = random([X,X])*2.-1. # a X-by-X array of random numbers in [-1,1]


class subject:
    def __init__(self, sid, xoffset, position, keys, kb):
        '''
            state is either 0 or 1 for observing or acting conditions, respectively
            xoffset is the constant added to all stimuli rendered for the subject
            signal is the signal according to the subject's threshold
            position is either left of right. it is used to determine the speaker of the subject
            keys is a list of keys expected from the user. it has to be in the order of yes and no
        '''

        # fetching subject titration thresholds
        try:
            n = "1" if position == "left" else "2"
            f = open("data/" + str(pair_id) + "/data_chamber" + n + ".json", "r")
            data = json.load(f)
        except FileNotFoundError:
            print("Titration file not found for subject in chamber " + n)
            exit(-1)
        else:
            self.threshold = data["threshold"]

        self.id = sid
        self.kb = kb
        self.state = 0
        self.xoffset = xoffset
        self.response = None
        self.actingheadphonebalance = "30%,0%" if position == "left" else "0%,30%"

        stimuli = stimulus(X=X, window=window, xoffset=xoffset, threshold=self.threshold)

        if pair_id < 13:
            self.buttons = {
                    keys[1] : "yes",
                    keys[0] : "no",
                    None : "noresponse"
                    }
        else:
            self.buttons = {
                keys[0]: "yes",
                keys[1]: "no",
                None: "noresponse"
            }

        # signal
        self.signal = stimuli.signal

        # noise patch
        self.noise = stimuli.noise

        # red fixation dot for decision phase
        self.reddot = stimuli.reddot

        # green fixation dot for pre trial and inter trial condition
        self.greendot = stimuli.greendot

        # a dot which indicates to the subject they are in the observation state
        self.indicatordict = {
                "yes" : visual.TextStim(
                            win = window, text="Yes", units='pix', pos=[0 + xoffset, 0]
                        ),
                "no" : visual.TextStim(
                            win = window, text="No", units='pix', pos=[0 + xoffset, 0]
                        ),
                "noresponse" : visual.TextStim(
                            win = window, text="No Response", units='pix', pos=[0 + xoffset, 0]
                        )
                }

    def __repr__ (self):
        return str(self.id)


### Global variables for rendering stimuli

ofs = window.size[0] / 4 # determine the offset once, assign it as neg or pos next

def getKeyboards():
    keybs = keyboard.getKeyboards()
    k = {"chone" : None, "chtwo" : None}

    for keyb in keybs:
        if keyb['product'] == "Black Box Toolkit Ltd. BBTK Response Box":
            if k['chone'] != None:
                k['chtwo'] = keyb['index']
                return k

            if k['chtwo'] != None:
                k['chone'] = keyb['index']
                return k

            ktemp = keyboard.Keyboard(keyb['index'])
            keypress = ktemp.waitKeys(keyList=["1", "2", "7", "8"])

            if keypress[0].name in ["1", "2"]:
                k['chone'] = keyb['index']
            else:
                k['chtwo'] = keyb['index']

keybs = getKeyboards()

#import pdb; pdb.set_trace()

sone = subject(1, ofs, "right", ["1", "2"], keyboard.Keyboard( keybs["chone"] ))
stwo = subject(2, -ofs, "left", ["8", "7"], keyboard.Keyboard( keybs["chtwo"] ))
subjects = [sone, stwo]

expkb = keyboard.Keyboard() # @Hunaid: change this to the experimenter keyboard

kb = keyboard.Keyboard() # variable including all keyboards for clearing buffers and resetting clocks

expinfo = {'pair': pair_id}

blocks = range(2)
ntrials = 80 # trials per block

# create beep for decision interval
beep = Sound('A', secs=0.5, volume=0.1)

def gentext (instr):
    visual.TextStim(window,
                    text=instr, pos=[0 + sone.xoffset, 0],
                    color='black', height=20).draw()

    visual.TextStim(window,
                    text=instr, pos=[0 + stwo.xoffset, 0],
                    color='black', height=20).draw()

def genstartscreen ():
    instructions = "Welcome to our experiment! \n\n\
    Your task is to indicate whether you see a vertical grating or not.\n\
    If you have any questions after reading the instructions on the next screen, please feel free to ask the experimenter.\n\n\
    Press the {} key to continue".format(instrmapping[0])

    gentext(instructions)

def geninstructionspractice ():
    instructions = "Please read the instructions carefully.\n\
    1. Place your index finger on the left key and your middle finger on the right key.\n\
    2. Now, you will have a few practice trials to see how the experiment works.\n\
    3. You will do the task together with your partner.\n\
    4. The stimulus will be the same as you saw before: a circle of noise.\n\
    5. Fixate on the dot in the center of the circle.\n\
    6. What's new: Only when you hear a beep, it’s your turn to indicate whether you saw a vertical grating on top of the noise.\n\
    7. Press the {} key for 'yes' and the {} key for 'no'.\n\
    8. It’s very important that you respond as fast and as accurate as possible! You only have a limited amount of time for your response.\n\
    9. If you don’t hear a beep, it’s the other person’s turn to respond. You will both see the the same stimulus and you will also see their response on your screen.\n\n\
    Press yes to continue".format(instrmapping[0], instrmapping[1])

    gentext(instructions)

def geninstructionsexperiment ():
    instructions = "Now you’re ready to start the experiment. Please remember:\n\
    1. Place your index finger on the left key and your middle finger on the right key.\n\
    2. Fixate on the dot in the center of the circle.\n\
    3. When you hear a beep it’s your turn. If you don’t hear a beep, you will see your partner’s response.\n\
    4. Press the {} key for 'yes' and the {} key for 'no'.\n\
    5. Please respond as quickly and as accurately as possible! \n\
    6. Once you finished one block, you’ll be asked if you’re ready for the next block.\n\
    7. After every second block, you will have a break.\n\
    8. There will be a total of 12 blocks.\n\n\
    Press yes when you’re ready to start the experiment".format(instrmapping[0], instrmapping[1])

    gentext(instructions)

def genendscreen ():
    instructions = "Thank you for your time.\n\n\
    Please let the experimenter know you're finished."

    gentext(instructions)

def genbreakscreen ():
    '''
        Generate the screen shown when the break is in progress
    '''
    instructions = "Are you ready for the next block?\n\n\
    Press yes when you're ready to resume"

    gentext(instructions)

def genmandatorybreakscreen ():
    '''
        Generate the screen shown when the mandatory break is in progress
    '''
    instructions = "Enjoy your break. Please inform the experimenter.\n\n\
    The experimenter will resume the experiment after a short break."

    gentext(instructions)

def genbaseline (subjects):
    for s in subjects:
        s.noise.phase += (10 / 128.0, 10 / 128.0)
        s.noise.draw()
        s.reddot.draw()

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
            s.noise.phase += (10 / 128.0, 10 / 128.0)
            s.noise.draw()
            s.signal.draw()
            s.reddot.draw()
    else:
        raise NotImplementedError

def genintertrial (subjects):
    for s in subjects:
        s.noise.phase += (10 / 128.0, 10 / 128.0)
        s.noise.draw()
        s.greendot.draw()

    # if subject one/two is in an acting state, add their response to the response box of subject two/one
    if stwo.state == 1:
        if stwo.response != "noresponse":
            sone.indicatordict[stwo.response].draw()
    if sone.state == 1:
        if sone.response != "noresponse":
            stwo.indicatordict[sone.response].draw()


def fetchbuttonpress (subjects):
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
            temp = s.kb.getKeys(keyList=s.buttons.keys(), clear=True)

            if len(temp) == 0:
                resp = []
                s.response = s.buttons[None]
            else:
                keystroke = temp[0].name
                s.response = s.buttons[keystroke]
                resp = [s.buttons[keystroke], temp[0].rt]

    return resp

def updatespeakerbalance ():
    # we can a terminal command to shift the balance. it does not work if both the subject are acting (in the individual condition)
    # but it is a more efficient solution if we don't have a condition where both are acting
    for s in subjects:
        if s.state == 1:
            run(["amixer", "-D", "pulse", "sset", "Master", s.actingheadphonebalance, "quiet"])
            #pass

def updatestate ():
    '''
        Which dyad makes the button box
    '''
    sone.state = next(iterstates)
    stwo.state = 1 - sone.state

def secondstoframes (seconds):
    return range( int( np.rint(seconds * REFRESH_RATE) ) )

def getacknowledgements ():
    sone_ack, stwo_ack = None, None

    while (sone_ack != 'yes') or (stwo_ack != 'yes'):
        resp1 = sone.kb.getKeys(clear=False)
        resp2 = stwo.kb.getKeys(clear=False)

        if resp1:
            for r in resp1:
                if sone_ack != 'yes': sone_ack = sone.buttons[r.name]
        if resp2:
            for r in resp2:
                if stwo_ack != 'yes': stwo_ack = stwo.buttons[r.name]

    kb.clearEvents(eventType='keyboard') # clearing buffers

def getexperimenterack ():
    keys = expkb.waitKeys(keyList=["q", "space"], clear=True)
    if "q" in keys: # exit experiment
        window.close()
        core.quit()


def genactingstates ():
    return np.random.randint(0, 2, ntrials)

# update speaker balance for the first time
updatespeakerbalance()

# specifications of output file
_thisDir = os.path.dirname(os.path.abspath(__file__))
expName = 'DDM'
filename = _thisDir + os.sep + u'data/%s_pair%s_%s' % (expName, expinfo['pair'], data.getDateStr())


# set up trial handler and experiment handler
triallist=[]
# make sure signal is present on 50% of trials
for Idx in range(ntrials//2):
    triallist.append({"condition": "signal"})
    triallist.append({"condition": "noise"})

exphandler = data.ExperimentHandler(name=expName, extraInfo=expinfo, saveWideText=True, dataFileName=filename)
for b in blocks:
    exphandler.addLoop(data.TrialHandler(trialList=triallist, nReps=1, method='random', originPath=-1, extraInfo=expinfo) )


##### PRACTICE TRIALS #####

# diplay welcome screen
genstartscreen()
window.flip()
getacknowledgements()

# display instructions for practice trials
geninstructionspractice()
window.flip()
getacknowledgements()

# set up practice trials
npracticetrials = 2 # needs to be an even number
practicestates=[]
practicetriallist=[]
# make sure signal/noise and acting/observing are equally distributed for practice trials
for _ in range (npracticetrials//2):
    practicestates.append(0)
    practicestates.append(1)
    practicetriallist.append("signal")
    practicetriallist.append("noise")

# shuffle the lists
shuffle(practicestates)
shuffle(practicetriallist)

# make an iterator object
iterstates = iter(practicestates)

# traverse through practice trials
for idx in range(npracticetrials):
    # subject state update
    updatestate()
    # update the speaker balance to play the beep for the right subject
    updatespeakerbalance()

    # display baseline
    # wait for a random time between 2 to 4 seconds
    for frame in secondstoframes( np.random.uniform(2, 4) ):
        genbaseline(subjects)
        window.flip()


    # preparing time for next window flip, to precisely co-ordinate window flip and beep
    # display stimulus
    nextflip = window.getFutureFlipTime(clock='ptb')
    beep.play(when=nextflip)

    kb.clearEvents(eventType='keyboard')

    response = [] # we have no response yet
    for frame in secondstoframes(2.5):
        gendecisionint(subjects, practicetriallist[idx])
        window.flip()

        # fetch button press
        if not response:
            response = fetchbuttonpress(subjects)
        else:
            break

    # need to explicity call stop() to go back to the beginning of the track
    # we reset after collecting a response, otherwise the beep is stopped too early
    beep.stop()

    # display inter trial interval for 2s
    for frame in secondstoframes(2):
        genintertrial(subjects)
        window.flip()


##### MAIN EXPERIMENT #####

# display instructions for experiment
geninstructionsexperiment()
window.flip()
getacknowledgements()

# variables for data saving
block=0

# start MAIN EXPERIMENT
for trials in exphandler.loops:

    # variables for data saving
    block+=1
    trialInBlock=0

    # make an iterator object
    states = genactingstates()
    iterstates = iter(states)

    # traverse through trials
    for trial in trials:

        # subject state update
        updatestate()
        # update the speaker balance to play the beep for the right subject
        updatespeakerbalance()

        # save trial data to file
        trialInBlock += 1
        exphandler.addData('block', block)
        exphandler.addData('trial', trialInBlock)
        exphandler.addData('totalTrials', (block-1)*ntrials+trialInBlock)
        exphandler.addData('s1_state', sone.state)
        exphandler.addData('s2_state', stwo.state)

        # display baseline for a random time between 2 to 4 seconds
        for frame in secondstoframes( np.random.uniform(2, 4) ):
            genbaseline(subjects)
            window.flip()

        kb.clearEvents(eventType='keyboard')

        # preparing time for next window flip, to precisely co-ordinate window flip and beep
        # display stimulus
        nextflip = window.getFutureFlipTime(clock='ptb')
        beep.play(when=nextflip)

        #kb.clock.reset()  resets clocks for all keyboards
        sone.kb.clock.reset()
        stwo.kb.clock.reset()

        response = []  # we have no response yet
        for frame in secondstoframes(2.5):
            gendecisionint(subjects, trials.thisTrial['condition'])
            window.flip()

            # fetch button press
            if not response:
                response = fetchbuttonpress(subjects)
            else:
                break

        # need to explicity call stop() to go back to the beginning of the track
        # we reset after collecting a response, otherwise the beep is stopped too early
        beep.stop()

        # display inter trial interval for 2s
        for frame in secondstoframes(2):
            genintertrial(subjects)
            window.flip()

        # save response to file
        if not response:
            exphandler.addData('response', "noresponse")
            exphandler.addData('rt', "None")
        else:
            exphandler.addData('response', response[0])
            exphandler.addData('rt', response[1])

        # move to next row in output file
        exphandler.nextEntry()

    # after every second block (unless after the last block), there will be a mandatory break which only the experimenter can end
    if block % 2 == 0 and block != blocks[-1]:
        genmandatorybreakscreen()
        window.flip()
        getexperimenterack()
    # otherwise, wait for the subjects to start their next block
    elif block % 2 == 1:
        genbreakscreen()
        window.flip()
        getacknowledgements()
        continue

genendscreen()
window.flip()
core.wait(10)
