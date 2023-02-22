from collections import Counter
import sys
import re
import jieba
import nagisa
import time
from konlpy.tag import Komoran

lang_unicodes = [
	('\u0000','\u007F'),
	('\u0080','\u00FF'),
	('\u0100','\u017F'),
	('\u0180','\u024F'),
	('\u0250','\u02AF'),
	('\u02B0','\u02FF'),
	('\u0300','\u036F'),
	('\u1E00','\u1EFF'),
	('\u2C60','\u2C7F'),
	('\uA720','\uA7FF'),
	('\u1D00','\u1D7F'),
	('\u1D80','\u1DBF'),
	('\u3000','\u303F') # CJK Punctuation
	]

# define the set of punctuations to add spaces before and after
all_punctuations = set([chr(code_point) for code_point in range(0x2000, 0x2070)])
all_punctuations.update(['!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', '{', '|', '}', '~'])

def add_spaces(text):

	# use regular expressions to add spaces before and after each punctuation
	for p in list(all_punctuations):
		pattern = re.escape(p)
		replace = ' {} '.format(p)
		text = re.sub(pattern, replace, text)

	# remove any double spaces that may result from adding spaces around punctuation
	text = re.sub(r' {2,}', ' ', text)

	return text


def dect_word_latin(word):
	latin = 0
	nonlatin = 0
	for ch in word:
		isLatin = False
		for block in lang_unicodes:
			if ch >= block[0] and ch <= block[1]:
				isLatin = True
				break
		if isLatin == False:
			nonlatin += 1
		else:
			latin += 1
			
	assert latin + nonlatin == len(word), "{} does not have total count of {} latin + {} non-latin chars".format(word, latin, nonlatin)
	return True if latin > nonlatin else False

def tokenize(sentence, lang):
	if "ch" in lang.lower():
		tokens = list(filter(lambda a: a != " ", jieba.lcut(sentence)))
	elif "ja" in lang.lower():
		tokens = list(filter(lambda a: a != "\u3000", nagisa.tagging(sentence).words))
	elif "ko" in lang.lower():
		tokenizer = Komoran()        
		tokens = tokenizer.morphs(add_spaces(sentence))
	else:
		tokens = sentence.split()
	return " ".join(tokens)


def create_cslang_list(words_list):
	output = list()
	for words in words_list:
		output.append(dect_word_latin(words))
	return output
  
if __name__ == "__main__":
	if len(sys.argv) != 5:
		print("[USAGE] %s input_rcm_file output_rcm_file lang1_tag lang2_tag" % sys.argv[0])
		sys.exit()

	input_rcm_file = sys.argv[1]
	output_rcm_file = sys.argv[2]
	lang1_tag = sys.argv[3]
	lang2_tag = sys.argv[4]

	with open(input_rcm_file, "r") as input_f, open(output_rcm_file, "w+") as output_f:
		sentences = input_f.read().split("\n")
		sentences = [tokenize(sent.replace("\u3000", " "), lang2_tag) for sent in sentences]
		cs_list = [create_cslang_list(sentence.split(" ")) for sentence in sentences]
		for sentence, sent_list in zip(sentences, cs_list):
			write_str  = ""
			for word, cs in zip(sentence.split(" "), sent_list):
				cs_out = lang1_tag if cs else lang2_tag
				write_str += word + "/" + cs_out + " "
			output_f.writelines(write_str.strip() + "\n")