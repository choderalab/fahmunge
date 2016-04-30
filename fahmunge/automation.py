import glob
import os
import mdtraj as md
from fahmunge import fah
import signal
import time
import sys
import collections
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

def concatenate_core17_wrapper(kwargs):
    """
    Wrapper for using fah.concatenate_core17 in map.
    """
    fah.concatenate_core17(**kwargs)

def strip_water_wrapper(args):
    """
    Wrapper for using fah.strip_water in map.
    """
    (in_filename, protein_filename, min_num_frames, topology_selection) = args
    t=md.load(in_filename)[0]
    topology = t.top.select(topology_selection)
    del t
    print("Stripping %s" % in_filename)
    fah.strip_water(in_filename, protein_filename, topology, min_num_frames=min_num_frames)
    del topology

def create_nosolvent_pdb(in_filename, pdb_filename, topology_selection):
    """Create a PDB file stripped of solvent coordinates.

    Parameters
    ----------
    in_filename : str
       HDF5 FAH trajectory (e.g. runX-cloneY.h5)
    pdb_filenmae : str
       PDB filename to write
    topology_selection : str
       MDTraj DSL topology selection syntax
       e.g. 'not (water or resname NA or resname CL)'

    TODO
    ----
    * If HDF5 file is corrupted, emit a warning and delete the HDF5 file so it can be regenerated.

    """
    try:
        traj = md.load(in_filename)
    except Exception as e:
        msg = "There was a problem reading the HDF5 file '%s'.\n" % in_filename
        msg += str(e)
        raise Exception(msg)
    t = traj[0]
    topology = t.top.select(topology_selection)
    no_solvent_t = t.atom_slice(topology)
    no_solvent_t.save(pdb_filename)
    del t, topology, no_solvent_t

def merge_fah_trajectories(input_data_path, output_data_path, top_filename, nprocesses=None, maxtime=None):
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
    MAXPACKETS = 1 # maximum number of packets to process per iteration

    # Build a list of work to parallelize
    n_runs, n_clones = get_num_runs_clones(input_data_path)
    work = collections.deque()
    for run in range(n_runs):
        for clone in range(n_clones):
            path = os.path.join(input_data_path, "RUN%d" % run, "CLONE%d" % clone)
            out_filename = os.path.join(output_data_path, "run%d-clone%d.h5" % (run, clone))
            kwargs = {'path' : path, 'top_filename' : top_filename % vars(), 'output_filename' : out_filename}
            # Set maxpackets and maxtime
            kwargs['maxpackets'] = MAXPACKETS
            if maxtime:
                kwargs['maxtime'] = maxtime
            # Append work
            work.append(kwargs)
    print('merging %s : work has %d RUN/CLONE pairs to process' % (input_data_path, len(work)))

    print('Using %d threads' % nprocesses)
    batchsize = 2*nprocesses
    maxtasksperchild = 10*nprocesses

    if maxtime:
        print('Starting timer. Will gracefully terminate phase after %d seconds.' % maxtime)
    initial_time = time.time()
    timeout = False
    try:
        print("Creating thread pool...")
        pool = Pool(nprocesses, set_signals, maxtasksperchild=maxtasksperchild)
        print("Starting asynchronous map operations...")
        while (len(work) > 0) and (not timeout):
            # Queue up some work
            work_batch = [ work.popleft() for index in range(batchsize) if (len(work) > 0) ]
            job = pool.map_async(concatenate_core17_wrapper, work_batch)
            while(not job.ready()):
                time.sleep(1)
            if maxtime:
                elapsed_time = time.time() - initial_time
                if elapsed_time > maxtime:
                    timeout = True
                    print('Elapsed time (%.1f s) exceeds timeout (%.1f s) so moving on to next project/phase.' % (elapsed_time, maxtime))
    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt, safely terminating workers. This may take several minutes. Please be patient to avoid data corruption.")
        pool.close()
        pool.join()
        sys.exit(1)
    except Exception as e:
        raise e
    finally:
        print("Finished processing work. Cleaning up...")
        pool.close()
        pool.join()

def strip_water(path_to_merged_trajectories, output_path, topology_selection, min_num_frames=1, nprocesses=None, maxtime=None):
    """Strip the water for a set of trajectories.

    Parameters
    ----------
    path_to_merged_trajectories : str
        Path to merged HDF5 FAH trajectories
    output_path : str
        Path to put stripped trajectories
    topology_selection : str
        MDTraj DSL topology selection string: e.g. 'not (water or resname NA or resname CL)'
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
    work = collections.deque()
    in_filenames = glob.glob(os.path.join(path_to_merged_trajectories, "*.h5"))
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
            print("Stripping solvent from '%s' to create '%s'" % (in_filename, pdb_filename))
            create_nosolvent_pdb(in_filename, pdb_filename, topology_selection)

    print('%s : %d trajectories to process' % (output_path, len(work)))

    print('Using %d threads' % nprocesses)
    batchsize = 2*nprocesses
    maxtasksperchild = 10*nprocesses

    if maxtime:
        print('Starting timer. Will gracefully terminate phase after %d seconds.' % maxtime)
    initial_time = time.time()
    timeout = False
    try:
        print("Creating thread pool...")
        pool = Pool(nprocesses, set_signals, maxtasksperchild=maxtasksperchild)
        print("Starting asynchronous map operations...")
        while (len(work) > 0) and (not timeout):
            # Queue up some work
            work_batch = [ work.popleft() for index in range(batchsize) if (len(work) > 0) ]
            job = pool.map_async(strip_water_wrapper, work_batch)
            while(not job.ready()):
                time.sleep(1)
            if maxtime:
                elapsed_time = time.time() - initial_time
                if elapsed_time > maxtime:
                    timeout = True
                    print('Elapsed time (%.1f s) exceeds timeout (%.1f s) so moving on to next project/phase.' % (elapsed_time, maxtime))
    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt, safely terminating workers. This may take several minutes. Please be patient to avoid data corruption.")
        pool.close()
        pool.join()
        sys.exit(1)
    except Exception as e:
        raise e
    finally:
        print("Finished processing work. Cleaning up...")
        pool.close()
        pool.join()
