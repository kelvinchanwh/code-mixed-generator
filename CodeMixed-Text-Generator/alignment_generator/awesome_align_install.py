import urllib.request
import zipfile
import os
import subprocess

def install_awesome_align():

    # fetch awesome_align from github
    url = "https://github.com/neulab/awesome-align/archive/refs/heads/master.zip"
    print("fetching awesome_align from web")
    res = urllib.request.urlopen(url)

    # save the fetched data as a file
    with open("master.zip", "wb") as f:
        f.write(res.read())
    print("extracting awesome_align from downloaded zip file")
    with zipfile.ZipFile("master.zip", "r") as zip_ref:
        zip_ref.extractall(".")

    # create build directory
    os.chdir("awesome-align-master/")

    # setup make
    print("setting up aligner")
    p_setup = subprocess.run(["python", "setup.py", "install"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print((p_setup.stdout).decode())

    # get rid of extra files
    print("awesome-align is successfully installed. Now cleaning up")
    os.chdir("../")
    os.remove("master.zip")
    print("Done.")
    print("Please download model from https://drive.google.com/file/d/1IcQx6t5qtv4bdcGjjVCwXnRkpr67eisJ/view?usp=sharing and add to ./alignment_generator/awesome-align-master/")


if __name__ == "__main__":
    try:
        install_awesome_align()
    except Exception as err:
        print(err)