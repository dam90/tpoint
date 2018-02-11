#! /bin/python
from datetime import datetime
import ephem
import numpy as np
import math

def vrotate(vector,axis,theta_rad):
    '''
    rotate vector (list) about axis (list) by theta (radians)
    '''
    # make arrays:
    vector = np.asarray(vector)
    axis = np.asarray(axis)
    # rotation matrix
    axis = axis/math.sqrt(np.dot(axis, axis))
    a = math.cos(theta_rad/2.0)
    b, c, d = -axis*math.sin(theta_rad/2.0)
    aa, bb, cc, dd = a*a, b*b, c*c, d*d
    bc, ad, ac, ab, bd, cd = b*c, a*d, a*c, a*b, b*d, c*d
    M = np.array([[aa+bb-cc-dd, 2*(bc+ad), 2*(bd-ac)],
                     [2*(bc-ad), aa+cc-bb-dd, 2*(cd+ab)],
                     [2*(bd+ac), 2*(cd-ab), aa+dd-bb-cc]])
    # rotate the vector
    rotated = np.dot(M,vector)
    return rotated

def azel2xyz(az,el):
    x = np.cos(np.deg2rad(el))*np.cos(np.deg2rad(az))
    y = np.cos(np.deg2rad(el))*np.sin(np.deg2rad(az))
    z = np.sin(np.deg2rad(el))
    return x,y,z

def xyz2azel(v):
    # normallize
    v  = np.asarray(v)
    v = v / np.linalg.norm(v)
    az = np.rad2deg(np.arctan2(v[1],v[0]))
    el = 90 - np.rad2deg(np.arccos(v[2]))
    return az,el

def meridian_rotate(az,el,theta_deg):
    '''
    rotate point perpendicular to its meridian, returns az/el
    '''
    v = list(azel2xyz(az,el))
    axis = list(azel2xyz(az,el+90))
    rotated = vrotate(v,axis,np.deg2rad(theta_deg))
    az,el = xyz2azel(rotated)
    return az,el

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

def GreatCircleDelta(az1,el1,az2,el2):
	'''
	Return sthe central angle between two az/el coordinates (great circle distance)
	Input/Output in degrees
	'''
	lam1 = np.deg2rad(az1)
	phi1 = np.deg2rad(el1)
	lam2 = np.deg2rad(az2)
	phi2 = np.deg2rad(el2)
	dlam = lam2-lam1
	if abs(dlam) < 0.00001:
		delta = 0
	else:
		sigma = np.arccos( (np.sin(phi1)*np.sin(phi2)) + (np.cos(phi1)*np.cos(phi2)*np.cos(dlam)) )
		delta = abs(np.rad2deg(sigma))
	return delta