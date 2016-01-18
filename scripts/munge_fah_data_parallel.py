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
output_path = "/data/choderalab/fah/munged_test/"
num_processes = 10

def init_work():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def munge(inputs):
    project, location, pdb = inputs
    print(project, location, pdb)
    allatom_output_path = os.path.join(output_path, "all-atoms/", "%s/" % project)
    protein_output_path = os.path.join(output_path, "no-solvent/", "%s/" % project)
    fahmunge.automation.make_path(allatom_output_path)
    fahmunge.automation.make_path(protein_output_path)
    fahmunge.automation.merge_fah_trajectories(location, allatom_output_path, pdb)
    fahmunge.automation.strip_water(allatom_output_path, protein_output_path)


if __name__ == "__main__":

    print "Creating thread pool..."
    pool = Pool(num_processes, init_work)
    for iteration in itertools.count():
        print "Starting asynchronous map operations..."
        job = pool.map_async(munge, projects.itertuples())

        while(not job.ready()):
            try:
                print "Sleeping for 10 seconds..."
                time.sleep(10)
            except KeyboardInterrupt:
                print "Caught KeyboardInterrupt, terminating workers"
                pool.terminate()
                pool.join()
                sys.exit(1)

        output = job.get()
        print output

        print("Finished iteration %d, sleeping." % iteration)
        time.sleep(3600)