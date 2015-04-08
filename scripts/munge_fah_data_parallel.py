from multiprocessing import Pool
import itertools
import time
import numpy as np
import os
import glob
import mdtraj as md
import fahmunge
import pandas as pd

# Reads in a list of project details from a CSV file with Core17/18 FAH projects and munges them.

projects = pd.read_csv("./projects.csv", index_col=0)
output_path = "/data/choderalab/fah/munged/"

def munge(inputs):
    project, location, pdb = inputs
    print(project, location, pdb)
    allatom_output_path = os.path.join(output_path, "all-atoms/", "%s/" % project)
    protein_output_path = os.path.join(output_path, "no-solvent/", "%s/" % project)
    fahmunge.automation.make_path(allatom_output_path)
    fahmunge.automation.make_path(protein_output_path)
    fahmunge.automation.merge_fah_trajectories(location, allatom_output_path, pdb)
    trj0 = md.load(pdb)  # Hacky temporary solution to get protein atoms, fix later.
    top, bonds = trj0.top.to_dataframe()
    protein_atom_indices = top.index[top.chainID == 0].values    
    fahmunge.automation.strip_water(allatom_output_path, protein_output_path, protein_atom_indices)


num_processes = 4
my_pool = Pool(num_processes)

for iteration in itertools.count():
    output = my_pool.map(munge, projects.itertuples())
    print("Finished iteration %d, sleeping." % iteration)
    time.sleep(3600)
