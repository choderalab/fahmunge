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
    parser.add_argument('--validate', dest='validate_topology_selection', action='store_true', default=False,
        help='Validate topology_selection in CSV projects file is valid')
    parser.add_argument('-o', '--outpath', metavar='OUTPATH', dest='output_path', action='store', type=str, default=None,
        help='Output pathname for munged data')
    parser.add_argument('-n', '--nprocesses', metavar='NPROCESSES', dest='nprocesses', action='store', type=int, default=1,
        help='Number of threads to use (default: 1)')
    parser.add_argument('-d', '--debug', dest='verbose', action='store_true', default=False,
        help='Turn on debug output')
    parser.add_argument('-t', '--time', metavar='TIME', dest='time_limit', action='store', type=int, default=None,
        help='Process each project for no more than specified time (in seconds) before moving on to next project')
    parser.add_argument('-m', '--maxits', metavar='MAXITS', dest='maximum_iterations', action='store', type=int, default=None,
        help='Perform specified number of iterations and exist (default: no limit, process indefinitely)')
    parser.add_argument('-s', '--sleeptime', metavar='SLEEPTIME', dest='sleep_time', action='store', type=int, default=0,
        help='Sleep for specified time (in seconds) between iterations (default: 0)')
    parser.add_argument('-v', '--version', action='store_true', default=False,
        help='Print version information and exit')
    args = parser.parse_args()

    if args.version:
        print(fahmunge.__version__)
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

    # Read project tuples
    projects = pd.read_csv(args.projectfile, index_col=0)

    # Check that all locations and PDB files exist, raising an exception if they do not (indicating misconfiguration)
    # TODO: Parallelize validation by entry?
    print('Validating contents of project CSV file...')
    for (project, location, pdb, topology_selection) in projects.itertuples():
        # Check project path exists.
        if not os.path.exists(location):
            raise Exception("Project %s: Cannot find data path '%s'. Check that you specified the correct location." % (project, location))
        # Check PDB file(s) exist
        # TODO: Check atom counts match?
        # TODO: Generalize with a generator for iterating over all RUN/CLONEs?
        n_runs, n_clones = fahmunge.automation.get_num_runs_clones(location)
        print("Project %s: %d RUNs %d CLONEs found; topology_selection = '%s'" % (project, n_runs, n_clones, topology_selection))
        if '%' in pdb:
            # perform filename substitution on all RUNs
            pdb_filenames_to_check = list()
            for run in range(n_runs):
                pdb_filename = pdb % vars()
                pdb_filenames_to_check.append(pdb_filename)
        else:
            pdb_filenames_to_check = [ pdb ] # just one filename
        for pdb_filename in pdb_filenames_to_check:
            pdb_filename = pdb % vars()
            if not os.path.exists(pdb_filename):
                raise Exception("Project %s: PDB filename specified as '%s' but '%s' was not found. Check that you specified the correct path and PDB files are present." % (project, pdb, pdb_filename))
            if args.validate_topology_selection:
                # Check toplogy selection is valid.
                # TODO: Report on original and stripped atom numbers
                traj = md.load(pdb_filename)
                original_topology = traj.top
                indices = original_topology.select(topology_selection)
                print("  %s : %d atoms; selection '%s' has %d atoms" % (pdb_filename, original_topology.n_atoms, topology_selection, len(indices)))
                if len(indices)==0:
                    raise Exception("topology_selection '%s' matches zero atoms!" % topology_selection)
                del traj, original_topology, indices
    print('All specified paths and PDB files found.')
    print('')

    # Report any special processing requests
    if args.maximum_iterations:
        print('Processing for a total of %d iterations' % args.maximum_iterations)
    if args.time_limit:
        print('Will force safe advance to next phase after %s seconds' % args.time_limit)
    if args.sleep_time:
        print('Will sleep for %s seconds between iterations' % args.sleep_time)
    print('')


    # Main processing loop
    iteration = 0
    while((args.maximum_iterations == None) or (iteration < args.maximum_iterations)):
        for (project, location, pdb, topology_selection) in projects.itertuples():

            if args.verbose:
                print('----------' * 8)
                print('Processing project %s' % project)
                print("  location: '%s'" % location)
                print("  reference PDB: '%s'" % pdb)
                print("  topology selection: '%s'" % topology_selection)
                print('----------' * 8)

            # Form output paths
            allatom_output_path = os.path.join(args.output_path, "all-atoms/", "%s/" % project)
            protein_output_path = os.path.join(args.output_path, "no-solvent/", "%s/" % project)

            # Make sure output paths exist
            fahmunge.automation.make_path(allatom_output_path)
            fahmunge.automation.make_path(protein_output_path)

            # Munge data
            fahmunge.automation.merge_fah_trajectories(location, allatom_output_path, pdb, nprocesses=args.nprocesses, maxtime=args.time_limit)
            fahmunge.automation.strip_water(allatom_output_path, protein_output_path, topology_selection, nprocesses=args.nprocesses, maxtime=args.time_limit)

        # Report progress.
        print('')
        if (args.maximum_iterations == None):
            print("Finished iteration %d, sleeping for %d seconds." % (iteration, args.sleep_time))
        else:
            print("Finished iteration %d / %d, sleeping for %d seconds." % (iteration, args.maximum_iterations, args.sleep_time))
        print('')

        # Increment iteration counter
        iteration += 1

        # Exit now if specified number of iterations is reached
        if (args.maximum_iterations and (iteration >= args.maximum_iterations)):
            return

        # Sleep
        time.sleep(args.sleep_time)
