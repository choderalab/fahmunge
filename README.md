## FAHMunge

#### How to use

0.  Install FAHMunge via setup.py using anaconda (not system) python
1.  Login to work server using the usual FAH login
2.  Check if script is running (`screen -r -d`).  If True, stop here.
3.  Start a screen session
4.  `cd /data/choderalab/fah/Software/FAHMunge`
5.  `export PATH=/data/choderalab/anaconda/bin:$PATH; python scripts/munge_fah_data_parallel.py`
6.  To stop, control c when the script is in the "sleep" phase

The metadata for FAH is a CSV file located here:

/data/choderalab/fah/Software/FAHMunge/projects.csv


### Example CSV
```
project,location,pdb
"10491","/home/server.140.163.4.245/server2/data/SVR2359493877/PROJ10491/","/home/server.140.163.4.245/server2/projects/GPU/p10491/topol-renumbered-explicit.pdb"
"10492","/home/server.140.163.4.245/server2/data/SVR2359493877/PROJ10492/","/home/server.140.163.4.245/server2/projects/GPU/p10492/topol-renumbered-explicit.pdb"
"10495","/home/server.140.163.4.245/server2/data/SVR2359493877/PROJ10492/","/home/server.140.163.4.245/server2/projects/GPU/p10495/MTOR_HUMAN_D0/RUN%(run)d/system.pdb"
```
pdb points pipeline towards pdb to look at for numbering atoms in the munged data. The top two lines are eamples of using a single pdb for the munging pipeline.
The third line shows how to use a different pdb for each run. %(run)d is substituted by the run number via filename % vars() in Python, whic allows run numbers 
or other variables to be substituted. This is done on a per-run basis, not per-clone.


#### Single vs. multi process

There is also a multiprocessing version in the `scripts/` folder.  However,
the scripts generate potentially large temporary files.  The single process
version seems to put less strain on the `/tmp` filesystem, so we prefer that
right now.

#### More description

Overall Pipeline (Core17/18):

1.  Extract XTC data from bzips
2.  Append allatom coordinates and filenames to HDF5 file
3.  Extract protein coordinates and filenames into a second HDF5 file


General instructions:

1.  Run FAH servers
2.  Edit scripts/munge_fah_data.py to load your FAH data.
3.  Run scripts/munge_fah_data.py in a screen session
4.  rsync your stripped data to analysis machines periodically.  

Note: the rate limiting step appears to be bunzip.  

#### Sync to `hal.cbio.mskcc.org`

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

