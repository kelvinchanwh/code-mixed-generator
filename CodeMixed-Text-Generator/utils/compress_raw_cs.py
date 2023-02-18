import sys
import glob
import os
import multiprocessing

def compress(input_file_path, output_file_path):
	print ("Processing file {}".format(input_file_path))
	with open (input_file_path, "r") as input_f, open (output_file_path, "w+") as output_f:
		counter = 0
		pre_cache = ""
		post_cache = ""
		cm = ""
		for line in input_f:
			if line.startswith("[BREAK]"):
				output_f.writelines(pre_cache + cm + post_cache + "\n")
				counter = 0
				pre_cache = "[BREAK]\n"
				post_cache = ""
				cm = ""
			elif line.startswith("[CM]"):
				cm += line
			elif line == "\n":
				pass
			elif counter < 3:
				pre_cache += line
				counter += 1
			elif counter == 3:
				post_cache += line
				counter += 1
		output_f.writelines(pre_cache + cm + post_cache + "\n")
	print ("Completed processing file {}. Saved to {}".format(input_file_path, output_file_path))
	if os.path.isfile(input_file_path):
		os.remove(input_file_path)
	else:
		print ("Error: {} not found".format(input_file_path))


if len(sys.argv) != 3:
	print("[USAGE] %s raw_folder_dir output_folder_dir" % sys.argv[0])
	# Eg. python utils/compress_raw_cs.py /data/corpus/parallel/lang8-errorful-train-en-zh-p1-gcm code-mixed-generator/CodeMixed-Text-Generator/data/corpus/parallel/lang8-errorful-train-en-zh-p1-gcm/compressed/
	sys.exit()

input_path = sys.argv[1]
output_path = sys.argv[2]
num_procs = multiprocessing.cpu_count()

files_list = [files for files in os.listdir(input_path) if files.endswith(".raw")]
# files_list = [files for files in files_list if (int(files.split("-")[4].split(".")[0]) >= 20000 and int(files.split("-")[4].split(".")[0]) < 30000)]
procs = [files_list[n:n+num_procs] for n in range(0, len(files_list), num_procs*2)]

os.makedirs(output_path, exist_ok=True)

for j in range(len(procs)):
		print ("Running on {} cpus".format(num_procs))
		gcm_procs = []
		# iterate over all the files of a block and start the generation process
		for file in procs[j]:
			input_file_path = os.path.join(input_path, file)
			output_file_path = os.path.join(output_path, file)
			
			process = multiprocessing.Process(target=compress, args=(input_file_path, output_file_path))
			process.start()
			gcm_procs.append(process)

		# Waits for process completion
		# Kills all processes if a KeyboardInterrupt is recieved
		try:
			for p in gcm_procs:
				p.join()

		except KeyboardInterrupt:
			for p in gcm_procs:
				p.kill()

