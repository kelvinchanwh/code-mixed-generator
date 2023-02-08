import subprocess
import sys

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

configs = [
    "config.fce.dev.ini",
    "config.fce.test.ini",
    "config.fce.train.ini",
    "config.locness.dev.ini",
    "config.locess.train.ini",
    "config.nucle.train.ini",
    "config.lang8.train.ini",
    "config.lang8.errorful.train.ini"
]

for config in configs:
    print("====================\n\nRunning Config %s...\n\n===================="%config)
    p_aligner = run_command(["python", "sequence_run.py", config])