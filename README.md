## FAHMunge

A tool to automate processing of Folding@home data to produce [mdtraj](http://mdtraj.org/)-compatible trajectory sets.

#### Authors
* Kyle A. Beauchamp
* John D. Chodera
* Steven Albanese
* Rafal Wiewiora

#### Installation

The easiest way to install `fahmunge` and its dependencies is via `conda` (preferably [`miniconda`](http://conda.pydata.org/miniconda.html)):
```bash
conda install --yes -c omnia fahmunge
```

#### Usage

##### Basic Usage

Basic usage simply specifies a project CSV file and an output path for the munged data:
```bash
munge-fah-data --projects projects.csv --outpath /data/choderalab/fah/munged-data
```
The metadata for FAH is a CSV file located here on `choderalab` FAH servers:
```
/data/choderalab/fah/Software/FAHMunge/projects.csv
```
This file specifies the project number, the location of the FAH data, a reference PDB file (or files) to be used for munging, and the MDTraj DSL topology selection to be used for extracting solute coordinates of interest.

For example:
```
project,location,pdb,topology_selection
"10491","/home/server.140.163.4.245/server2/data/SVR2359493877/PROJ10491/","/home/server.140.163.4.245/server2/projects/GPU/p10491/topol-renumbered-explicit.pdb","not water"
"10492","/home/server.140.163.4.245/server2/data/SVR2359493877/PROJ10492/","/home/server.140.163.4.245/server2/projects/GPU/p10492/topol-renumbered-explicit.pdb","not (water or resname NA or resname CL)"
"10495","/home/server.140.163.4.245/server2/data/SVR2359493877/PROJ10492/","/home/server.140.163.4.245/server2/projects/GPU/p10495/MTOR_HUMAN_D0/RUN%(run)d/system.pdb","not (water or resname NA or resname CL)"
```
`pdb` points the pipeline toward a PDB file to look at for numbering atoms in the munged data.
The top two lines are examples of using a single PDB for all RUNs in the project.
The third line shows how to use a different PDB for each RUN.
`%(run)d` is substituted by the run number via `filename % vars()` in Python, which allows run numbers or other local Python variables to be substituted.
This is done on a per-run basis, not per-clone.

##### Advanced Usage

More advanced usage allows additional arguments to be specified:
* `--nprocesses <NPROCESSES>` will parallelize munging by RUN using `multiprocessing` if `NPROCESSES > 1` is specified. (**NOTE: Parallel processing is still experimental and tends to occasionally corrupt munged trajectories---we are working on fixing this.**) By default, a serial code path is used with `NPROCESSES = 1`.
* `--time <TIME_LIMIT>` specifies that munging should move on to another phase or project after the given time limit (in seconds) is reached, once it is safe to move on.  This is useful for ensuring that some munging occurs on all projects of interest every day.
* `--verbose` will produce verbose output
* `--maxits <MAXITS>` will cause the munging pipeline to run for the specified number of iterations and then exit. This can be useful for debugging. Without specifying this option, munging will run indefinitely.
* `--sleeptime <SLEEPTIME>` will cause munging to sleep for the specified number of seconds if no work was done in this iteration (default:3600).

#### Usage on `choderalab` Folding@home servers

1.  Login to work server using the usual FAH login
2.  Check if script is running (`screen -r -d`).  If True, stop here.
3.  Start a screen session
4.  Run with: `munge-fah-data --projects /data/choderalab/fah/projects.csv --outpath /data/choderalab/fah/munged-data --time 3600 --nprocesses 16`
5.  To stop, control c when the script is in the "sleep" phase

#### Single vs. multi process

**This section needs to be updated**

There is also a multiprocessing version in the `scripts/` folder.  
However, the scripts generate potentially large temporary files.  
The single process version seems to put less strain on the `/tmp` filesystem, so we prefer that right now.

#### How it works

Overall Pipeline (Core17/18):

1.  Extract XTC data from `bzip`s
2.  Append all-atom coordinates and filenames to HDF5 file
3.  Extract protein coordinates and filenames from the all-atom HDF5 file into a second HDF5 file

General instructions:

1.  Run FAH servers
2.  Edit `scripts/munge_fah_data.py` to load your FAH data.
3.  Run `scripts/munge_fah_data.py` in a screen session
4.  rsync your stripped data to analysis machines periodically.  

#### Efficiency considerations

The rate limiting step appears to be `bunzip`.  
If we can avoid having the trajectories be double-`bzip`ped by the client, this will speed up things immensely.

#### Nightly syncing to `hal.cbio.mskcc.org`

Munged `no-solvent` data is `rsync`ed nightly from `plfah1` and `plfah2` to `hal.cbio.mskcc.org` via the `choderalab` robot user account to:
```
/cbio/jclab/projects/fah/fah-data/munged
```
This is done via a `crontab`:
```
04 01 * * * rsync -av --chmod=g-w,g+r,o-w,o+r server@plfah1.mskcc.org:/data/choderalab/fah/munged/no-solvent /cbio/jclab/projects/fah/fah-data/munged >> $HOME/plfah1-rsync-no-solvent.log 2>&1
39 01 * * * rsync -av --chmod=g-w,g+r,o-w,o+r server@plfah2.mskcc.org:/data/choderalab/fah/munged/no-solvent /cbio/jclab/projects/fah/fah-data/munged >> $HOME/plfah2-rsync-no-solvent.log 2>&1
34 03 * * * rsync -av --chmod=g-w,g+r,o-w,o+r server@plfah1.mskcc.org:/data/choderalab/fah/munged/all-atoms /cbio/jclab/projects/fah/fah-data/munged >> $HOME/plfah1-rsync-all-atoms.log 2>&1
50 03 * * * rsync -av --chmod=g-w,g+r,o-w,o+r server@plfah2.mskcc.org:/data/choderalab/fah/munged/all-atoms /cbio/jclab/projects/fah/fah-data/munged >> $HOME/plfah2-rsync-all-atoms.log 2>&1
```
To install this `crontab` as the `choderalab` user:
```bash
crontab ~/crontab
```
To list the active `crontab`:
```bash
crontab -l
```
Transfers are logged in the `choderalab` account:
```
plfah1-rsync-all-atoms.log
plfah1-rsync-no-solvent.log
plfah2-rsync-all-atoms.log
plfah2-rsync-no-solvent.log
```
