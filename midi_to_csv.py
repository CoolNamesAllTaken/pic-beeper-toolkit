import sys
import os
from collections import defaultdict
import py_midicsv

ACCEPTED_EVENTS = ["Note_on_c", "Note_off_c"]
INPUT_DIR = "midi_files"
OUTPUT_DIR = "output_files"

MIDI_TO_HZ = [8.18, 8.66, 9.18, 9.72, 10.3, 10.91, 11.56, 12.25, 12.98, 13.75, 14.57, 15.43, 16.35, 17.32, \
18.35, 19.45, 20.6, 21.83, 23.12, 24.5, 25.96, 27.5, 29.14, 30.87, 32.7, 34.65, 36.71, 38.89, 41.2, 43.65, \
46.25, 49, 51.91, 55, 58.27, 61.74, 65.41, 69.3, 73.42, 77.78, 82.41, 87.31, 92.5, 98, 103.83, 110, 116.54, \
123.47, 130.81, 138.59, 146.83, 155.56, 164.81, 174.61, 185, 196, 207.65, 220, 233.08, 246.94, 261.63, 277.18, \
293.66, 311.13, 329.63, 349.23, 369.99, 392, 415.3, 440, 466.16, 493.88, 523.25, 554.37, 587.33, 622.25, 659.26, \
698.46, 739.99, 783.99, 830.61, 880, 932.33, 987.77, 1046.5, 1108.73, 1174.66, 1244.51, 1318.51, 1396.91, \
1479.98, 1567.98, 1661.22, 1760, 1864.66, 1975.53, 2093, 2217.46, 2349.32, 2489.02, 2637.02, 2793.83, 2959.96, \
3135.96, 3322.44, 3520, 3729.31, 3951.07, 4186.01, 4434.92, 4698.64, 4978.03, 5274.04, 5587.65, 5919.91, 6271.93, \
6644.88, 7040, 7458.62, 7902.13, 8372.02, 8869.84, 9397.27, 9956.06, 10548.08, 11175.3, 11839.82, 12543.85]

ms_per_midi_clock = 0;

def main():
	# rev = []
	# for i in range(len(MIDI_TO_HZ)):
	# 	rev.append([MIDI_TO_HZ[len(MIDI_TO_HZ) - 1 - i]])
	# print(rev)

	# if len(sys.argv) < 2:
	# 	print("Not enough arguments.")
	# 	return

	# midi_filename = sys.argv[0]
	# csv_filename = sys.argv[1]

	midi_filename = os.path.join(INPUT_DIR, "cruel_angels_thesis.mid")
	# strip off everything except the filename
	stripped_filename = midi_filename[midi_filename.rfind(os.path.sep)+1:midi_filename.rfind(".mid")]
	# add folder and .csv extension
	csv_filename = os.path.join(OUTPUT_DIR, stripped_filename + ".csv")

	csv_string = parse_midi_file(midi_filename, csv_filename)
	tracks_dict = build_tracks_dict(csv_string)
	# write_tracks(tracks_dict)
	write_single_note_tracks(tracks_dict)

def parse_midi_file(midi_filename, csv_filename=None):
	"""
	Decompiles a MIDI file into human-readable text
	Inputs:
		midi_filename - name of MIDI file to convert
		csv_filename - name of csv file to output string to (optional), no file output if empty
	Returns:
		csv_string - string of all MIDI lines, according to the midicsv standard
	"""
	csv_string = py_midicsv.midi_to_csv(midi_filename)
	# print(csv_string)

	if csv_filename is not None:
		# output to CSV file
		with open(csv_filename, 'w') as csv_file:
			for line in csv_string:
				csv_file.write(line)

	return csv_string

def build_tracks_dict(csv_string):
	"""
	Supports single-channel, ignores note velocity
	"""
	global ms_per_midi_clock

	tracks_dict = defaultdict(list)

	for i in range(len(csv_string)):
		line = csv_string[i]
		words = line.split(',')
		track = int(words[0])
		time = int(words[1])
		event = (words[2]).strip()

		if event == "Tempo":
			ms_per_midi_clock = int(int(words[3]) / 1000 / 32)

		if event in ACCEPTED_EVENTS:
			# print(event)
			channel = int(words[3])
			note = int(words[4])
			velocity = int(words[5])

			# extend the list of channels with empty lists until current channel has a spot
			while (len(tracks_dict[track]) <= channel):
				tracks_dict[track].append([])

			tracks_dict[track][channel].append([time, note, velocity])
			# tracks_dict[track].append(line[1:])
	
	# print(tracks_dict)
	return tracks_dict

def write_tracks(tracks_dict, stripped_filename=""):
	"""
	Writes the tracks dictionary to a series of text files, one for each track.  Separate sections for each channel
	are written into the individual track text files.
	Inputs:
		tracks_dict - dictionary of dictionaries
		stripped_filename - optional, arbitrary filename to pre-pend to output track file filenames
	"""
	for track_num in tracks_dict.keys():
		output_filename = os.path.join(OUTPUT_DIR, stripped_filename + "_track" + str(track_num))
		with open(output_filename, "w+") as track_file:
			for channel_num in range(len(tracks_dict[track_num])):
				channel = tracks_dict[track_num][channel_num]
				track_file.write("=====BEGIN CHANNEL " + str(channel_num) + "=====\n")
				for command in channel:
					time = command[0]
					note = command[1]
					velocity = command[2]
					track_file.write("time: " + str(command[0]) + " note: " + str(command[1]) + " velocity " + str(command[2]) + "\n")
				track_file.write("=====END CHANNEL " + str(channel_num) + "=====\n")

def write_single_note_tracks(tracks_dict, stripped_filename=""):
	for track_num in tracks_dict.keys():
		output_filename = os.path.join(OUTPUT_DIR, stripped_filename + "_track" + str(track_num))
		with open(output_filename, "w+") as track_file:
			for channel_num in range(len(tracks_dict[track_num])):
				channel = tracks_dict[track_num][channel_num]
				track_file.write("=====BEGIN CHANNEL " + str(channel_num) + "=====\n")

				found_note_start = False
				start_command = None
				end_command = [0, 0, 0] # time=0, note=0, velocity=0
				for command_index in range(len(channel)):
					if start_command == None:
						# use current command as beginning of new note
						start_command = channel[command_index]
						if start_command[0] - end_command[0] > 0:
							# delay since last note
							track_file.write("beeper_wait_duration({});\n".format((start_command[0] - end_command[0]) * ms_per_midi_clock))
					else:
						# finding the end of a note
						curr_command = channel[command_index]
						if (curr_command[1] != start_command[1]):
							# not the same note, skip (if concurrent notes, use first one to start)
							continue
						if (curr_command[2] != 0):
							# velocity is not zero, note is not ending
							continue
						# found end note
						end_command = channel[command_index]
						track_file.write("beeper_play_tone({}, {});\n".format(int(MIDI_TO_HZ[start_command[1]]), (end_command[0] - start_command[0]) * ms_per_midi_clock))

						start_command = None
				track_file.write("=====END CHANNEL " + str(channel_num) + "=====\n")

if __name__ == '__main__':
	main()