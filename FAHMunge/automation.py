import glob
import os
import mdtraj as md
import fah
import signal
import time
import sys
from multiprocessing import Pool

def set_signals():
    """
    Set signals so that multiprocessing processes are correctly killed.
    """
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def make_path(filename):
    try:
        path = os.path.split(filename)[0]
        os.makedirs(path)
    except OSError:
        pass

def get_num_runs_clones(path):
    """Get the number of runs and clones.
    
    Parameters
    ----------
    path : str
        Path to FAH data.
    
    Returns
    -------
    n_runs : int
    n_clones : int
    
    Notes
    -----
    Assumes each run has the same number of clones.
    """
    runs = glob.glob(os.path.join(path, "RUN*"))
    n_runs = len(runs)
    
    if n_runs == 0:
        n_clones = 0
    else:
        clones = glob.glob(os.path.join(path, "RUN0", "CLONE*"))
        n_clones = len(clones)
    
    return n_runs, n_clones

def strip_water_wrapper(args):
    (in_filename, protein_filename, min_num_frames, topology_selection) = args
    t=md.load(in_filename)[0]
    # add other neutralizing ions if needed
    topology = t.top.select(topology_selection)
    del t
    print("Stripping %s" % in_filename)
    fah.strip_water(in_filename, protein_filename, topology, min_num_frames=min_num_frames)
    del topology
    
def strip_water(path_to_merged_trajectories, output_path, min_num_frames=1, nprocesses=None):
    """Strip the water for a set of trajectories.
    
    Parameters
    ----------
    path_to_merged_trajectories : str
        Path to merged HDF5 FAH trajectories
    output_path : str
        Path to put stripped trajectories
    protein_atom_indices : np.ndarray, dtype='int'
        Atom indices for protein atoms (or more generally, atoms to keep).
    min_num_frames : int, optional, default=1
        Skip if below this number.
    nprocesses : int, optional, default=None
        If not None, use multiprocessing to parallelize up to the specified number of workers.

    Notes
    -----
    Assumes each run has the same number of clones.
    """
    # Build a list of work.
    work = list()
    in_filenames = glob.glob(os.path.join(path_to_merged_trajectories, "*.h5"))
    topology_selection = 'not (water or resname NA or resname CL)'
    for in_filename in in_filenames:
        protein_filename = os.path.join(output_path, os.path.basename(in_filename))
        args = (in_filename, protein_filename, min_num_frames, topology_selection)
        work.append(args)
        # create no-solvent pdbs for all RUNs. Relies on trajectories having
        # runX-cloneY.h5 filename format
        pdb_name = os.path.basename(in_filename)
        pdb_name = pdb_name[:pdb_name.index('-')] + '.pdb'
        pdb_filename = os.path.join(output_path, pdb_name)
        if not os.path.exists(pdb_filename):
            t = md.load(in_filename)[0]
            topology = t.top.select(topology_selection)
            no_solvent_t = t.atom_slice(topology)
            no_solvent_t.save(pdb_filename)
            del t, topology, no_solvent_t
    # Do the work in parallel or serial
    if nprocesses != None:
        print(nprocesses)
        
        try:
            print("Creating thread pool...")
            pool = Pool(nprocesses, set_signals)
            print("Starting asynchronous map operations...")
            job = pool.map_async(strip_water_wrapper, work)
            while(not job.ready()):
                try:
                    print "Sleeping for 10 seconds..."
                    time.sleep(10)
                except KeyboardInterrupt:
                    print "Caught KeyboardInterrupt, terminating workers"
                    pool.terminate()
                    pool.join()
                    sys.exit(1)
        finally:
            print "Finished processing work. Cleaning up..."
            pool.close()
            pool.join()

        print('All trajectories merged.')
        #output = job.get()
        #print(output)
    else:
        # Serial version.
        map(strip_water_wrapper, work)

def concatenate_core17_filenames_wrapper(args):
    fah.concatenate_core17_filenames(*args)
        
def merge_fah_trajectories(input_data_path, output_data_path, top_filename, nprocesses=None):
    """Strip the water for a set of trajectories.
    
    Parameters
    ----------
    input_data_path : str
        Path to FAH Core17/Core18 data directory.  E.g. XYZ/server2/data/SVRXYZ/PROJ10470/
    output_data_path : str
        Path to dump merged HDF5 files with concantenated trajectories.
        Metadata for which files are processed are included INSIDE the HDF5
        files.  
    top_filename : str, 
        filename of PDB containing the topology information, necessary
        for loading the XTC files.
    nprocesses : int, optional, default=None
        If not None, use multiprocessing to parallelize up to the specified number of workers.

    """
    # Build a list of work to parallelize
    n_runs, n_clones = get_num_runs_clones(input_data_path)
    work = list()
    for run in range(n_runs):
        for clone in range(n_clones):
            path = os.path.join(input_data_path, "RUN%d" % run, "CLONE%d" % clone)
            out_filename = os.path.join(output_data_path, "run%d-clone%d.h5" % (run, clone))
            args = (path, top_filename % vars(), out_filename)
            work.append(args)

    # Do the work in parallel or serial
    if nprocesses != None:
        print(nprocesses)

        try:
            print("Creating thread pool...")
            pool = Pool(nprocesses, set_signals)
            print("Starting asynchronous map operations...")
            job = pool.map_async(concatenate_core17_filenames_wrapper, work)
            while(not job.ready()):
                try:
                    print "Sleeping for 10 seconds..."
                    time.sleep(10)
                except KeyboardInterrupt:
                    print "Caught KeyboardInterrupt, terminating workers"
                    pool.terminate()
                    pool.join()
                    sys.exit(1)
        finally:
            print "Finished processing work. Cleaning up..."
            pool.close()
            pool.join()

        print('All trajectories merged.')
        #output = job.get()
        #print(output)
    else:
        # Serial version.
        map(fah.concatenate_core17_filenames, work)
