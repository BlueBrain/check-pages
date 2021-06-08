import os
import sys
import json
import shutil

filename = sys.argv[1]
with open(filename) as filein:
    for line in filein.readlines():
        sline = line.strip()
        if sline.startswith("error") or sline.startswith("not found"):
            eline = sline.replace("'", "").replace('"', '')
            print(eline + "\n")
            
            
cwd = os.getcwd()
dir_reports = "/gpfs/bbp.cscs.ch/project/proj12/page_checker/reports"
dir_reports = cwd
build_number = 1#os.environ["BUILD_NUMBER"]
source = os.path.join(cwd, filename)
dest = os.path.join(dir_reports, "report{}.txt".format(build_number))
shutil.copyfile(source, dest)