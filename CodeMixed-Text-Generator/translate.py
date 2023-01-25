import os
import logging
import re
import time
import jieba
import nagisa
from konlpy.tag import Komoran


from configparser import ConfigParser
from googletrans import Translator

def get_config():
    config = ConfigParser()
    config.read("config.ini")
    config_general = config["GENERAL"]
    config_translate = config["TRANSLATE"]
    return config_general, config_translate

def read_data(input_loc, lang1_in_file):
    with open(os.path.join(input_loc, lang1_in_file), "r") as f:
        lang1_in = f.read().strip().split("\n")
    return lang1_in

def clean_sentence(sent):
    return re.sub(r"[()]", "", re.sub(r"\s+", " ", re.sub(r"([?!,.])", r" \1 ", sent))).strip()

def translate(translator, lang1_code, lang2_code, lang1_in):
    success = False
    while success == False:
        try:
            translations = translator.translate(lang1_in, src=lang1_code, dest=lang2_code)
            success = True
        except Exception as e:
            logger.error(e)
            time.sleep(10)
    return translations

def divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield lang1_in[i:i+n]

def translate_batch(lang1_code, lang2_code, lang1_in, lang2_op_file, max_len=500):
    translations = list()
    translator = Translator()

    lang1_chunks = list(divide_chunks(lang1_in, max_len))
    logger.info("Translating %d chunks"%(len(lang1_chunks)))
    
    for chunk in range(len(lang1_chunks)):
        batch = translate(translator, lang1_code, lang2_code, lang1_chunks[chunk])
        logger.info("Translated %d/%d batches"%(chunk+1, len(lang1_chunks)))

        # Additional tokenization for CJK languages
        if "zh" in lang2_code:
            batch = [list(filter(lambda a: a != " ", jieba.lcut(sentence.text))) for sentence in batch]
        elif "ja" in lang2_code:
            batch = [list(filter(lambda a: a != "\u3000", nagisa.tagging(sentence.text).words)) for sentence in batch]
        elif "ko" in lang2_code:
            tokenizer = Komoran()        
            batch = [tokenizer.morphs(sentence.text) for sentence in batch]


        translations.extend(batch)


    assert len(lang1_in) == len(translations)
    os.makedirs(output_loc, exist_ok=True)
    with open(os.path.join(output_loc, lang2_op_file), "w+") as f:
        for translation in translations:
            # print (translation.text)
            f.writelines(" ".join(translation) + "\n")

if __name__ == "__main__":

    # setup logging
    logger = logging.getLogger(__name__)
    # setup file paths using config file
    config_general, config_translate = get_config()
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


    # Learn alignments on all sentences
    translate_batch(lang1_code, lang2_code, lang1_in, lang2_op_file)
