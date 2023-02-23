import random
import sys
import nltk
from utils import rcm_std_mean, spf_sampling, frac_std_mean, frac_sampling


def lang_tag(gcm_raw_output, parse_string_src, source_lang, target_lang):
    source_lang = source_lang.upper()
    target_lang = target_lang.upper()
    tagged_strings = []
    
    for i in gcm_raw_output:
        string, parse_string_cm = i[0], i[1]
        tokens = string.split("|||")
        parse_tree = nltk.tree.Tree.fromstring(parse_string_src)
        leaves = parse_tree.leaves()
        tagged_tokens = []
        for token in tokens:
            if token in leaves:
                tagged_tokens.append('{}/{}'.format(token, target_lang))
            else:
                tagged_tokens.append('{}/{}'.format(token, source_lang))
        tagged_strings.append(('|||'.join(tagged_tokens), parse_string_cm))
    return tagged_strings

def post_process(ret, sent1, sent2, alignment, tree, lang1_code, lang2_code, f, k = 1, sampling = "random", rcm_file = None):
	# random sample only if k != -1 and sampling is not spf
	if k !=-1 and len(ret) >= k and sampling != 'spf':
		ret = random.sample(ret, k)
	# word level language tagging
	init_ret = ret.copy()
	try:
		ret = lang_tag(ret, tree, lang1_code, lang2_code)
	except ValueError:
		ret = init_ret
		print ("Could not parse tree, skipping sentence")
		return
	# spf based sampling
	if sampling == 'spf':
		langtags = [lang1_code.upper(), lang2_code.upper()]

		spf_mean, spf_std = rcm_std_mean.main(rcm_file, langtags)
		ret = spf_sampling.rank(ret, langtags, spf_mean, spf_std)

		if len(ret) >= k:
			ret = ret[:k]
	elif sampling == 'frac':
		langtags = [lang1_code.upper(), lang2_code.upper()]

		frac_mean, frac_std = frac_std_mean.main(rcm_file, langtags)
		ret = frac_sampling.rank(ret, langtags, frac_mean, frac_std)

	ret = [cs + (sent1, sent2, alignment) for cs in ret]
	# final generated cm to be added for each input sentence pair
	# outputs.append(ret)
	for j in ret:
		finaloutput = "\n[SENT1]" + j[2] + "\n[SENT2]" + j[3] + "\n[ALIGN]" + j[4] + "\n[CM]" + j[0] + "\n[TREE]" + tree + "\n"
		f.write(finaloutput)
	return ret



if __name__ == "__main__":
	if len(sys.argv) != 7:
		print("[USAGE] %s input_path output_path pregcm_path rcm_path lang1_tag lang2_tag" % sys.argv[0])
		sys.exit()
	input_path = sys.argv[1]
	output_path = sys.argv[2]
	pregcm_path = sys.argv[3]
	rcm_path = sys.argv[4]
	lang1_code = sys.argv[5]
	lang2_code = sys.argv[6]

	with open(input_path, "r") as input_file, open(output_path, "w+") as output_file:
		pregcm = open(pregcm_path, "r").read().split("\n\n")
		tree_dict = dict()
		for sent in pregcm:
			rows = sent.split("\n")
			tree_dict["".join(rows[2].split(" "))] = rows[3]

		sentences = input_file.read().split("\n\n")
		data = list()
		for sent in sentences:
			sent_data = dict()
			cm_list = list()
			try:
				for line in sent.split("\n"):
					if line.startswith("[SENT1]"):
						sent_data["sent1"] = line[7:]
					elif line.startswith("[SENT2]"):
						sent_data["sent2"] = line[7:]
					elif line.startswith("[ALIGN]"):
						sent_data["align"] = line[7:]
					elif line.startswith("[CM]"):
						cm_list.append(line[7:])
					elif line.startswith("[TREE]"):
						sent_data["tree"] = tree_dict["".join(sent_data["sent1"].replace("``", "\"").split(" "))]
			except KeyError:
				print ("Unable to locate tree {}".format("".join(sent_data["sent1"].replace("``", "\"").split(" "))))
				continue
			sent_data["cm"] = [[cm, ""] for cm in cm_list]
			data.append(sent_data)
		
		for sent in data:
			post_process(sent["cm"], sent["sent1"], sent["sent2"], sent["align"], sent["tree"], lang1_code, lang2_code, output_file, k = 1, sampling = "frac", rcm_file = rcm_path)
