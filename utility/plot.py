#! /bin/python
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
from .geometry import *

def PolePolygon(P):
	'''
	Generate two polygon patches dpicting a ring around the celestial pole
	in az/el space.  Produce two, one at zero, one at 360 azimuth
	'''
	# Get values from config:
	pole_buffer = P['survey']['buffers']['pole']
	lat = P['location']['lat']
	lon = P['location']['lon']
	dt = datetime.now()
	low_pole_points = []
	high_pole_points = []
	for ra in range(0,360):
		paz,pel = RaDec2AzEl(dt,ra,90-pole_buffer,lat,lon)
		if paz <= 180:
			low_pole_points.append(paz)
			high_pole_points.append(paz+360)
		if paz > 180:
			low_pole_points.append(paz-360)
			high_pole_points.append(paz)
		low_pole_points.append(pel)
		high_pole_points.append(pel)
	low_pole_points = np.reshape(low_pole_points,(len(low_pole_points)/2,2))
	high_pole_points = np.reshape(high_pole_points,(len(high_pole_points)/2,2))
	low_pole_patch = matplotlib.patches.Polygon(low_pole_points,ec="b",fill=None,label='Pole Buffer ('+str(pole_buffer)+' deg)')
	high_pole_patch = matplotlib.patches.Polygon(high_pole_points,ec="b",fill=None)
	return low_pole_patch, high_pole_patch

def Plot2D(az,el,P,my_line_style='None'):
	'''
	Plot survey data in 2D
	'''
	# Get values from config:
	meridian_buffer = P['survey']['buffers']['meridian']
	pole_buffer = P['survey']['buffers']['pole']
	min_el = P['survey']['masks']['include']['elevation'][0]
	lat = P['location']['lat']
	lon = P['location']['lon']

	plt.subplot(1,1,1)
	# plot meridian boundary:
	handle_meridian = plt.plot([180,180],[0,90],color='red',linestyle='-',marker='None',label='Local Meridian')
	handle_meridian_west_buffer = plt.plot([180+meridian_buffer,180+meridian_buffer],[0,90],color='red',linestyle='--',marker='None',label='Meridian Buffer ('+str(meridian_buffer)+' deg)')
	handle_meridian_east_buffer = plt.plot([180-meridian_buffer,180-meridian_buffer],[0,90],color='red',linestyle='--',marker='None')
	handle_meridian_east_buffer = plt.plot([360-meridian_buffer,360-meridian_buffer],[0,90],color='red',linestyle='--',marker='None')
	handle_meridian_east_buffer = plt.plot([meridian_buffer,meridian_buffer],[0,90],color='red',linestyle='--',marker='None')
	# plot minimum elevation:
	handle_elevation_limit = plt.plot([0,360],[min_el,min_el],color='green',linestyle='--',marker='None',label='Minimum Elevation ('+str(min_el)+' deg)')
	# plot pole boundary:
	ax = plt.gca()
	lowpatch,hipatch = PolePolygon(P)
	ax.add_patch(lowpatch)
	ax.add_patch(hipatch)
	# plot the survey points:
	plt.plot(az,el,linestyle=my_line_style,marker='+')
	# Make it nice
	plt.axis('scaled')
	if lat >= 0:
		plt.axis([0,360,0,90])
	else:
		plt.axis([0,360,0,90])
	plt.ylabel('Elevation (deg)')
	plt.xlabel('Azimuth (deg)')
	plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,ncol=2, mode="expand", borderaxespad=0.)

def Plot3D(az,el,P,my_line_style='None'):
	'''
	plot sruvey data in 3D
	'''
	from mpl_toolkits.mplot3d import Axes3D
	fig = plt.figure()
	ax = fig.add_subplot(111, projection='3d')
	x = np.cos(np.deg2rad(el))*np.cos(np.deg2rad(az))
	y = np.cos(np.deg2rad(el))*np.sin(np.deg2rad(az))
	z = np.sin(np.deg2rad(el))
	ax.plot(x, y, z,linestyle=my_line_style,marker='+')
	ax.axis('equal')
	ax.set_xlim(-1,1)
	ax.set_ylim(-1,1)
	ax.set_zlim(0,1)
	ax.set_xlabel('X')
	ax.set_ylabel('Y')
	ax.set_zlabel('Z')
	plt.show()
