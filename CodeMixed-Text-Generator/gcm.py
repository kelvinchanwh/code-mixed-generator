import os
import sys
import logging
import shutil
import time
import cm_text_generator.bench_Merged
import multiprocessing
import tempfile
import random
import functools
import nltk
import subprocess

from configparser import ConfigParser
from utils import rcm_std_mean, spf_sampling 

open_file = functools.partial(open, encoding='utf-8')

def get_config(config_path):
    config = ConfigParser()
    config.read(config_path)
    config_pregcm = config["PREGCM"]
    config_gcm = config["GCM"]
    config_general = config["GENERAL"]
    config_output = config["OUTPUT"]
    return config_pregcm, config_gcm, config_general, config_output

def run_in_try(func, pipe, params):
    try:
        ret = func(params)
    except Exception as e:
        print (e)
        ret = "fail"
    pipe.send(ret)
    pipe.close()

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

def run_sh(inpfile, outfile, source_lang, target_lang, k, lid_output, sampling, lang1_code, lang2_code, rcm_file, linguistic_theory):
    logger = logging.getLogger(__name__)
    working_dir = "{}/cm_text_gnenerator/generator/"
    errfile = '{}.err'.format(inpfile)
    shutil.rmtree("{}onetweet-{}-{}.txt".format(working_dir,
                                                source_lang, target_lang), ignore_errors=True)
    shutil.rmtree(outfile, ignore_errors=True)
    count = 0
    outputs = []
    out_string = ""
    with open_file(inpfile, 'r') as inpfile_f, open(outfile, 'w+') as f:
        for line in inpfile_f.read().split('\n'):
            if line != "":
                out_string += line + '\n'
            else:
                arguments = out_string.split('\n')
                arguments.append(linguistic_theory)
                out_string = ""

                source, dest = multiprocessing.Pipe()
                p = multiprocessing.Process(target=run_in_try, args=(
                    cm_text_generator.bench_Merged.main, source, arguments,))
                p.start()
                t = 10
                timeout = 30
                p.join(t)
                ret = 'fail'
                if p.exitcode is None or p.exitcode >= 0:
                    if dest.poll(timeout):
                        recv = dest.recv()
                        ret = recv[0]
                        sentence_1 = recv[1]
                        sentence_2 = recv[2]
                        alignment = recv[3]
                dest.close()
                p.terminate()

                if type(ret) != str and len(ret) > 0:
                    # random sample only if k != -1 and sampling is not spf
                    if k !=-1 and len(ret) >= k and sampling != 'spf':
                        ret = random.sample(ret, k)
                    # word level language tagging
                    if lid_output == 1:
                        init_ret = ret.copy()
                        try:
                            ret = lang_tag(ret, arguments[3], source_lang, target_lang)
                        except ValueError:
                            ret = init_ret
                            print ("Could not parse tree, skipping sentence")
                            continue
                    # spf based sampling
                    if sampling == 'spf':
                        langtags = [lang1_code.upper(), lang2_code.upper()]

                        spf_mean, spf_std = rcm_std_mean.main(rcm_file, langtags)
                        ret = spf_sampling.rank(ret, langtags, spf_mean, spf_std)

                        if len(ret) >= k:
                            ret = ret[:k]
                    ret = [cs + (sentence_1, sentence_2, alignment) for cs in ret]
                    # final generated cm to be added for each input sentence pair
                    outputs.append(ret)
                    for j in ret:
                        finaloutput = "\n[SENT1]" + j[2] + "\n[SENT2]" + j[3] + "\n[ALIGN]" + j[4] + "\n[CM]" + j[0] + "\n[TREE]" + j[1] + "\n"
                        f.write(finaloutput)
    return outputs


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s: %(funcName)s: %(levelname)s: %(asctime)s: %(message)s",
        handlers=[
            # logging.FileHandler(filename=path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)

    # setup file paths using config file
    config_pregcm, config_gcm, config_general, config_output = get_config(sys.argv[1])
    lang1 = config_general["language_1"] if config_general["language_1"] else "EN"
    lang1_code = lang1.lower()[:2]
    lang2 = config_general["language_2"] if config_general["language_2"] else "ZH-TW"
    lang2_code = lang2.lower()[:2]
    input_loc = config_general["input_loc"] if config_general["input_loc"] else "data"
    pregcm_output_loc = config_pregcm["pregcm_output_loc"] if config_pregcm["pregcm_output_loc"] else lang1_code + "-to-" + lang2_code 
    gcm_input_loc = config_gcm["gcm_input_loc"] if config_gcm["gcm_input_loc"] else pregcm_output_loc
    gcm_output_loc = config_gcm["gcm_output_loc"] if config_gcm["gcm_output_loc"] else lang1_code + "-to-" + lang2_code + "-gcm"
    linguistic_theory = config_gcm["linguistic_theory"] if config_gcm["linguistic_theory"] else "ec"
    k = int(config_gcm["k"]) if config_gcm["k"] else 5
    lid_output = int(config_output["lid_output"]) if config_output["lid_output"] else 0
    sampling = config_output["sampling"] if config_output["sampling"] else "random"
    rcm_file = config_output["rcm_file"] if config_output["rcm_file"] else "rcm_lang_tagged.txt"
    num_procs = int(config_gcm["num_procs"]) if config_gcm["num_procs"] else -1
    num_procs = int(config_gcm["num_procs"]) if int(config_gcm["num_procs"]) > 0 else multiprocessing.cpu_count()

    # for spf sampling, lid tags are required in the output
    if sampling == "spf":
        lid_output = 1

    # setup root directory
    root_dir = os.getcwd()
    logger.info("ROOT DIR: {}".format(root_dir))
    logger.info("generating code mixed sentences")

    # setup input and output directories
    inputdir = os.path.join(input_loc, gcm_input_loc)
    outdir = os.path.join(input_loc, gcm_output_loc)
    while not os.path.exists(inputdir):
        logger.info("{} does not exist".format(inputdir))
        time.sleep(30)
    shutil.rmtree(outdir, ignore_errors=True)
    os.makedirs(outdir)

    # setup initial variables
    count_file = "{}/count".format(inputdir)
    source_lang = lang1_code
    target_lang = lang2_code
    block = 500
    with open_file(count_file, "r") as f:
        end = int(f.read())
    outputs = []

    inputs = list(range(0, end, 500))
    procs = [inputs[n:n+num_procs] for n in range(0, len(inputs), num_procs)]

    for j in range(len(procs)):
        gcm_procs = []
        # iterate over all the files of a block and start the generation process
        for value in procs[j]:
            counter = 0
            while not os.path.exists("{}/flag-cm-{}-{}-{}.txt".format(inputdir, source_lang, target_lang, value)):
                logger.info("Waiting for file starting at {}".format(value))
                time.sleep(30)
                counter += 1
                if counter >10:
                    print ("Timeout waiting for file")
                    raise TimeoutError
            arguments = ['{}/input-cm-{}-{}-{}.txt'.format(inputdir, source_lang, target_lang, value),
                    '{}/out-cm-{}-{}-{}.txt'.format(outdir,
                                                    source_lang, target_lang, value),
                    source_lang,
                    target_lang,
                    k,
                    lid_output,
                    sampling,
                    lang1_code,
                    lang2_code,
                    rcm_file,
                    linguistic_theory,
                    ]
            logger.info("Generating for {} to {}".format(
                value, min(end, value + block)))


            process = multiprocessing.Process(target=run_sh, args=arguments)
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

    # writing the generations to the output file
    # finaloutput = ""
    # for i in outputs:
    #     for j in i:
    #         finaloutput += "\n[SENT1]" + j[2] + "\n[SENT2]" + j[3] + "\n[ALIGN]" + j[4] + "\n[CM]" + j[0] + "\n[TREE]" + j[1] + "\n"
    # outfile = '{}/out-cm-{}-{}.txt'.format(outdir, source_lang, target_lang)
    # with open(outfile, 'w+') as f:
    #     f.write(finaloutput)
    logger.info("Sentence Generation Done")
