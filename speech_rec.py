import os
# AssemblyAI does the TTS
import assemblyai as aai
# Does Loudness Measurements
import pyloudnorm as pyln
# Converts Wav to Pandas for pyloudnorm
import soundfile as sf
# Does audio editing
from pydub import AudioSegment
# Technically dont need this.  Just for listenback...
from pydub.playback import play

# import dotenv
from dotenv import load_dotenv

load_dotenv()

aai_api_key = os.getenv('aai_api_key')


def transcribe_audio(main_wav_file):
    # Set up transcriber object
    transcriber = aai.Transcriber()
    # Create Transcript of Audio File
    transcript = transcriber.transcribe(main_wav_file)
    return transcript


def auto_censor_timing(transcript, exclusion_word_list):
    # exclusion_word_list should be a list of strings. ["cheese","count"]

    # Find Exclusion Words
    matches = transcript.word_search(exclusion_word_list)
    # Create list for timestamps (tuples) of words
    swear_timestamps_list = []
    for match in matches:
        for timestamp in match.timestamps:
            swear_timestamps_list.append(timestamp)
    # Create a list for the cutting function to slice through
    cut_times = []
    for timestamp_start, timestamp_end in sorted(swear_timestamps_list):
        cut_times.append(timestamp_start)
        cut_times.append(timestamp_end)
    return (cut_times)


def auto_gain_censor_tone(main_wav_file, censor_wav_file):
    # Convert main audio to get gain adjustment
    main_data, main_rate = sf.read(main_wav_file)
    # Create Meter
    meter = pyln.Meter(main_rate)
    # find main audio loudness
    main_loudness = meter.integrated_loudness(main_data)
    # Convert main audio to get gain adjustment
    censor_data, censor_rate = sf.read(censor_wav_file)
    # Create Meter
    meter = pyln.Meter(censor_rate)
    # find main audio loudness
    censor_loudness = meter.integrated_loudness(censor_data)
    beep_gain = censor_loudness-main_loudness
    return beep_gain


def process_cuts(main_wav_file, censor_wav_file, beep_gain, cut_times):
    # in the long term, "cut times" will probably be more complex to better accommodate "good mixing practices" and customizability. 
    
    # Create the AudioSegment object to cut up
    song = AudioSegment.from_wav(main_wav_file)
    
    # Create the AudioSegment object for the Censor soud
    beep = AudioSegment.from_wav(censor_wav_file)
    
    i = 2
    reworked_phrase = []
    beginning_of_phrase = song[0:cut_times[0]]
    new_phrase = beginning_of_phrase
    for cut in range(len(cut_times)-1):
        if i%2 == 1:
            uncensored = song[cut_times[cut]:cut_times[cut+1]]
            # the fade in/out is just to avoid speaker pop...
            reworked_phrase.append(uncensored.fade_in(10).fade_out(10))
            new_phrase = new_phrase.append(uncensored)
        else:
            beep_dur = cut_times[cut+1] - cut_times[cut]
            censored = beep[:beep_dur] - beep_gain
            new_phrase = new_phrase.append(censored.fade_in(10).fade_out(10))
        i+=1
    new_phrase = new_phrase.append(song[cut_times[-1]:])
    with open(f"{main_wav_file[:-4]}_censored.wav", 'wb') as out_f:
        new_phrase.export(out_f, format='wav')