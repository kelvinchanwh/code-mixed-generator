import os
import logging
import re
import sys
import time
import jieba
import nagisa
import time
from konlpy.tag import Komoran


from configparser import ConfigParser
from googletrans import Translator
import multiprocessing as mp

def get_config(config_path):
    config = ConfigParser()
    config.read(config_path)
    config_general = config["GENERAL"]
    config_translate = config["TRANSLATE"]
    return config_general, config_translate

def read_data(input_loc, lang1_in_file):
    with open(os.path.join(input_loc, lang1_in_file), "r") as f:
        lang1_in = f.read().strip().split("\n")
    return lang1_in

def clean_sentence(sent):
    return re.sub(r"[()]", "", re.sub(r"\s+", " ", re.sub(r"([?!,.])", r" \1 ", sent))).strip()

def translate(lang1_code, lang2_code, lang1_in, lang1_counter):
    translator = Translator()
    success = False
    while success == False:
        try:
            batch = translator.translate(lang1_in, src=lang1_code, dest=lang2_code)
            success = True
        except Exception as e:
            logger.error(e)
            time.sleep(10)

    translated_batch = [bat.text.split("\n") for bat in batch]
    translated_batch = [sent for line in translated_batch for sent in line]
    timediff = time.time() - starttime
    logger.info("Translated Batch %d. Elapsed time: %d sec"%(lang1_counter+1, timediff))

    return translated_batch

def divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i+n]

def translate_batch(lang1_code, lang2_code, lang1_in, lang2_op_file, max_len=500):
    global starttime
    starttime = time.time()
    translations = list()
    batch_string = list()

    string = lang1_in[0]
    for v in lang1_in[1:]:
        if (len(string) + len(' \n ') + len(v) <= 4800):
            string = string + ' \n ' + v
            if v == lang1_in[-1]:
                batch_string.append(string)
        else:
            batch_string.append(string)
            string = v

    lang1_chunks = list(divide_chunks(batch_string, max_len))
    logger.info("Translating %d chunks"%(len(lang1_chunks)))
    
    os.makedirs(output_loc, exist_ok=True)
    with open(os.path.join(output_loc, lang2_op_file), "w+") as f:
        # with concurrent.futures.ThreadPoolExecutor() as executor: # In this case thread would be better
        #     batch = executor.map(translate, [lang1_code], [lang2_code], lang1_chunks, lang1_counter)
            
        pool = mp.Pool(mp.cpu_count())
        batches = pool.starmap(translate, [(lang1_code, lang2_code, lang1_chunk, lang1_counter) for (lang1_counter, lang1_chunk) in enumerate(lang1_chunks)])

        translations = [sent for batch in batches for sent in batch]

        translatetime = time.time()-starttime
        print("Total Translate Time: %d"%(translatetime))

        # Additional tokenization for CJK languages
        if "zh" in lang2_code:
            translations = [list(filter(lambda a: a != " ", jieba.lcut(sentence))) for sentence in translations]
        elif "ja" in lang2_code:
            translations = [list(filter(lambda a: a != "\u3000", nagisa.tagging(sentence).words)) for sentence in translations]
        elif "ko" in lang2_code:
            tokenizer = Komoran()        
            translations = [tokenizer.morphs(sentence) for sentence in translations]
        else:
            translations = [[sentence] for sentence in translations]   

        for translation in translations:
            # print (translation.text)
            f.writelines(" ".join(translation) + "\n")

        print("Total Tokenization Time: %d"%(time.time()-translatetime-starttime))

        assert len(lang1_in) == len(translations), "Input length (%d) does not match output length (%d)"%(len(lang1_in), len(translations))

if __name__ == "__main__":

    # setup logging
    logger = logging.getLogger(__name__)
    # setup file paths using config file
    config_general, config_translate = get_config(sys.argv[1])
    lang1 = config_translate["language_1"] if config_translate["language_1"] else "EN"
    lang1_code = lang1.lower()
    lang2 = config_translate["language_2"] if config_translate["language_2"] else "ZH-TW"
    lang2_code = lang2.lower()
    input_loc = config_general["input_loc"] if config_general["input_loc"] else "data"
    output_loc = config_general["output_loc"] if config_general["output_loc"] else "data"
    lang1_in_file = config_translate["source_inp_file"] if config_translate["source_inp_file"] else lang1_code + "-to-" + lang2_code + "-input_lang1"
    lang2_op_file = config_translate["target_op_file"] if config_translate["target_op_file"] else lang1_code + "-to-" + lang2_code + "-input_lang2"

    # read data
    lang1_in = read_data(input_loc, lang1_in_file)
    logger.info("Read Input File Complete")
    
    # clean data
    for i in range(len(lang1_in)):
        lang1_in[i] = clean_sentence(lang1_in[i])
    logger.info("Clean Data Complete")

    # Remove empty lines
    lang1_in = [sent for sent in lang1_in if sent != ""]
    
    # Learn alignments on all sentences
    translate_batch(lang1_code, lang2_code, lang1_in, lang2_op_file)

    with open(os.path.join(output_loc, lang1_in_file), "w+") as in_f:
        for sent in lang1_in:
            # print (translation.text)
            in_f.writelines(sent + "\n")
