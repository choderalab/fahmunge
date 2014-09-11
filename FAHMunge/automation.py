import glob
import os
import mdtraj as md
import fah

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


def strip_water(path_to_merged_trajectories, output_path, protein_atom_indices, min_num_frames=1):
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

    Notes
    -----
    Assumes each run has the same number of clones.
    """
    in_filenames = glob.glob(os.path.join(path_to_merged_trajectories, "*.h5"))
    for in_filename in in_filenames:
        print("Stripping %s" % in_filename)
        protein_filename = os.path.join(output_path, os.path.basename(in_filename))
        fah.strip_water(in_filename, protein_filename, protein_atom_indices, min_num_frames=min_num_frames)
        

def merge_fah_trajectories(input_data_path, output_data_path, top_filename):
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

    """
    top = md.load(top_filename)
    n_runs, n_clones = get_num_runs_clones(input_data_path)
    for run in range(n_runs):
        for clone in range(n_clones):
            print(run, clone)
            path = os.path.join(input_data_path, "RUN%d" % run, "CLONE%d" % clone)
            out_filename = os.path.join(output_data_path, "run%d-clone%d.h5" % (run, clone))
            print(path)
            print(out_filename)
            fah.concatenate_core17(path, top, out_filename)
