import os
import subprocess
import sys

from configparser import ConfigParser

def get_config(config_path):
    config = ConfigParser()
    config.read(config_path)
    config_general = config["GENERAL"]
    return config_general

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while True:
        output = process.stdout.readline()
        if process.poll() is not None:
            break
        if output:
            print(output.decode().strip())
    rc = process.poll()
    return rc

if __name__ == "__main__":
    config_path = sys.argv[1]
    config_general = get_config(config_path)
    stages_to_run = config_general["stages_to_run"] if config_general["stages_to_run"] else "pregcm, gcm"
    stages_to_run = stages_to_run.split(",")
    stages_to_run = [x.strip() for x in stages_to_run]

    if "translate" in stages_to_run:
        print("====================\n\nSTARTING TRANSLATOR...\n\n====================")
        p_aligner = run_command(["python", "translate.py", config_path])
    if "aligner" in stages_to_run:
        print("====================\n\nSTARTING ALIGNER...\n\n====================")
        p_aligner = run_command(["python", "aligner.py", config_path])
    if "pregcm" in stages_to_run:
        print("====================\n\nSTARTING PRE-GCM...\n\n====================")
        p_pregcm = run_command(["python", "pre_gcm.py", config_path])
    if "gcm" in stages_to_run:
        print("====================\n\nSTARTING GCM...\n\n====================")
        p_gcm = run_command(["python", "gcm.py", config_path])