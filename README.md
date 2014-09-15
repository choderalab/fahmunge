## FAHMunge

Overall Pipeline (Core17/18):

1.  Extract XTC data from bzips
2.  Append allatom coordinates and filenames to HDF5 file
3.  Extract protein coordinates and filenames into a second HDF5 file


General instructions:

1.  Run FAH servers
2.  Edit scripts/munge_fah_data.py to load your FAH data.
3.  Run scripts/munge_fah_data.py in a screen session
4.  rsync your stripped data to analysis machines periodically.  

Note: the rate limiting step appears to be bunzip.  This suggests that we might
be able to run several instances of the script in parallel.  For example, one for each project.  
That should lead to improved performance.  

ToDo
Some of the same code should be re-usable for OCore based projects.  
