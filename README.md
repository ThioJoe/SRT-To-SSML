# SRT-To-SSML
 Converts SRT subtitle file to SSML file with speech durations. 

### Use Cases
- Enables automated translation and dubbing of videos while keeping the dub in sync. You can simply translate the text portions of the subtitles before feeding it into the script. This allows the translations of each line remain the same length of the original speech, so the generated speech should theoretically be a drop-in replacement of the original.

### How it Works:
- It takes the text lines from the subtitle file and puts each on a separate line within the `speak` tag
- It takes the timestamps for the start/end for each subtitle line, and calculates that time difference in milliseconds. Then uses that for the `duration` attribute for the `prosody` tag. This tells the TTS how long it should take to say the line, so it will stay in sync with the original video.
  - Warning: Not many neural TTS services support this duration feature, so this may not work as expected.
- It also calculates the time difference between the end of one subtitle line and the beginning of the next, and uses that as the `time` attribute for the `break` tag at the end of each text line. This is also to keep it in sync with the original video.

### SSML Options Changeable With Variables
- Language
- TTS Voice Name
- SSML Version
- xmlns Attributes for <speak> tag
- Whether to include the `xmlns:xsi` and `xsi:schemaLocation` attributes
- Input and Output file names (Defaults: `subtitles.srt` for input and `SSML.txt` for output)

# Example
### Input (SRT Subtitle File)
```
1
00:00:00,140 --> 00:00:05,050
This is an example of a subtitle file with a bunch of random words I've added with various timestamps.

2
00:00:05,240 --> 00:00:13,290
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim

3
00:00:13,480 --> 00:00:14,250
veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

4
00:00:14,340 --> 00:00:19,930
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat

5
00:00:20,130 --> 00:00:23,419
nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia.
```


### Output
```
<?xml version="1.0" encoding="UTF-8"?>
<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.w3.org/2001/10/synthesis http://www.w3.org/TR/speech-synthesis/synthesis.xsd" version="1.0" xml:lang="en-US"><voice name="en-US-DavisNeural">
	<prosody duration="4910ms">This is an example of a subtitle file with a bunch of random words I've added with various timestamps.<break time="190ms"/></prosody>
	<prosody duration="8050ms">Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim<break time="190ms"/></prosody>
	<prosody duration="770ms">veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.<break time="90ms"/></prosody>
	<prosody duration="5590ms">Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat<break time="200ms"/></prosody>
	<prosody duration="3289ms">nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia.</prosody>
</voice></speak>
```
