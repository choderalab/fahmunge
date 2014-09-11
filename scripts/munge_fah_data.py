import itertools
import time
import numpy as np
import os
import glob
import mdtraj as md
import fahmunge
import pandas as pd

projects = pd.read_csv("./projects.csv", index_col=0)
output_path = "/data/choderalab/fah/munged/"

for iteration in itertools.count():
    for (project, location, pdb) in projects.itertuples():
        print(project, location, pdb)
        allatom_output_path = os.path.join(output_path, "allatoms/", "%s/" % project)
        protein_output_path = os.path.join(output_path, "protein/", "%s/" % project)
        fahmunge.automation.make_path(allatom_output_path)
        fahmunge.automation.make_path(protein_output_path)
        fahmunge.automation.merge_fah_trajectories(location, allatom_output_path, pdb)
        trj0 = md.load(pdb)  # Hacky temporary solution to get protein atoms, fix later.
        top, bonds = trj0.top.to_dataframe()
        protein_atom_indices = top.index[top.chainID == 0].values    
        fahmunge.automation.strip_water(allatom_output_path, protein_output_path, protein_atom_indices)
    time.sleep(3600)
