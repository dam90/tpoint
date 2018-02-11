# import API libraries:
try:
	from api import skyx, maximdl
except:
	print "Could not import API libraries"
# import utilities:
from utility import sphere, dispatch, plot, geometry
from utility.tsp import tsp
# other dependencies:
import numpy as np
import ephem
# python defaults:
import os,json,hashlib
from datetime import datetime

def Survey(P):
	'''
	Perform automatic survey of the night sky by automating TheSkyX and MaximDL.

	- This will produce a set of FITS files with relevant time and pointing parameters 
	  stored in the headers.
	- This routine does not plate-solve.  That process should be de-coupled, so as not
	  to interupt the survey.
	- The fits headers will include a session key.  The key indicates that the files
	  were produced during the same run.
  	- The plate solver does not have to be run in real-time.  FITS header data should allow you
  	  to know not only rough pointing (speeds up plate solve), but also lat/lon and timestamp
  	  for producing a tpoint file
	'''
	# check if output directory exists:
	print "-------------------------------------"
	print " Verifying output directory...."
	if os.path.isdir(P['Save_Directory']):
		print "Storing FITS files in:",P['files']['fit_directory']
	else:
		print "Directory does not exist:",P['files']['fit_directory']
		print "Attempting to create directory..."
		os.makedirs(P['Save_Directory'])
		if os.path.isdir(P['Save_Directory']):
			print "Done."
		else:
			print "Could not create directory.  Exiting."
			return
	# read input
	session_key = hashlib.md5(datetime.now().strftime("%Y-%m-%d %H:%M:%S")).hexdigest()
	print "-------------------------------------"
	print " Current configuration:"
	print json.dumps(P,indent=4)
	# Connect
	print "-------------------------------------"
	print " Generating survey grid...."
	az,el = UniformSearchGrid(P)
	az,el = ShortestPath(az,el)
	print "-------------------------------------"
	print " Connecting to TheSkyX..."
	scope = skyx.sky6RASCOMTele()
	scope.Connect()
	print "-------------------------------------"
	print " Connecting to MaximDL..."
	camera = maximdl.Camera()
	print "-------------------------------------"
	print " Initiating Survey..."
	count = 0
	total = len(az)
	for az1,el1 in zip(az,el):
		count += 1
		print "-------------------------------------"
		print "Sample",count,"of",total
		print "Time:",datetime.now()
		print "Session Key:", session_key
		print "Slewing... Az:",az1,"El:",el1
		# Slew
		scope.SlewToAzAlt([az1,el1])
		# Expose
		print "Exposing for",P['camera']['exposure']," seconds..."
		camera.expose(P['camera']['exposure'])
		# -------------------------------------------
		#      Store Data in the FITS Header.
		# -------------------------------------------
		# store session key
		camera.setFitsKey("tp_key",session_key)
		ra,dec = scope.GetRaDec()
		# store ra/dec
		camera.setFitsKey("tp_ra",ra)
		camera.setFitsKey("tp_dec",dec)
		# store time_stamp
		time_stamp = datetime.strftime(datetime.utcnow(),"%Y-%m-%dT%H:%M:%S.%f")
		camera.setFitsKey("tp_utc",time_stamp)
		# store lat/lon
		camera.setFitsKey("tp_lat",P['location']['lat'])
		camera.setFitsKey("tp_lon",P['location']['lon'])
		# store sidereal time
		camera.setFitsKey("tp_LST",compute_sidereal_time(P['location']['lon']))
		# Save Exposure
		filename = session_key + "_" + str(count) + ".fits"
		# save_dir = "C:\\Users\\Dave\\Desktop\\tpoint"
		save_dir = P['files']['fit_directory']

		# need to change this to be platform independent:

		save_path = save_dir+"\\"+filename
		camera.saveImage(save_path)
	print "-------------------------------------"
	print " Survey Complete!"

def Solve(P):
	'''
	Watch directory of FITs files, solve them.
	'''
	w = dispatch.Watcher(P)
	w.run()

def ShortestPath(az,el):
	'''
	Given az/el pairs (deg), determine the shortest path through the grid.
	- Try to avoid meridian  flip
	'''
	# Split indeces into east/west data
	east = []
	west = []
	for idx,v in enumerate(az):
		if v <= 180:
			east.append(idx)
		else:
			west.append(idx)
	a=[]
	e=[]
	for points in [east,west]:
		# create list of tuples
		s = []
		# add tuples to the list from one side of meridian
		for i in points:
			s.append((az[i],el[i]))
		# find the index order for the shortest path
		tour_id = tsp(s)
		# add points to output
		for i in tour_id:
			a.append(s[i][0])
			e.append(s[i][1])

	return a,e

def ScrubGridAzEl(P,Az,El):
	'''
	This filters az/el pairs based on paramaters in the dictionary P
	'''
	Az_Scrub = []
	El_Scrub = []
	for az,el in zip(Az,El):
		# Convert to ra/dec in order to add declination offset
		ra,dec = geometry.AzEl2RaDec(datetime.now(),az,el,P['location']['lat'],P['location']['lon'])
		# 1) Distance from celestial pole
		if dec > (90-P['survey']['buffers']['pole']):
			continue
		# 2) Closeness to local meridian
		if az <= 90 or az >= 270:
			if geometry.GreatCircleDelta(az,el,0,el) < P['survey']['buffers']['meridian']:
				continue
		else:
			if geometry.GreatCircleDelta(az,el,180,el) < P['survey']['buffers']['meridian']:
				continue
		# 3) minimum elevation
		if el < P['survey']['masks']['include']['elevation'][0]:
			continue
		# else, finally it should be good pointing:
		Az_Scrub.append(az)
		El_Scrub.append(el)
	return Az_Scrub,El_Scrub

def RandomSearchGrid(P):
	'''
	Produce a survey grid from randomly sampled points.

	To obtain uniform sampling on a sphere...
	U and V random on (0,1)
	theta = 2*pi*U = Azimuth*pi/180
	phi = acos(2*V-1)= (90 - Elevation)*pi/180
	'''
	num_samples = 41253/P['survey']['area']
	U = np.random.rand(num_samples/4)
	V = np.random.rand(num_samples)
	theta = 2*np.pi*U
	phi = np.arccos(2*V-1)
	az = theta*180/np.pi
	el = 90 - phi*(180/np.pi)
	az,el = ScrubGridAzEl(P,az,el)
	return az,el

def UniformSearchGrid(P):
	'''
	Produce a search grid with specified area per grid point.
	This results in a regular distribution.
	'''
	# points:
	V,Phi = sphere.area_regular_points(P['survey']['area'])
	# create az/el:
	az = Phi
	el = []
	for v in V:
		el.append(90.0-v)
	az,el = ScrubGridAzEl(P,az,el)
	return az,el

def Test(P):
	print '--------------------------------------------'
	print '    Demo of scripted T-Point Calibration'
	print '--------------------------------------------'
    # Show Input:
	print json.dumps(P,indent=4)
	az,el = UniformSearchGrid(P)
	# az,el = ShortestPath(az,el)
	plot.Plot2D(az,el,P)
	plot.Plot3D(az,el,P)
	Plot2D(az,el,P,'-')
	Plot3D(az,el,P,'-')

if __name__ == "__main__":
	# load survey config fromt he default file:
	P = json.load(open('test_input.json'))
	Test(P)
	# Survey(P)
	# Solve(P)