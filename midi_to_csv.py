import sys
import os
from collections import defaultdict
import py_midicsv

ACCEPTED_EVENTS = ["Note_on_c", "Note_off_c"]
INPUT_DIR = "midi_files"
OUTPUT_DIR = "output_files"

def main():
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
	tracks_dict = defaultdict(list)

	for i in range(len(csv_string)):
		line = csv_string[i]
		words = line.split(',')
		track = int(words[0])
		time = int(words[1])
		event = words[2]

		if event.strip() in ACCEPTED_EVENTS:
			# print(event)
			channel = int(words[3])
			note = int(words[4])
			velocity = int(words[5])

			# extend the list of channels with empty lists until current channel has a spot
			while (len(tracks_dict[track]) <= channel):
				tracks_dict[track].append([])

			tracks_dict[track][channel].append([time, note, velocity])
			# tracks_dict[track].append(line[1:])
	
	print(tracks_dict)
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
							track_file.write("beeper_wait_duration({});\n".format(start_command[0] - end_command[0]))
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
						track_file.write("beeper_play_tone({}, {});\n".format(start_command[1], end_command[0] - start_command[0]))

						start_command = None
				track_file.write("=====END CHANNEL " + str(channel_num) + "=====\n")

if __name__ == '__main__':
	main()