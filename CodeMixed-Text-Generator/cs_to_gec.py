import sys
import copy

# %%
def parse_m2(input_m2_path):
	m2_dict = dict()
	with open(input_m2_path) as input_m2:
		# English Sentence
		for line in input_m2:
			line = line.strip()
			if line.startswith('S'):
				line = line[2:]
				S = "".join(line.split(" "))
				m2_dict[S] = {"incorr": line.split(" ")  , "edits":[]}
			elif line.startswith('A'):
				line = line[2:]
				info = line.split("|||")
				info[0] = [int(i) for i in info[0].split(" ")]
				m2_dict[S]["edits"].append(info)
	return m2_dict

# %%
def parse_cs(input_cs_corr_path):
	cs_dict = list()
	with open(input_cs_corr_path) as input_cs_corr:
		for line in input_cs_corr:
			line = line.strip()
			if line.startswith("[SENT1]"):
				line = line[7:]
				S = "".join(line.split(" "))
				cs_dict.append([S, line.split(" ")])
			elif line.startswith("[CM]"):
				line = line[10:]
				cs_word_pair = [word.split("/")[0].split("\\") for word in line.split("|||")]
				cs_list = [False if len(word)==1 else True for word in cs_word_pair]
				cs_dict[-1].extend([cs_word_pair, cs_list])
	return cs_dict

# %%
def get_matching_m2(eng_words, m2):
	matching_m2 = m2["".join(eng_words).replace("``", "\"")]
	return matching_m2["incorr"], matching_m2["edits"]


#%%
def align_edits_to_eng(eng_words, m2_words, m2_edits):
	"""
	
	"""
	for i in range(len(eng_words)):
		if eng_words[i] != m2_words[i]:
			m2_words[i] = m2_words[i] + m2_words[i+1]
			del m2_words[i+1]
			# Edit M2 Edits
			# Check if within range
			for edit in m2_edits:
				if edit[0][0] > i:
					edit[0][0] -= 1
				if edit[0][1] > i:
					edit[0][1] -= 1
				if edit[0][0] == edit[0][1]:
					del edit
			return align_edits_to_eng(eng_words, m2_words, m2_edits)
	return m2_words, m2_edits

#%%
def apply_edit_to_cs(cs_words, cs_list, m2_edits):
	"""
	
	"""
	sid = eid = 0
	prev_sid = prev_eid = -1
	pos = 0
	corrected = list()
	corrected = ['<S>'] + cs_words[:]
	for i in range(len(m2_edits)):
		edit = m2_edits[i]
		sid = int(edit[0][0]) + 1
		eid = int(edit[0][1]) + 1
		error_type = edit[1]
		if error_type == "Um":
			continue
		if sum(cs_list[sid-1:eid-1]) > 0:
			continue
		for idx in range(sid, eid):
			corrected[idx] = ""
		if sid == eid:
			if sid == 0: continue	# Originally index was -1, indicating no op
			if sid != prev_sid or eid != prev_eid:
				pos = len(corrected[sid-1].split())
			cur_words = corrected[sid-1].split()
			cur_words.insert(pos, edit[2])
			pos += len(edit[2].split())
			cur_words = [i for i in cur_words if i != "XXXXX"]
			corrected[sid-1] = " ".join(cur_words)
		else:
			corrected[sid] = edit[2]
			pos = 0
		prev_sid = sid
		prev_eid = eid
	else:
		target_sentence = [word for word in corrected if word != ""]
		assert target_sentence[0].strip() == '<S>', '(' + " ".join(target_sentence) + ')'
		target_sentence = target_sentence[1:]
		return target_sentence

# %%
def align_cs_to_m2(cs_words, cs_list, m2_words):
	words_output = list()
	cs_output = list()
	m2_pointer = 0
	cs_pointer = 0
	while m2_pointer < len(m2_words):
		try:
			en_word = cs_words[cs_pointer][0]
			if cs_list[cs_pointer]:
				cs_word = cs_words[cs_pointer][1]	
			if en_word != m2_words[m2_pointer]:
				# Replace "." with " . " to split dots
				# en_word.replace(".", " . ")
				split_words = en_word.split(" ")
				for word in range(len(split_words)):
					if split_words[word] == m2_words[m2_pointer]:
						if word == len(split_words)-1:
							# Add the whole phrase in the final split for non-splitable terms
							words_output.append(cs_word if cs_list[cs_pointer] else split_words[word])	
						else:
							words_output.append("" if cs_list[cs_pointer] else split_words[word])
						cs_output.append(True if cs_list[cs_pointer] else False)
						m2_pointer += 1
					else:
						found = False
						# Word(s) may be skipped in CS text. Try checking following words
						for i in range(m2_pointer+1, len(m2_words)):
							# Additional loop to jump to the next match
							if split_words[word] == m2_words[i]:
								words_output.extend(["XXXXX"]*(i-m2_pointer))
								cs_output.extend([True]*(i-m2_pointer)) # Prevent m2 edit in these regions
								m2_pointer = i
								cs_pointer -= 1 # Offset the upcoming +1
								found = True
								break
						if found == False and cs_list[cs_pointer]:
							# if in CS component and word not found, it may be due to alternative grammar in CS component
							# print ("%s Not found, trying again"%split_words[word])
							for i in range(0, len(m2_words), -1):
								# Additional loop to jump to the next match
								if split_words[word] == m2_words[i]:
									words_output.extend(["XXXXX"]*(i-m2_pointer))
									cs_output.extend([True]*(i-m2_pointer)) # Prevent m2 edit in these regions
									m2_pointer = i
									cs_pointer -= 1 # Offset the upcoming +1
									break
				cs_pointer += 1
			else:
				words_output.append(cs_word if cs_list[cs_pointer] else en_word)	
				cs_output.append(True if cs_list[cs_pointer] else False)
				m2_pointer += 1
				cs_pointer += 1
			
					
		except IndexError:
			# print ("English sentence does not match CS Sentence")
			# print ("Missing: " + str(m2_words[m2_pointer]))
			# print ("M2: " + str("|||".join(m2_words)))
			# print ("CS: " + str("|||".join([cs[0] for cs in cs_words])))
			# print ("WORDS: " + str("|||".join(words_output)))
			return words_output, cs_output

	return words_output, cs_output


#%%

def main():
	input_cs_corr_path = sys.argv[1]
	input_m2_path = sys.argv[2]
	output_cs_incorr_path = sys.argv[3]
	output_cs_corr_path = sys.argv[4]
	# max_missing_ratio = float(sys.argv[5])

	m2 = parse_m2(input_m2_path)
	cs = parse_cs(input_cs_corr_path)

	corr_cs = list()
	incorr_cs = list()
	with open(output_cs_incorr_path, 'w+') as output_cs_incorr, open(output_cs_corr_path, 'w+') as output_cs_corr:
		for item in cs:
			eng_words = item[1]
			cs_words = item[2]
			cs_list = item[3]
			# print(eng_words)
			try:
				m2_words, m2_edits = get_matching_m2(eng_words, m2)
			except KeyError:
				print ("Key '%s' not found"%("".join(eng_words)))
				continue
			try:
				initial_m2_words = copy.deepcopy(m2_words)
				initial_m2_edits = copy.deepcopy(m2_edits)
				eng_words, m2_edits = align_edits_to_eng(eng_words, m2_words, m2_edits)
			except IndexError:
				m2_words = initial_m2_words
				m2_edits = initial_m2_edits

			cs_words, cs_list = align_cs_to_m2(cs_words, cs_list, m2_words)

			# if (cs_words.count("XXXXX")/len(cs_words)) <= max_missing_ratio:
				# Check if max edit is within cs_words list
			if max([m2_edit[0][1] for m2_edit in m2_edits]) <= len(cs_list):
				incorr = apply_edit_to_cs(cs_words, cs_list, m2_edits)

				# Remove empty words and "XXXXX" placeholders
				corr = [i for i in cs_words if (i != "" and i != "XXXXX")]
				incorr = [i for i in incorr if (i != "" and i != "XXXXX")]

				corr = " ".join(corr)
				incorr = " ".join(incorr)

				output_cs_incorr.write(incorr + '\n')
				output_cs_corr.write(corr + '\n')

				incorr_cs.append(incorr)
				corr_cs.append(corr)
			else:
				print ("Sentence is shorter than m2 edit")
				print ("M2: " + str("|||".join(m2_words)))
				print ("CS: " + str("|||".join(cs_words)))
			# else:
			# 	print ("Sentence has too many missing words")
			# 	print ("M2: " + str("|||".join(m2_words)))
			# 	print ("CS: " + str("|||".join(cs_words)))

		# check if both files are of equal length
		assert len(incorr_cs) == len(corr_cs), "Parallel sentences do not have equal length"

# Run the program
if __name__ == "__main__":
	if len(sys.argv) != 5:
		print("[USAGE] %s input_cs_corr input_m2_file output_cs_incorr output_cs_corr" % sys.argv[0])
		sys.exit()

	main()
