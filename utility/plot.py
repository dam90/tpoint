#! /bin/python
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
#from .geometry import *
import geometry

def azel2xyz(az,el):
	x = np.cos(np.deg2rad(el))*np.cos(np.deg2rad(az))
	y = np.cos(np.deg2rad(el))*np.sin(np.deg2rad(az))
	z = np.sin(np.deg2rad(el))
	return x,y,z

def PolePolygon(P,output='2d'):
	'''
	Generate two polygon patches dpicting a ring around the celestial pole
	in az/el space.  Produce two, one at zero, one at 360 azimuth
	'''
	# Get values from config:
	pole_buffer = P['survey']['buffers']['pole']
	lat = P['location']['lat']
	lon = P['location']['lon']
	dt = datetime.now()
	if output == '2d':
		low_pole_points = []
		high_pole_points = []
		for ra in range(0,360):
			paz,pel = geometry.RaDec2AzEl(dt,ra,90-pole_buffer,lat,lon)
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
	elif output == '3d':
		az = []
		el = []
		for ra in range(0,360):
			paz,pel = geometry.RaDec2AzEl(dt,ra,90-pole_buffer,lat,lon)
			az.append(paz)
			el.append(pel)
		return az,el

def ElevationLimit(P,output='2d'):
	min_el = P['survey']['masks']['include']['elevation'][0]
	if output == '2d':
		az = [0,360]
		el = [min_el,min_el]
		return az, el
	if output == '3d':
		el_list = []
		az_list = []
		for az in range(0,360):
			el_list.append(min_el)
			az_list.append(az)
		return az_list,el_list

def LocalHorrizon(P,output='2d'):
	if output == '2d':
		az = [0,360]
		el = [0,0]
		return az, el
	if output == '3d':
		el_list = []
		az_list = []
		for az in range(0,360):
			el_list.append(0)
			az_list.append(az)
		return az_list,el_list

def MeridianLine(P,output='2d'):
	
	if output =='2d':
		az = [180,180]
		el = [0,90]
		return az, el
	if output == '3d':
		el_list = []
		az_list = []
		for el in range(0,90):
			el_list.append(el)
			az_list.append(0)
		for el in range(90,0,-1):
			el_list.append(el)
			az_list.append(180)
		return az_list,el_list

def MeridianBuffer(P,output='2d'):
	meridian_buffer = P['survey']['buffers']['meridian']
	if output == '3d':
		az = [[],[]]
		el = [[],[]]
		for e in range(0,180):
			# one way..
			raz,rel = geometry.meridian_rotate(0,e,meridian_buffer)
			el[0].append(rel)
			az[0].append(raz)
			# then the other
			raz,rel = geometry.meridian_rotate(0,e,-meridian_buffer)
			el[1].append(rel)
			az[1].append(raz)
		return az, el

	if output == '2d':
		az = [[],[],[],[]]
		el = [[],[],[],[]]
		start_az = [180,180,0,360]
		theta_list = [meridian_buffer,-meridian_buffer,meridian_buffer,-meridian_buffer]
		for i,a in enumerate(start_az):
			for e in range(0,91):
				raz,rel = geometry.meridian_rotate(a,e,theta_list[i])
				if raz < 0:
					raz = raz + 360
				el[i].append(rel)
				az[i].append(raz)
		return az,el

def Plot2D(az,el,P,my_line_style='None',save_path=None):
	'''
	Plot survey data in 2D
	'''
	# Get values from config:
	meridian_buffer = P['survey']['buffers']['meridian']
	pole_buffer = P['survey']['buffers']['pole']
	min_el = P['survey']['masks']['include']['elevation'][0]
	lat = P['location']['lat']
	lon = P['location']['lon']

	# specify figure size:
	fig = plt.figure(figsize=(16,6.5))
	ax = fig.add_subplot(111)
	plt.tight_layout()

	# plot meridian :
	x,y =MeridianLine(P)
	handle_meridian = plt.plot(x,y,color='red',linestyle='-',marker='None',label='Local Meridian')

	# plot meridian boundary:	
	x,y = MeridianBuffer(P)
	plt.plot(x[0],y[0],color='red',linestyle='--',marker='None',label='Meridian Buffer ('+str(meridian_buffer)+' deg)')
	plt.plot(x[1],y[1],color='red',linestyle='--',marker='None')
	plt.plot(x[2],y[2],color='red',linestyle='--',marker='None')
	plt.plot(x[3],y[3],color='red',linestyle='--',marker='None')

	# plot minimum elevation:
	x,y = ElevationLimit(P) 
	handle_elevation_limit = plt.plot(x,y,color='green',linestyle='--',marker='None',label='Minimum Elevation ('+str(min_el)+' deg)')
	
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
	if save_path:
		plt.savefig(save_path,bbox_inches='tight',dpi=400)
	else:
		plt.show()

def Plot3D(az,el,P,my_line_style='None',save_path=None):
	'''
	plot sruvey data in 3D
	'''
	from mpl_toolkits.mplot3d import Axes3D

	meridian_buffer = P['survey']['buffers']['meridian']
	pole_buffer = P['survey']['buffers']['pole']
	min_el = P['survey']['masks']['include']['elevation'][0]
	lat = P['location']['lat']
	lon = P['location']['lon']

	fig = plt.figure(figsize=(16,16))
	ax = fig.add_subplot(111, projection='3d')
	plt.tight_layout()

	# plot the survey points
	x,y,z = geometry.azel2xyz(az,el)
	ax.plot(x, y, z,linestyle=my_line_style,marker='+')

	# plot pole buffer
	az,el = PolePolygon(P,'3d')
	x,y,z = geometry.azel2xyz(az,el)
	ax.plot(x, y, z,color='blue',linestyle='-',marker='None',label='Pole Buffer ('+str(pole_buffer)+' deg)')

	# plot elevation limit
	az,el = ElevationLimit(P,'3d')
	x,y,z = geometry.azel2xyz(az,el)
	ax.plot(x, y, z,color='green',linestyle='--',marker='None',label='Minimum Elevation ('+str(min_el)+' deg)')

	# plot local horrizon
	az,el = LocalHorrizon(P,'3d')
	x,y,z = geometry.azel2xyz(az,el)
	ax.plot(x, y, z,color='black',linestyle='-',marker='None')

	# plot meridian
	az,el = MeridianLine(P,'3d')
	x,y,z = geometry.azel2xyz(az,el)
	ax.plot(x, y, z,color='red',linestyle='-',marker='None',label='Local Meridian')

	# plot meridian buffer
	az,el = MeridianBuffer(P,'3d')
	x,y,z = geometry.azel2xyz(az[0],el[0])
	ax.plot(x, y, z,color='red',linestyle='--',marker='None',label='Meridian Buffer ('+str(meridian_buffer)+' deg)')
	x,y,z = geometry.azel2xyz(az[1],el[1])
	ax.plot(x, y, z,color='red',linestyle='--',marker='None')

	# formatting:
	ax.axis('equal')
	ax.set_xlim(-1,1)
	ax.set_ylim(-1,1)
	ax.set_zlim(0,1)
	ax.set_xticklabels([])
	ax.set_yticklabels([])
	ax.view_init(elev=20, azim=-40)
	plt.axis('off')
	plt.legend(mode="expand", borderaxespad=0.)

	# output
	if save_path:
		plt.savefig(save_path,bbox_inches='tight',dpi=400)
	else:
		plt.show()
