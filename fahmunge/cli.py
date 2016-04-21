import itertools
import time
import numpy as np
import os
import glob
import mdtraj as md
import pandas as pd
import argparse
import sys

import fahmunge

# Reads in a list of project details from a CSV file with Core17/18 FAH projects and munges them.

def main():
    description = 'Munge FAH data'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-p', '--projects', metavar='PROJECTFILE', dest='projectfile', action='store', type=str, default=None,
        help='CSV file containing (project,filepath,pdbfile) tuples')
    parser.add_argument('-o', '--outpath', metavar='OUTPATH', dest='output_path', action='store', type=str, default=None,
        help='Output pathname for munged data')
    parser.add_argument('-n', '--nprocesses', metavar='NPROCESSES', dest='nprocesses', action='store', type=int, default=1,
        help='For parallel processing, number of processes to use')
    parser.add_argument('-v', dest='verbose', action='store_true', default=False,
        help='Turn on debug output')
    parser.add_argument('-t', '--time', metavar='TIME', dest='time_limit', action='store', type=int, default=None,
        help='Process each project for no more than specified time (in seconds) before moving on to next project')
    parser.add_argument('-m', '--maxits', metavar='MAXITS', dest='maximum_iterations', action='store', type=int, default=None,
        help='Perform specified number of iterations and exist (default: no limit, process indefinitely)')
    parser.add_argument('-s', '--sleeptime', metavar='SLEEPTIME', dest='sleep_time', action='store', type=int, default=3600,
        help='Sleep for specified time (in seconds) between iterations (default: 3600)')
    parser.add_argument('--version', action='store_true', default=False,
        help='Print version information and exit')
    args = parser.parse_args()

    if args.version:
        print(fahmunge.version)
        sys.exit(0)

    # Check arguments
    if args.projectfile == None:
        print('ERROR: projectfile must be specified\n\n')
        parser.print_help()
        sys.exit(1)
    if args.output_path == None:
        print('ERROR: outpath must be specified\n\n')
        parser.print_help()
        sys.exit(1)
    if args.nprocesses <= 0:
        print('ERROR: nprocesses must be positive\n\n')
        parser.print_help()
        sys.exit(1)

    # Read project tuples.
    projects = pd.read_csv(args.projectfile, index_col=0)

    # Process for specified length of time.
    iteration = 0
    while((args.maximum_iterations==None) or (iteration < args.maximum_iterations)):
        for (project, location, pdb) in projects.itertuples():

            if args.verbose:
                print('----------' * 8)
                print('Processing project %s' % project)
                print(project, location, pdb)
                print('----------' * 8)

            # Form output paths
            allatom_output_path = os.path.join(args.output_path, "all-atoms/", "%s/" % project)
            protein_output_path = os.path.join(args.output_path, "no-solvent/", "%s/" % project)

            # Make sure output paths exist
            fahmunge.automation.make_path(allatom_output_path)
            fahmunge.automation.make_path(protein_output_path)

            # Munge data
            fahmunge.automation.merge_fah_trajectories(location, allatom_output_path, pdb, nprocesses=args.nprocesses, maxtime=args.time_limit)
            fahmunge.automation.strip_water(allatom_output_path, protein_output_path, nprocesses=args.nprocesses, maxtime=args.time_limit)

        # Report progress.
        if (args.maximum_iterations == None):
            print("Finished iteration %d, sleeping for %d seconds." % (iteration, args.sleep_time))
        else:
            print("Finished iteration %d / %d, sleeping for %d seconds." % (iteration, args.maximum_iterations, args.sleep_time))

        # Iteration is successful
        iteration += 1

        # Exit now if specified number of iterations is reached
        if (iteration >= args.maximum_iterations):
            return

        # Sleep.
        time.sleep(args.sleep_time)
