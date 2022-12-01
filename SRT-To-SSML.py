# This script converts an SRT subtitle files to an SSML file, using the timestamps of the subtitles to accurately create tags for speech timing.
# Note: Many services do not support the 'duration' parameter, so this might not always work as expected.
#
# I offer no warranty or guarantees of any kind. Use at your own risk. I didn't even know what SSML meant a few days ago.
#--------------------------------------------------------------
import re

#------- Basic Options -------
# Path to Subtitles File
srtFile = "subtitles.srt"
# Output file name
outputFile = "SSML.txt"

#------- SSML Options -------
    # Language
language = "en-US"
    # Voice Name - To not specify a voice, put nothing between the quotes or set value to None
voiceName = "en-US-DavisNeural"
    # Duration Attribute Name - The standard name for this attribute within the 'prosody' tag is 'duration', however some services may use their own name, such as Amazon Polly.
    # Default/Standard: "duration"
    # Amazon Polly: "amazon:max-duration"  # See: https://docs.aws.amazon.com/polly/latest/dg/supportedtags.html#maxduration-tag
durationAttributeName = "duration"

#------- Advanced SSML Options -------
    # SSML Version
ssmlVersion = "1.0"
    # Whether to include the xmlns:xsi and xsi:schemaLocation attributes in the <speak> tag.
includeSchemaLocation = True   # Possible Values: True, False
    #schemaLocations
schema_1_0 = "http://www.w3.org/2001/10/synthesis http://www.w3.org/TR/speech-synthesis/synthesis.xsd"
schema_1_1 = "http://www.w3.org/2001/10/synthesis http://www.w3.org/TR/speech-synthesis11/synthesis.xsd"
    # Output File Encoding
chosenFileEncoding = "utf_8_sig" # utf_8_sig for BOM, utf_8 for no BOM
    # Dictionary of xmlns attributes to be added to <speak> tag
    # To not include one, just comment it out
xmlnsAttributesDict = {
    "xmlns": "http://www.w3.org/2001/10/synthesis", # Required! See: https://www.w3.org/TR/speech-synthesis11/#S2.1
    "xmlns:mstts": "http://www.w3.org/2001/mstts", 
    "xmlns:emo": "http://www.w3.org/2009/10/emotionml",
    #"xmlns:xsi":           # Don't uncomment this, refer to "includeSchemaLocation" option above
    #"xsi:schemaLocation":  # Don't uncomment this, refer to "includeSchemaLocation" option above
}


#====================================================================================================
# Sets the schemaLocation attribute based on the SSML version you chose
if includeSchemaLocation:
    xmlnsAttributesDict["xmlns:xsi"] = "http://www.w3.org/2001/XMLSchema-instance"
    if ssmlVersion == "1.0":
        xmlnsAttributesDict["xsi:schemaLocation"] = schema_1_0
    elif ssmlVersion == "1.1":
        xmlnsAttributesDict["xsi:schemaLocation"] = schema_1_1

# Constructs the xmlns attributes string
xmlnsAttributesString = ""
for key, value in xmlnsAttributesDict.items():
    xmlnsAttributesString += f"{key}=\"{value}\" "
xmlnsAttributesString = xmlnsAttributesString.strip() # Remove extra space at end

# --------------- Parse SRT File ---------------
# Open an srt file and read the lines into a list
with open(srtFile, 'r') as f:
    lines = f.readlines()

# Matches the following example with regex:    00:00:20,130 --> 00:00:23,419
subtitleTimeLineRegex = re.compile(r'\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d')

# Create a dictionary
subsDict = {}

# Enumerate lines, and if a line in lines contains only an integer, put that number in the key, and a dictionary in the value
# The dictionary contains the start, ending, and duration of the subtitles as well as the text
# The next line uses the syntax HH:MM:SS,MMM --> HH:MM:SS,MMM . Get the difference between the two times and put that in the dictionary
# For the line after that, put the text in the dictionary
for lineNum, line in enumerate(lines):
    line = line.strip()
    # If line has no text
    if line.isdigit() and subtitleTimeLineRegex.match(lines[lineNum + 1]):
        lineWithTimestamps = lines[lineNum + 1].strip()
        lineWithSubtitleText = lines[lineNum + 2].strip()
        # Create empty dictionary with keys for start and end times and subtitle text
        subsDict[line] = {'start_ms': '', 'end_ms': '', 'duration_ms': '', 'text': '', 'break_until_next': ''}

        time = lineWithTimestamps.split(' --> ')
        time1 = time[0].split(':')
        time2 = time[1].split(':')
        # Converts the time to milliseconds
        processedTime1 = int(time1[0]) * 3600000 + int(time1[1]) * 60000 + int(time1[2].split(',')[0]) * 1000 + int(time1[2].split(',')[1]) #/ 1000 #Uncomment to turn into seconds
        processedTime2 = int(time2[0]) * 3600000 + int(time2[1]) * 60000 + int(time2[2].split(',')[0]) * 1000 + int(time2[2].split(',')[1]) #/ 1000 #Uncomment to turn into seconds
        timeDifferenceMs = str(processedTime2 - processedTime1)
        # Set the keys in the dictionary to the values
        subsDict[line]['start_ms'] = str(processedTime1)
        subsDict[line]['end_ms'] = str(processedTime2)
        subsDict[line]['duration_ms'] = timeDifferenceMs
        subsDict[line]['text'] = lineWithSubtitleText
        if lineNum > 0:
            # Goes back to previous line's dictionary and writes difference in time to current line
            subsDict[str(int(line)-1)]['break_until_next'] = str(processedTime1 - int(subsDict[str(int(line) - 1)]['end_ms']))
        else:
            subsDict[line]['break_until_next'] = '0'

# --------------- Create a new file ---------------
# Make voice tag if applicable
if voiceName is None or voiceName == '' or voiceName.lower() == 'none':
    voiceTag = ''
    voiceTagEnd = ''
else:
   voiceTag = '<voice name="' + voiceName + '">'
   voiceTagEnd = '</voice>'

# Encoding with utf-8-sig adds BOM to the beginning of the file, because use with Azure requires it
with open(outputFile, 'w', encoding=chosenFileEncoding) as f:
    # Write the header
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write(f'<speak {xmlnsAttributesString} version="{ssmlVersion}" xml:lang="{language}">{voiceTag}\n')

    # Write SSML tags with the text and duration from the dictionary
    # Prosody Syntax: https://www.w3.org/TR/speech-synthesis11/#S3.2.4
    for key, value in subsDict.items():
        # Get Break Time
        if not value['break_until_next'] or value['break_until_next'] == '0':
            breakTimeString = ''
        else:
            breakTime = str(value['break_until_next'])
            breakTimeString = f'<break time="{breakTime}ms"/>'

        texToWrite = (f'\t<prosody {durationAttributeName}="{value["duration_ms"]}ms">{value["text"]}{breakTimeString}</prosody>\n')
        # Remove the extra indentation from using triple quotations
        
        f.write(texToWrite)
    f.write(f'{voiceTagEnd}</speak>')

