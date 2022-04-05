# -*- coding: utf-8 -*-
"""
OpenPMU - wavewrite
Copyright (C) 2022  www.OpenPMU.org

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import soundfile as sf
import os
import numpy as np
from datetime import datetime, timedelta


# WaveWrite is intended for writing OpenPMU sampled value (SV) data to disk in
# the form of a WAVE file.  By default, a WAVE file is created each minute, and
# data is appended to it once per second.  Files are normally stored in a
# structure "/YYYY-MM-DD/YYYY-MM-DD_HH-MM-SS.wav".
#
# The interval between files may be changed using 'waveMinutes', in which case
# new files are created each defined number of minutes.
#
# Presently, assumes that SVs are in int16 format.  Fair since that's the only
# model of OpenPMU ADC which exists.

# ###########################################
# ------------- FlacWrite Class -------------

class WaveWrite:
    
    def __init__(self, waveTime, sampleRate, channels, wavePath="", waveMinutes=1, frmt='wav'):
        
        # waveTime      - datetime of the wave file to be created/written to
        # sampleRate    - sampling rate (Fs) of the SV data
        # channels      - number of channels to record
        # wavePath      - directory in which to store WAVE files
        # waveMinutes   - minutes between files (i.e. new file interval)
        
        # self.waveTime       = waveTime.replace(second=0, microsecond=0)
        self.waveTime       = self.floorTime(waveTime, waveMinutes)
        self.sampleRate     = sampleRate
        self.channels       = channels
        self.waveMinutes    = waveMinutes
              
        # Sets up the filename and path
        # Format is <configPath>/YYYY-MM-DD/<waveFile>        
        wavePathYMD = self.waveTime.strftime("%Y-%m-%d") + "/"        
        waveFileName = str(self.waveTime)[0:19].replace(':','-').replace(' ','_') + '.' + frmt
        waveFilePath = wavePath + wavePathYMD + waveFileName
        
        # Open the file
        # - WAVE allows file to be opened in read/write mode.  FLAC does not.
        # - This means an existing FLAC file, and its contents will be overwritten.
        # - If opening an existing file, seek to end so new data is written there.
        try:
            self.waveFile = sf.SoundFile(waveFilePath, 'r+')    # Check if the file already exists
            self.waveLength = self.getLength()                       # Get its length so we can 'pad' the difference        
            self.waveFile.seek(0,sf.SEEK_END)                   # Move pointer to end of file
                    
        except Exception as e:                                  # If the file doesn't exist, create it
            self.ensureDir(waveFilePath)                        # If path doesn't exist, create it.
            self.waveFile = sf.SoundFile(waveFilePath, 'w', self.sampleRate, self.channels, subtype='PCM_16')
            self.waveLength = 0                                      # New file, so length is zero
        
        # print(". WAVE_Length", self.waveLength) # Debug
        
        # Pad the newly opened file so that it is the correct length to start appending new data
        # That is, the new data should be appended such that it is the correct time after file time stamp
        initialPad = int((waveTime - self.waveTime).total_seconds() - self.waveLength)
        self.pad(initialPad)
        # print(">>->>", waveTime, self.waveTime, initialPad) # Debug
        
    # Append SVs to the wave file.    
    def append(self, samples):
        
        samples = np.ascontiguousarray(samples.copy().transpose(), dtype=np.int16)
        self.waveFile.buffer_write( samples, dtype='int16' )
        # print("POS: ", self.getLength() )
        
    # Pad the wave file by desired number of seconds    
    def pad(self, padSeconds):
        
        # print("PAD: ", padSeconds) # Debug
        self.padSeconds = padSeconds
        waveEmpty = np.ones((self.channels, (self.sampleRate * padSeconds)))        
        
        samples = np.ascontiguousarray((waveEmpty).copy().transpose(), dtype=np.int16)
        self.waveFile.buffer_write( samples, dtype='int16' )                 
    
    # Calculate the length of the wavefile in seconds    
    def getLength(self):
       
        try:
            length = self.waveFile.frames / self.waveFile.samplerate    
        except Exception as e:
            print(e)      
        return length 
        # return self.flacPosition
    
    # Finalise the wavefile to length of 60 seconds, and close
    def finalise(self):
        
        waveSeconds = self.waveMinutes*60
        preLength   = self.getLength()
        
        # Can't pad FLAC because normally the file is empty        
        if preLength < waveSeconds:
            
            self.pad(int(waveSeconds - preLength))     
            
        finalLength = self.getLength()         
        self.close()
        # print("> Pre-finalised length:", preLength, "Finalised length:", finalLength)   # Debug
        
    # Close the wavefile    
    def close(self):
        self.waveFile.close()
    
    # Ensure the path to the wavefile exists, if not create the path    
    def ensureDir(self, filePath):
        directory = os.path.dirname(filePath)
        if not os.path.exists(directory):
            os.makedirs(directory)
            
    # Finds the floor datetime for a given interval
    def floorTime(self, timeIn, interval):
        return timeIn - timedelta(minutes=timeIn.minute % interval,
                                  seconds=timeIn.second,
                                  microseconds=timeIn.microsecond)