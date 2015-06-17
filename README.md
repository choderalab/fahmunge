## FAHMunge

#### How to use

0.  Install FAHMunge via setup.py using anaconda (not system) python
1.  Login to work server using the usual FAH login
2.  Check if script is running (`screen -r -d`).  If True, stop here.
3.  Start a screen session
4.  `cd /data/choderalab/fah/Software/FAHMunge`
5.  `/data/choderalab/anaconda/bin/python scripts/munge_fah_data.py`
6.  To stop, control c when the script is in the "sleep" phase

The metadata for FAH is a CSV file located here:

/data/choderalab/fah/Software/FAHMunge/projects.csv

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
