# SVtoWave
Time Synchronised Sampled Values (SV) to WAVE file.

The OpenPMU ADC produces time synchronised sampled values (SV) in a manner similar to that of IEC 61850-9-2 merging units [^1].  The analogue-to-digital converter's sampling clock is strictly disciplined to GNSS derived time [^2].

The SVtoWave software stores this time synchronised waveform data in standard audio file formats.  This has advantages in terms of ease of use of the data for later analysis, since these files can be opened in a variety of environments, including Python.  Audio compression may be used to reduce file sizes.

The filenames include a timestamp which indicates the time that the first SV in the file was acquired.  The sampling rate is continuous, so the time of all subsequent SVs can be extrapolated.  If there is any data loss, for example due to network failures, then SVtoWave will pad the missing section of the fill so that when data acquisition resumes the SVs are in the correct position in the file.

## Configuration

Configuration changes are made via the `'config.json'` file.

Labels are largely self descriptive.  You may want to change:

`"recMask": [0,4]`
-  This is the "recording mask" which tells the software which channels you are interested in.  In this example, channels `0` and `4` from the ADC will be recorded, and any other channel data will be discarded.  This is useful when some of the ADC inputs are not connected, and recording noise would waste disk space.  If left blank, `[]`, then all channels are recorded.

`"allowDeletion": True`
-  This gives the code permission to delete old records on disk

`"daysToKeep": 7`
-  This is the number of days of data to keep (excluding the current day).  The larger this number is, the more storage will be required.  Requires `"allowDeletion"`.

## Help the project

If you would like to support this project, citing our papers would be a great help.  If you would like to cotribute to the project, please get in touch with the authors.

[^1]: X. Zhao, D. M. Laverty, A. McKernan, D. J. Morrow, K. McLaughlin and S. Sezer, "GPS-Disciplined Analog-to-Digital Converter for Phasor Measurement Applications," in IEEE Transactions on Instrumentation and Measurement, vol. 66, no. 9, pp. 2349-2357, Sept. 2017, doi: 10.1109/TIM.2017.2700158. https://ieeexplore.ieee.org/document/7931698
[^2]: P. Tosato, D. Macii, D. Fontanelli, D. Brunelli and D. Laverty, "A Software-based Low-Jitter Servo Clock for Inexpensive Phasor Measurement Units," 2018 IEEE International Symposium on Precision Clock Synchronization for Measurement, Control, and Communication (ISPCS), 2018, pp. 1-6, doi: 10.1109/ISPCS.2018.8543082. https://ieeexplore.ieee.org/abstract/document/8543082
