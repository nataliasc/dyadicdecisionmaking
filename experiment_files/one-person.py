
'''
    Naming Convention:
        The subjects are either refered to as 'sone' or 'stwo'
'''

import os
import sys
from subprocess import run
import numpy as np
import psychtoolbox as ptb
from psychopy import visual, event, core, gui, data, prefs, monitors
import stimuli
from random import choice, shuffle
import json
import pandas as pd

'''
To obtain your sounddevices run the following line on the terminal
python3 -c "from psychopy.sound.backend_sounddevice import getDevices;print(getDevices())"
Copy the `name` attribute of your device to the audioDevice
'''

# setting PTB as our preferred sound library and then import sound
prefs.hardware['audioLib'] = ['PTB']

from psychopy import sound
sound.setDevice('USB Audio Device: - (hw:3,0)')

from psychopy.sound import Sound
from numpy.random import random

# get pair id via command-line argument
try:
    pair_id = int(sys.argv[1])
except:
    print('Please enter a number as pair id as command-line argument!')
    sys.exit(-1)

# monitor specs global variables
M_WIDTH = stimuli.M_WIDTH
M_HEIGHT = stimuli.M_HEIGHT
REFRESH_RATE = stimuli.REFRESH_RATE

myMon = monitors.Monitor('DellU2412M', width=M_WIDTH, distance=80)
myMon.setSizePix([M_WIDTH, M_HEIGHT])


window = visual.Window(size=(M_WIDTH, M_HEIGHT), monitor=myMon, units='pix', fullscr=True, useFBO=True, allowGUI=False, pos=(0,0))
window.mouseVisible = False # hide cursor

class subject:
    def __init__(self, sid):
        '''
            sid is 1 for chamber 1, and 2 for chamber 2
            kb is the psychopy keyboard object to connect to the button box
            keys is a list of keys expected from the user. it has to be in the order of yes and no
            state is either 0 or 1 for observing or acting conditions, respectively
            threshold is the signal according to the subject's threshold
            xoffset is the constant added to all stimuli rendered for the subject
        '''

        # fetching subject titration thresholds
        #try:
        #    f = open("data/" + str(pair_id) + "/data_chamber" + str(sid) + ".json", "r")
        #    data = json.load(f)
        #except FileNotFoundError:
        #    print("Titration file not found for subject in chamber " + n)
        #    exit(-1)
        #else:
        #    self.threshold = data["threshold"]
        self.threshold = 0.018088

        self.id = sid
        self.state = False
        self.response = None
        self.actingheadphonebalance = "30%,0%" if sid == 2 else "0%,30%"

        self.stimulus = stimuli.stim(window=window, xoffset=0, threshold=self.threshold)

        # signal
        self.signal = self.stimulus.signal

        # noise patch
        self.noise = self.stimulus.noise

        # red fixation target for decision phase
        self.fixation_red = self.stimulus.fixation_red

        # green fixation target for pre trial and inter trial condition
        self.fixation_green = self.stimulus.fixation_green

        # a dot which indicates to the subject they are in the observation state
        self.indicatordict = self.stimulus.indicatordict

    def __repr__ (self):
        return str(self.id)


sone = subject(1)
subjects = [sone]

expinfo = {'pair': pair_id, 'threshold': sone.threshold}

blocks = range(2)
ntrials = 2 # trials per block

# create beep for decision interval
beep = Sound('A', secs=0.5, volume=0.1)


def gentext (instr):
    '''
        Generate text on both subject screens
    '''
    visual.TextStim(window,
                    text=instr, pos=[0, 0],
                    color='black', height=20).draw()

    visual.TextStim(window,
                    text=instr, pos=[0, 0],
                    color='black', height=20).draw()


def genstartscreen ():
    instructions = "Welcome to our experiment! \n\n\
    Press the green button to continue"

    gentext(instructions)


def geninstructionspractice ():
    instructions = "Please read the instructions carefully.\n\n\
    1. Place your index finger on the left button and your middle finger on the right button.\n\
    2. Fixate on the dot in the center of the screen.\n\
    3. After the beep, press the green button if noise had stripes. Press the red button if it did not.\n\
    4. Try to respond as fast and accurate as possible. You will have 2.5 seconds to respond.\n\n\
    Press the green button to begin with practice trials.\
    "
    gentext(instructions)


def geninstructionsexperiment ():
    instructions = "You are about to start the main experiment. Please read the instructions. \n\n\
    1. There will be a total of 4 blocks.\n\n\
    2. After every block, you can have a break.\n\
    3. Place your index finger on the left button and your middle finger on the right button.\n\
    4. Fixate on the dot in the center of the screen.\n\
    5. After the beep, press the green button if noise had stripes. Press the red button if it did not. \n\n\
    Press the green button when you’re ready to start the experiment.\n\
    If you have any questions, address the experimenter."

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


def noise (subjects):
    '''
        Show dynamic noise + red fixation dot
    '''
    for s in subjects:
        s.noise = s.stimulus.updateNoise()
        s.noise.draw()
        for grating in s.fixation_red:
            grating.draw()


def gendecisionint (subjects, condition):
    '''
        Generate the stimulus
        condition:
            signal + noise + red fixation dot
            noise + red fixation dot
    '''
    if condition == 'noise':
        noise(subjects)
    elif condition == 'signal':
        for s in subjects:
            s.noise = s.stimulus.updateNoise()
            s.noise.draw()
            s.signal.draw()
            for grating in s.fixation_red:
                grating.draw()
    else:
        raise NotImplementedError


def genintertrial (subjects):
    '''
        Keep displaying the stimulus but also display the other person's response if it wasn't their own turn
        Indicated to the subject by a green fixation dot (instead of a red one)
    '''
    for s in subjects:
        s.noise = s.stimulus.updateNoise()
        s.noise.draw()
        for grating in s.fixation_green:
            grating.draw()


def secondstoframes (seconds):
    return range( int( np.rint(seconds * REFRESH_RATE) ) )


def getexperimenterack ():
    '''
        Wait for the experimenter input
            q: quit experiment (data is saved)
            space: continue
    '''
    keys = expkb.waitKeys(keyList=["q", "space"], clear=True)
    if "q" in keys: # exit experiment
        window.close()
        core.quit()


def fetchbuttonpress ():
    '''
        Get the button box input from the acting subject
        Return the response (yes/ no) and the reaction time
    '''
    for s in subjects:
        keys = event.getKeys()

        if keys:
            return keys[0]
        else:
            return None


# specifications of output file
_thisDir = os.path.dirname(os.path.abspath(__file__))
expName = 'DDM'
filename = _thisDir + os.sep + u'data/%s_pair%s_%s' % (expName, expinfo['pair'], data.getDateStr())

triallist = [{"condition": "signal"}, {"condition": "noise"}] * (ntrials//2)

exphandler = data.ExperimentHandler(name=expName, extraInfo=expinfo, saveWideText=True, dataFileName=filename)
for b in blocks:
    exphandler.addLoop(data.TrialHandler(trialList=triallist, nReps=1, method='random', originPath=-1, extraInfo=expinfo) )

##### PRACTICE TRIALS  START #####

# diplay welcome screen
genstartscreen()
window.flip()
event.waitKeys()

# # display instructions for practice trials
geninstructionspractice()
window.flip()
#core.wait(10)
event.waitKeys()

# set up practice trials
npracticetrials = 10 # needs to be an even number

# make sure signal/noise and acting/observing are equally distributed for practice trials
practicetriallist = ['signal', 'noise'] * (npracticetrials//2)

# shuffle the lists
shuffle(practicetriallist)

# traverse through practice trials
for idx in range(npracticetrials):
    # display baseline
    # wait for a random time between 2 to 4 seconds
    for frame in secondstoframes( np.random.uniform(2, 4) ):
        noise(subjects)
        window.flip()

    # preparing time for next window flip, to precisely co-ordinate window flip and beep
    nextflip = window.getFutureFlipTime(clock='ptb')
    beep.play(when=nextflip)
    event.clearEvents()

    response = [] # we have no response yet
    for frame in secondstoframes(2.5):
        gendecisionint(subjects, practicetriallist[idx])
        window.flip()

        # fetch button press
        if not response:
            response = fetchbuttonpress()
        else:
            event.clearEvents()
            break

    # need to explicity call stop() to go back to the beginning of the track
    # we reset after collecting a response, otherwise the beep is stopped too early
    beep.stop()

    # display inter trial interval for 2s
    for frame in secondstoframes(2):
        genintertrial(subjects)
        window.flip()

##### PRACTICE TRIALS  END #####

##### MAIN EXPERIMENT START #####

# display instructions for experiment
geninstructionsexperiment()
window.flip()
#core.wait(10)
event.waitKeys()

# variables for data saving
block = 0

# start main experiment
for trials in exphandler.loops:

    # variables for data saving
    block += 1

    # traverse through trials
    for trial in trials:
        # save trial data to file
        exphandler.addData('block', block)
        exphandler.addData('trial', trials.thisTrialN)

        # display baseline for a random time between 2 to 4 seconds
        for frame in secondstoframes( np.random.uniform(2, 4) ):
            noise(subjects)
            window.flip()

        # preparing time for next window flip, to precisely co-ordinate window flip and beep
        nextflip = window.getFutureFlipTime(clock='ptb')
        beep.play(when=nextflip)
        event.clearEvents()

        response = []  # we have no response yet
        for frame in secondstoframes(2.5):
            gendecisionint(subjects, trials.thisTrial['condition'])
            window.flip()

            # fetch button press
            if not response:
                response = fetchbuttonpress()
            else:
                event.clearEvents()
                break

        # need to explicity call stop() to go back to the beginning of the track
        beep.stop()

        # display inter trial interval for 2s
        for frame in secondstoframes(2):
            genintertrial(subjects)
            window.flip()

        # save response to file
        if not response:
            exphandler.addData('response', "noresponse")
            #exphandler.addData('rt', "None")
        else:
            exphandler.addData('response', response[0])
            #exphandler.addData('rt', response[1])

        # move to next row in output file
        exphandler.nextEntry()

    # after every second block (unless after the last block), there will be a mandatory break which only the experimenter can end
    #if block % 2 == 0 and block != (blocks[-1] + 1):
    #    genmandatorybreakscreen()
    #    window.flip()
    #    getexperimenterack()
    # otherwise, wait for the subjects to start their next block
    #else:
    genbreakscreen()
    window.flip()
    event.waitKeys()
        #continue

genendscreen()
window.flip()
core.wait(5)

#code to calculate and show the performance metrics
exphandler.saveAsWideText(str(pair_id) + '.csv',delim=',')
df = pd.read_csv(str(pair_id) + '.csv')
df = df[['condition','response']]
conditions = [
    (df['condition'] == 'signal') & (df['response'] == 1),
    (df['condition'] == 'signal') & (df['response'] == 2),
    (df['condition'] == 'noise')  & (df['response'] == 1),
    (df['condition'] == 'noise')  & (df['response'] == 2),
    (df['response'] == 'noresponse')
]
values = ['hit', 'miss', 'false-alarm', 'correct-reject','no-response']
df['outcome'] = np.select(conditions, values)
accuracy = df[df['outcome'].isin(['hit','correct-reject'])].shape[0]/df.shape[0]
print("     Overall Accuracy %.2f\n" % (accuracy*100))
print(df.groupby(['condition'])['outcome'].value_counts(normalize=True,sort=False)*100)
df = df[['condition','response','outcome']]
