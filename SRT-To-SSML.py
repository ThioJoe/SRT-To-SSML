# This script converts an SRT subtitle files to an SSML file, using the timestamps of the subtitles to accurately create tags for speech timing.
# Note: Many services do not support the 'duration' parameter, so this might not always work as expected.
#
# I offer no warranty or guarantees of any kind. Use at your own risk. I didn't even know what SSML meant a few days ago.
#--------------------------------------------------------------
import re

#====================================================================================================
#======================================== USER VARIABLES ============================================
#====================================================================================================

#------- Basic Options -------
# Path to Subtitles File
srtFile = r"subtitles.srt"
# Output file name
outputFile = "SSML.txt"

#------- SSML Options -------
    # Service Mode - Automaticaly adjusts some variables depending on the TTS service
    # Note: Amazon Polly only supports the duration feature on non-neural voices. Only Azure currently supports duration on neural voices.
    # Default: "generic"
serviceMode = "generic" # Possible Values: "azure", "amazon-standard-voice", "generic"
    # Language
language = "en-US"
    # Voice Name - To not specify a voice, put nothing between the quotes or set value to None
voiceName = "en-US-DavisNeural"
    # Whether to escape special characters in the text. Possible Values: True, False
enableCharacterEscape = True

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

# ------- Other Optional Advanced Settings You Probably Don't Need to Worry About -------
    # NOTE: The script will already automatically account for Microsoft Azure and Amazon Polly, but if you are using a different service, you may wish to change this.
    # Duration Attribute Name - The standard name for this attribute within the 'prosody' tag is 'duration', however some services may use their own name.
    # Default/Standard: "duration"
durationAttributeName = "duration"
    # If you are using Azure or Amazon, but want to force force the use of the durationAttributeName instead whatever one would be set autoamtically.
    # You probably don't need to change this.
overrideDurationAttributeName = False # Default: False

# ---- Possibly Helpful Resources -----
# Amazon Polly Duration Tag Info: "amazon:max-duration"  # See: https://docs.aws.amazon.com/polly/latest/dg/supportedtags.html#maxduration-tag

#====================================================================================================
#====================================== Start Program ===============================================
#====================================================================================================

# ---- Prepare variables with correct formatting ----
serviceMode = serviceMode.lower()
useInnerDurationTag = False
# Only need to set this for Amazon, because it isnt used for Azure
if serviceMode == "amazon-standard-voice":
    durationAttributeName = "amazon:max-duration"
elif serviceMode == "azure":
    useInnerDurationTag = True

# If user chooses to override automatic tag
if overrideDurationAttributeName:
    durationAttributeName = overrideDurationAttributeName


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

# Creates function to escape special characters such as: " & ' < >
def escapeChars(enableCharacterEscape, text):
    if enableCharacterEscape:
        text = text.replace("&", "&amp;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&apos;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
    return text


#======================================== Parse SRT File ================================================
# Open an srt file and read the lines into a list
with open(srtFile, 'r', encoding='utf-8-sig') as f:
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

        # If there are more lines after the subtitle text, add them to the text
        count = 3
        while True:
            # Check if the next line is blank or not
            if (lineNum+count) < len(lines) and lines[lineNum + count].strip():
                lineWithSubtitleText += ' ' + lines[lineNum + count].strip()
                count += 1
            else:
                break

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

#=========================================== Create SSML File ============================================
# Make voice tag if applicable
if voiceName is None or voiceName == '' or voiceName.lower() == 'none':
    voiceTag = ''
    voiceTagEnd = ''
else:
   voiceTag = '<voice name="' + voiceName + '">'
   voiceTagEnd = '</voice>'

# Set Up Special Tag If Necessary
if useInnerDurationTag:
    if serviceMode == "azure":
        specialDurationTag = "mstts:audioduration"
else:
    useSpecialDurationTag = None

# Encoding with utf-8-sig adds BOM to the beginning of the file, because use with Azure requires it
with open(outputFile, 'w', encoding=chosenFileEncoding) as f:
    # Write the header
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write(f'<speak {xmlnsAttributesString} version="{ssmlVersion}" xml:lang="{language}">\n')
    # If using Azure, each duration tag must be inside a voice tag, so need to write voice tag later
    if not serviceMode == "azure":
        f.write(f'{voiceTag}\n')

    # Write SSML tags with the text and duration from the dictionary
    # Prosody Syntax: https://www.w3.org/TR/speech-synthesis11/#S3.2.4
    for key, value in subsDict.items():
        # Get Break Time
        if not value['break_until_next'] or value['break_until_next'] == '0':
            breakTimeString = ''
        else:
            breakTime = str(value['break_until_next'])
            breakTimeString = f'<break time="{breakTime}ms"/>'
        
        # Get and escape text, then write
        text = escapeChars(enableCharacterEscape, value['text'])
        # Format each line of text, then write
        if not useInnerDurationTag:
            textToWrite = (f'\t<prosody {durationAttributeName}="{value["duration_ms"]}ms">{text}</prosody>{breakTimeString}\n')
        else:
            textToWrite = (f'\t{voiceTag}<{specialDurationTag}="{value["duration_ms"]}ms"/>{text}{voiceTagEnd}{breakTimeString}\n')
        f.write(textToWrite)

    # Write ending voice tag if applicable
    if not useInnerDurationTag:
        f.write(f'{voiceTagEnd}\n')
    # Write ending speak tag
    f.write('</speak>\n')
