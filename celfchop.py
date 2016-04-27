#!/usr/bin/env python
# Copyright (c) 2016 Allison Sliter
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the 'Software'), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE

import textgrid
import subprocess
import os.path
import argparse

#CELF resectioning doohicky

class PromptResponse(object):
    """
    Stores a prompt designation(string), a start and end time for an interval (floats), and the transcription(string) for that interval"
    """
    def __init__ (self, prompt, minTime, maxTime, transcript):
        if minTime > maxTime: # not an actual interval
            raise ValueError(minTime, maxTime)
        self.prompt = prompt
        self.minTime = minTime
        self.maxTime = maxTime
        self.transcript = transcript
    
    def __str__(self):
        label = self.prompt
        label = label + ", "
        label = label + self.transcript
        label = label + " ["
        label = label + str(self.minTime)
        label = label + ", "
        label = label + str(self.maxTime)  
        label = label + "]"
        return label
    


def blankRemoval(tier):
    """
    Removes intervals not containing data from a textgrid.IntervalTier object
    """
        
    interval_list = [interval for interval in tier if len(interval.mark.strip()) > 0]
    return interval_list

def before(intX, intY):
    """
    Takes textgrid.Interval objects
    Returns true if intX starts before intY
    """
    return intX.minTime < intY.minTime

def timeOrder(tier, start, end):
    """
    Sorts an textgrid.IntervalTier into chronological order and returns the ordered list
    """
    if start < end:
        pivot = partition(tier, start, end)
        timeOrder(tier, start, pivot-1)
        timeOrder(tier, pivot+1, end)
    return tier
        

def partition(tier, start, end):
    """
    Quicksort helper function
    """
    
    pivot = tier[start]
    left = start + 1
    right = end
    done = False
    
    while not done:
        while left<= right and tier[left].minTime <= pivot.minTime:
            left = left + 1
        while tier[right].minTime >= pivot.minTime and right >= left:
            right = right - 1
        if right < left:
            done = True
        else:
            temp = tier[left]
            tier[left] = tier[right]
            tier[right] = temp
    temp = tier[start]
    tier[start] = tier[right]
    tier[right] = temp
    return right
    


def findDigression(comment_tier):
    """
    Takes textgrid.IntervalTier representing the comments tier and locates digression intervals and returns a list of them.
    """
    digress_list = []
    for interval in comment_tier:
        if interval.mark == '[.digress]':
            digress_list.append(interval)
    return digress_list

def isInInterval(intX, intY):
    """
    Takes two textgrid.Interval objects and determines if interval y is in interval x
    """
    return intX.overlaps(intY)
    
def timeFormat(seconds):
    """
    Helper function
    """
    
    time = ""
    h = 0
    m = 0
    s = 0
    while seconds >= 3600:
        h = h + 1
        seconds = seconds - 3600
    while seconds >= 60:
        m = m + 1
        seconds = seconds - 60
    s = seconds
    
    if (m == 0):
        mm = "00"
    elif(m < 10):
        mm = "0" + str(m)
    else:
        mm = m
    
    if (s == 0):
        ss = "00"
    elif(s < 10):
        ss = "0" + str(s)
    else:
        ss = str(s)
    
    if (h is 0):
        time = str(mm) + ":" + str(ss)
        
    else:
         time = str(h) + ":" + mm + ":" + ss
    return time
        

def wavChop(subject, inpath, response):
    """
    takes a PromptResponse and a path that points to a .wav file and chops a clip (creating a new .wav file) from that 
    .wav file starting and stopping at the boundaries of the response and place it in directory
    
    Calls "sox" application 
    """

    prompt = response.prompt
    prompt = prompt.replace(' ', '-')    
    outpath = subject + "-" + prompt + ".wav"
    folder = subject + "-" + prompt
    dest = os.path.join(subject, folder, outpath)
    start = timeFormat(response.minTime)
    stop = "=" + timeFormat(response.maxTime)
    
    
    subprocess.call(["sox", inpath, dest, "trim", start, stop])
    
def clearChar(text):
    """
    Takes a string a a removes { } ( ) and *, returning the clean string
    """
    
    text = text.replace("}", "")
    text = text.replace("{", "")
    text = text.replace("*", "")
    text = text.replace("(", "")
    text = text.replace(")", "")
    
def textChop(subject, response):
    """
    Writes transcript portion of a PromptResponse to a text file named with the subject and PromptResponse.prompt and places it in directory
    """
    prompt = subject + "-" + response.prompt
    prompt = prompt.replace(' ', '-')
    name = prompt + ".txt"
    dest = os.path.join(subject, prompt, name)
    text = response.transcript
    text = clearChar(text)
    with open(dest, "w") as text:
        text.write(response.transcript)
 
def makeDirectories(subject, responses):
    """
    Takes a string representing the subject designation and list of PromptResponses and makes directories for files to land in.
    If two identical PromptResponse.prompt object exist, the directory is only created once.
    """
    dirlist = []
    os.mkdir(subject)
    for dirs in range(0, len(responses)):
        prompt = subject + "-" + responses[dirs].prompt
        prompt = prompt.replace(' ', '-')
        path = os.path.join(subject, prompt)
        try:
            os.mkdir(path)
        except:
            print subject + "-" + prompt + " Directory exists"
            continue

#ArgumentParser
parser = argparse.ArgumentParser()
parser.add_argument('wavfile', metavar="wavfile", help = 'path of sound file containing full task')
parser.add_argument('grid', metavar="textgrid", help = 'path of textgrid containing transcription')
args = parser.parse_args()


subject = args.wavfile[0:7]
grid = textgrid.TextGrid.fromFile(args.grid)


child_list = blankRemoval(grid.getList("Child")[0])
child_list = timeOrder(child_list, 0, len(child_list)-1)

prompt_list = blankRemoval(grid.getList("Prompt")[0])
prompt_list = timeOrder(prompt_list, 0, len(prompt_list)-1)

if(len(grid.getList("Comments")) > 0):    
    comment_list = blankRemoval(grid.getList("Comments")[0])
    digress_list = findDigression(comment_list)
elif(len(grid.getList("Comment")) > 0):
    comment_list = blankRemoval(grid.getList("Comment")[0])
    digress_list = findDigression(comment_list)
else:
    comment_list = []    

clean_list = []
if (len(digress_list) > 0):
    for p in range(0, len(digress_list)):
        for q in range(0,len(child_list)):
            if not isInInterval(child_list[q],digress_list[p]):
                clean_list.append(child_list[q])
    child_list = clean_list

response_list = []
prompt = None
transcript = None
minTime = 0
maxTime = 0

for x in range(0, len(prompt_list)):
    for y in range(0, len(child_list)):
        if isInInterval(prompt_list[x],child_list[y]):
            prompt = prompt_list[x].mark
            minTime = child_list[y].minTime
            maxTime = child_list[y].maxTime
            transcript = child_list[y].mark
            response = PromptResponse(prompt, minTime, maxTime, transcript)
            response_list.append(response)
            break
            




"""
for x in range(0, len(response_list)):
    print response_list[x].transcript
"""
makeDirectories(subject, response_list)
for response in range(0, len(response_list)):
    wavChop(subject, args.wavfile, response_list[response])
    textChop(subject, response_list[response])

