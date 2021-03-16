## How to Avoid Jitter in Experiment Display

### Introduction
#### Aim of this Document
The aim of this text is to explain tips on how to code you experiment such that it's display is consistent time-wise. A delay in experiment display is manageable because we can subtract a constant from all time stamps, but jitter cannot be regulated simply.

#### Understanding the Problem
The primary cause of jitter is the behaviour of the operating system. The operating system, such as linux, is designed to manage its tasks to increase computational throughput. This can sometimes come at the cost of producing and saving output.

There are two key areas where our ability to regulate timing is weak because the operating system is making independant management decisions:
- writing to/reading from disk
- priority of process/thread execution

Example:
When you write to a file (output to the screen is also a file in Linux), the program writes the output to the output buffer and continues execution. The Linux Kernel may or may not pick this output from the buffer and dump it into the actual file. This will depend on the how busy it is (based on back- and foreground processes) and how full the buffer is.
This problem is resolved by forcing the Kernel to `flush` the buffer. This is also the reason you are asked to eject your USB storage device from the OS before before removing it physicaly. You might have written a file to it and was only added to the buffer and not dumped on the USB stick.

### Techniques for Avoiding Jitter
#### File I/O
Avoid writing the output of your experiment timings into a csv file during the execution of the experiment. Append all the values to a Pandas Dataframe or a String. After you have looped through the entire experiment, dump the content into a csv file.

Take the following staircase experiment example for Psychopy [tutorials](https://www.psychopy.org/coder/tutorial2.html):
```python3
# make a text file to save data
fileName = expInfo['observer'] + expInfo['dateStr']
dataFile = open(fileName+'.csv', 'w')  # a simple text file with 'comma-separated-values'
dataFile.write('targetSide,oriIncrement,correct\n')

for thisIncrement in staircase:  # will continue the staircase until it terminates!
    # CODE FOR PREPARATION OF STIMULUS

    while thisResp==None:
        # CODE FOR COLLECTING A RESPONSE

    # add the data to the staircase so it can calculate the next level
    staircase.addData(thisResp)

    # The statement below is problematic. It asks python to write the result to file.
    dataFile.write('%i,%.3f,%i\n' %(targetSide, thisIncrement, thisResp))

    core.wait(1)
```

An alternate approach is to:
```python3
# make a empty dataframe to save data
df = pd.DataFrame(columns=['targetSide', 'oriIncrement', 'correct'])

for thisIncrement in staircase:  # will continue the staircase until it terminates!
    # CODE FOR PREPARATION OF STIMULUS

    while thisResp==None:
        # CODE FOR COLLECTING A RESPONSE

    # add the data to the staircase so it can calculate the next level
    staircase.addData(thisResp)

    # The statement below is problematic. It asks python to write the result to file.
    #dataFile.write('%i,%.3f,%i\n' %(targetSide, thisIncrement, thisResp))
    # append recorded data as a row to the dataframe
    df.append([targetSide, thisIncrement, thisResp])

    core.wait(1)

# prepare filename for data file
fileName = expInfo['observer'] + expInfo['dateStr']
# save dataframe as a file
df.to_csv(fileName)
```

#### Pre Load the Stimuli
If you're going to display pictorial the stimuli, it is important to pre-load it.

Access to RAM is faster than Backing Store (HDD/SDD). RAM is built of transistors, is small and closer to the processor. Therefore, if you read the file from disk everytime you want to display it, not only will the OS take longer but also an inconsistent amount of time because look up and fetch are affected by the physical location and size of the file.

Pre-loading an image is as simple as creating a variable which has the image in it. When you want to display it, you display the variable.
Example code<sup>[Source](https://discourse.psychopy.org/t/colour-imagestim-inconsistent-timing/1817/5)</sup>

```python3
""" PRELOAD IMAGES"""
imgList = []
path = os.getcwd()
for infile in glob.glob(os.path.join(path, '*.jpg')):
    imgList.append(infile)
pictures = [visual.ImageStim(win, img, ori=0, pos=[0, 0]) for img in imgList]

""" DISPLAY PRELOADED IMAGES """
for picture in pictures:
    for frame in range(15):
        picture.draw()
        win.flip()
```

#### Use io.Hub
Newly generated stimulus is updated on the screen using the [`window.flip()`](https://www.psychopy.org/api/visual/window.html#psychopy.visual.Window.flip) function. This function takes the input from the monitor buffer and dumps it on the screen. Execution moves forward after the buffer is released<sup>[Source](https://discourse.psychopy.org/t/understanding-the-flip-method/6164)</sup>. Even if the stimulus is not changing, the screen is redrawn bottom to top at the refresh rate of the monitor.

If you have a `event.wait()` function in the same sequence, this function will not <i>fetch</i> the new button press from the keyboard or kernel buffer till it is called. The dependency of these two events which are executed at uncertain times can cause randomness is recorded times of button press.

The problem is remedied (not fully resolved) by io.Hub<sup>[Docs](https://www.psychopy.org/api/iohub/index.html). Which creates a separate process which waits on the input devices to provide input. This makes this process independant of calling `window.flip()`.

### Important Links
- [Interpretation of different time logs](https://discourse.psychopy.org/t/response-times-in-log-files-key-press-vs-release-and-exp-log-messages/19127)
