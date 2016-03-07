from multiprocessing import Pool
import itertools
import time
import numpy as np
import os
import glob
import mdtraj as md
import fahmunge
import pandas as pd
import signal
import sys

# Reads in a list of project details from a CSV file with Core17/18 FAH projects and munges them.

projects = pd.read_csv("./projects.csv", index_col=0)
output_path = "/data/choderalab/fah/munged-with-time/"
nprocesses = 16

for iteration in itertools.count():
    for (project, location, pdb) in projects.itertuples():
        print(project, location, pdb)
        allatom_output_path = os.path.join(output_path, "all-atoms/", "%s/" % project)
        protein_output_path = os.path.join(output_path, "no-solvent/", "%s/" % project)
        fahmunge.automation.make_path(allatom_output_path)
        fahmunge.automation.make_path(protein_output_path)
        fahmunge.automation.merge_fah_trajectories(location, allatom_output_path, pdb, nprocesses=nprocesses)
        fahmunge.automation.strip_water(allatom_output_path, protein_output_path, nprocesses=nprocesses)
    print("Finished iteration %d, sleeping." % iteration)
    time.sleep(3600)
