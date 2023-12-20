from speech_rec import transcribe_audio
from speech_rec import auto_censor_timing
from speech_rec import auto_gain_censor_tone
from speech_rec import process_cuts


transcript = transcribe_audio("thecount.wav")

exclusion_word_list = ["count"]

cut_times = auto_censor_timing(transcript, exclusion_word_list)

beep_gain = auto_gain_censor_tone("thecount.wav","censor-beep-10.wav")

process_cuts("thecount.wav","censor-beep-10.wav",beep_gain,cut_times)