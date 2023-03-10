import urllib.request
import zipfile
import os
import subprocess
import shutil
import glob

def install_stanford_parser():

    # fetch stanford parser software
    url = "https://nlp.stanford.edu/software/stanford-parser-full-2017-06-09.zip"
    print("fetching stanford parser from web")
    res = urllib.request.urlopen(url)

    # save the fetched data as a file
    with open("parser.zip", "wb") as f:
        f.write(res.read())
    print("extracting stanford parser from downloaded zip file")
    with zipfile.ZipFile("parser.zip", "r") as zip_ref:
        zip_ref.extractall(".")

    # setup the directory for parser
    print("setting up the directory for the parser")
    os.mkdir("stanford_parser_full_2017_06_09")
    for fil in glob.glob("stanford-parser-full-2017-06-09/*"):
      shutil.move(fil, "stanford_parser_full_2017_06_09")
    
    print("renaming jar files")
    os.rename("stanford_parser_full_2017_06_09/stanford-parser.jar", "stanford_parser_full_2017_06_09/stanford-parser-3.8.0.jar")

    # cleaning up
    os.remove("parser.zip")
    os.rmdir("stanford-parser-full-2017-06-09")
    print("Done.")

if __name__ == "__main__":
    try:
        install_stanford_parser()
    except Exception as err:
        print(err)