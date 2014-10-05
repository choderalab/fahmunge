import itertools
import time
import numpy as np
import os
import glob
import mdtraj as md
import fahmunge
import siegetank
import pandas as pd

# Reads in a list of project details from a CSV file with Core17/18 FAH projects and munges them.

# TODO: Read from config file
projects = [
    {
        'user_id': 'xxx',
        'target_id': 'xxx'
    },
    {
        'user_id': 'xxx',
        'target_id': 'xxx'
    }
]


output_path = "/data/choderalab/siegetank/munged/"

for iteration in itertools.count():
    for project in projects:

        # LOGIN
        siegetank.login(project.user_id)
        # LOAD TARGET
        target = siegetank.load_target(project.target_id)

        print(project.user_id, location, pdb)


        allatom_output_path = os.path.join(output_path, "all-atoms/", "%s/" % project)
        protein_output_path = os.path.join(output_path, "no-solvent/", "%s/" % project)
        fahmunge.automation.make_path(allatom_output_path)
        fahmunge.automation.make_path(protein_output_path)
        fahmunge.automation.merge_fah_trajectories(location, allatom_output_path, pdb)
        trj0 = md.load(pdb)  # Hacky temporary solution to get protein atoms, fix later.
        top, bonds = trj0.top.to_dataframe()
        protein_atom_indices = top.index[top.chainID == 0].values
        fahmunge.automation.strip_water(allatom_output_path, protein_output_path, protein_atom_indices)
    print("Finished iteration %d, sleeping." % iteration)
    time.sleep(3600)
