import skyx, maximdl, sphere
import numpy as np
import ephem
import json
from datetime import datetime
import hashlib

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
	session_key = hashlib.md5(datetime.now().strftime("%Y-%m-%d %H:%M:%S")).hexdigest()
	scope = skyx.sky6RASCOMTele()
	scope.Connect()
	camera = maximdl.Camera()
	az,el = UniformSearchGrid(P)
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
		print "Exposing for",P['Exposure']," seconds..."
		camera.expose(P['Exposure'])

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
		camera.setFitsKey("tp_lat",P['Lat'])
		camera.setFitsKey("tp_lon",P['Lon'])
		# store sidereal time
		camera.setFitsKey("tp_LST",compute_sidereal_time(P['Lon']))

		# Save Exposure
		filename = session_key + "_" + str(count) + ".fits"
		save_dir = "C:\\Users\\Dave\\Desktop\\tpoint\\"
		save_path = save_dir+filename
		camera.saveImage(save_path)

def compute_sidereal_time(lon,lat=0,alt=0,t=datetime.utcnow()):
    '''
        Return local apparent sidereal time in decimal hours:
        
        Inputs [required]
        lon - (float) longitude in decimal degrees
        
        Inputs [optional]
        lat - (float, default=0) latitude in decimal degrees
        alt - (float, default=0) altitude in meteres
        time - (float, default=now) datetime object
        
        Output
        sidereal_time - (float) local apparent sidereal time in decimal hours
    '''
    ovr = ephem.Observer()
    ovr.lon = lon * ephem.degree
    ovr.lat = lat * ephem.degree
    ovr.elevation = alt
    ovr.date = t
    st = ovr.sidereal_time()
    st_hours = (st/ephem.degree)/15 # convert time in radians to decimal hours
    return st_hours

def RaDec2AzEl(DateTime,Ra,Dec,Lat,Lon,Alt=0,display=False):
    '''
    Given ra/dec pointing and an observation lat(deg),lon(deg),alt(m) at a UTC time
    convert to az/el angles.  All inputs and outputs in degrees.
    '''
    # We need to create a "Body" in pyephem, which represents the coordinate
    # http://stackoverflow.com/questions/11169523/how-to-compute-alt-az-for-given-galactic-coordinate-glon-glat-with-pyephem
    body = ephem.FixedBody()
    body._ra = np.radians(Ra)
    body._dec = np.radians(Dec)
    # Set observer parameters
    obs = ephem.Observer()
    obs.lon = np.radians(Lon)
    obs.lat = np.radians(Lat)
    obs.elevation = Alt
    obs.date = DateTime
    # Turn refraction off by setting pressure to zero
    obs.pressure = 0
    # Compute alt / az of the body for that observer
    body.compute(obs)
    az, alt = np.degrees([body.az, body.alt])
    return az, alt

def AzEl2RaDec(DateTime,Az,El,Lat,Lon,Alt=0,display=False):
    '''
    Given az/el pointing and an observation lat(deg),lon(deg),alt(m) at a UTC time
    convert to rad/dec angles.  All inputs and outputs in degrees.
    '''
    import numpy as np
    import ephem
    # convert to radians
    az = np.radians(Az)
    el = np.radians(El)
    lon = np.radians(Lon)
    lat = np.radians(Lat)
    alt = Alt
    # Define an observer:
    observer = ephem.Observer()
    observer.lon = lon
    observer.lat = lat
    observer.elevation = alt
    observer.date = DateTime
    # Compute ra,dec 
    ra,dec = observer.radec_of(az, el)
    if display:
        print "Time: " + datetime.strftime(DateTime,'%d-%m-%Y %H:%M:%S.%f')
        print "RA: " + str(np.degrees(ra))
        print "DEC: " + str(np.degrees(dec))
    # return output
    return np.degrees(ra),np.degrees(dec)

def ScrubGridAzEl(P,Az,El):
	'''
	This filters az/el pairs based on paramaters in the dictionary P
	'''
	Az_Scrub = []
	El_Scrub = []
	for az,el in zip(Az,El):
		# Convert to ra/dec in order to add declination offset
		ra,dec = AzEl2RaDec(datetime.now(),az,el,P['Lat'],P['Lon'])
		# 1) Distance from celestial pole
		if dec > (90-P['PoleBuffer']):
			continue
		# convert back to az/el and slew
		az2,el2 = RaDec2AzEl(datetime.now(),ra,dec,P['Lat'],P['Lon'])
		# 2) Closeness to local meridian
		if az2 < P['MeridianBuffer']:
			continue
		if abs(360-az2) < P['MeridianBuffer']:
			continue 
		if abs(180-az2) < P['MeridianBuffer']:
			continue
		# 3) minimum elevation
		if el2 < P['MinEl']:
			continue
		# else, finally it should be good pointing:
		Az_Scrub.append(az2)
		El_Scrub.append(el2)
	return Az_Scrub,El_Scrub

def RandomSearchGrid(P):
	'''
	Produce a survey grid from randomly sampled points.

	To obtain uniform sampling on a sphere...
	U and V random on (0,1)
	theta = 2*pi*U = Azimuth*pi/180
	phi = acos(2*V-1)= (90 - Elevation)*pi/180
	'''
	num_samples = P['Number_Samples']
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
	V,Phi = sphere.area_regular_points(P['Area'])
	# create az/el:
	az = Phi
	el = []
	for v in V:
		el.append(90.0-v)
	az,el = ScrubGridAzEl(P,az,el)
	return az,el

def Test():
    # Calibration Parameters:
    P = {
        'MinEl': 30,
        'MeridianBuffer': 30,
        'PoleBuffer': 20,
        'FovOverlap': 0.5,
        'Fov': 10,
        'Lat': 40,
        'Lon': -84,
        'Direction': 'EW',
        'Number_Samples': 5000,
        'Exposure': 1,
        'Step': 5,
        'Area': 5
        } 
    # Show Input:
    print json.dumps(P,indent=4)
    # Execute Survey:
    if True:
    	Survey(P)
	# Plot
    if False:
		az,el = UniformSearchGrid(P)
		Plot2D(az,el,P)
		Plot3D(az,el,P)

def Plot2D(az,el,P):
	import matplotlib
	import matplotlib.pyplot as plt
	plt.subplot(1,1,1)
	# plot meridian boundary:
	handle_meridian = plt.plot([180,180],[0,90],color='red',linestyle='-',marker='None',label='Local Meridian')
	handle_meridian_west_buffer = plt.plot([180+P['MeridianBuffer'],180+P['MeridianBuffer']],[0,90],color='red',linestyle='--',marker='None',label='Meridian Buffer ('+str(P['MeridianBuffer'])+' deg)')
	handle_meridian_east_buffer = plt.plot([180-P['MeridianBuffer'],180-P['MeridianBuffer']],[0,90],color='red',linestyle='--',marker='None')
	handle_meridian_east_buffer = plt.plot([360-P['MeridianBuffer'],360-P['MeridianBuffer']],[0,90],color='red',linestyle='--',marker='None')
	handle_meridian_east_buffer = plt.plot([P['MeridianBuffer'],P['MeridianBuffer']],[0,90],color='red',linestyle='--',marker='None')
	# plot minimum elevation:
	handle_elevation_limit = plt.plot([0,360],[P['MinEl'],P['MinEl']],color='green',linestyle='--',marker='None',label='Minimum Elevation ('+str(P['MinEl'])+' deg)')
	# plot pole boundary:
	ax = plt.gca()
	circle0 = matplotlib.patches.Circle((0,P['Lat']), P['PoleBuffer'], ec="b",fill=None,label='Pole Buffer ('+str(P['PoleBuffer'])+' deg)')
	circle360 = matplotlib.patches.Circle((360,P['Lat']), P['PoleBuffer'], ec="b",fill=None)
	ax.add_patch(circle0)
	ax.add_patch(circle360)
	# plot the survey points:
	plt.plot(az,el,linestyle='None',marker='+')
	# Make it nice
	plt.axis('scaled')
	if P['Lat'] >= 0:
		plt.axis([0,360,0,90])
	else:
		plt.axis([0,360,0,90])
	plt.ylabel('Elevation (deg)')
	plt.xlabel('Azimuth (deg)')
	plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,ncol=2, mode="expand", borderaxespad=0.)

def Plot3D(az,el,P):
	import matplotlib
	import matplotlib.pyplot as plt
	from mpl_toolkits.mplot3d import Axes3D
	fig = plt.figure()
	ax = fig.add_subplot(111, projection='3d')
	x = np.cos(np.deg2rad(el))*np.cos(np.deg2rad(az))
	y = np.cos(np.deg2rad(el))*np.sin(np.deg2rad(az))
	z = np.sin(np.deg2rad(el))
	ax.scatter(x, y, z)
	ax.axis('equal')
	ax.set_xlim(-1,1)
	ax.set_ylim(-1,1)
	ax.set_zlim(0,1)
	ax.set_xlabel('X')
	ax.set_ylabel('Y')
	ax.set_zlabel('Z')
	plt.show()

if __name__ == "__main__":
	print '--------------------------------------------'
	print '    Demo of scripted T-Point Calibration'
	print '--------------------------------------------'
	Test()