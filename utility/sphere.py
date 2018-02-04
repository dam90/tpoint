#! python
import numpy as np

def regular_points(d):
	'''
	Create a regular distribution of points on a sphere, where
	the average area per point is d^2 (radians^2).
	Input:
		d: half-dimension of unit area, required
	Ouput:
		  V: is the polar angle (degrees)
		Phi: is the azimuth angle (degrees)
	'''
	V = []
	Phi = []
	a = d**2
	pi = np.pi
	Mv = np.round(pi/d)
	dv = pi/Mv
	dphi = a/dv
	for m in range (0,int(Mv)):
		V_current = pi*(m + 0.5)/Mv
		Mphi = np.round(2*pi*np.sin(V_current)/dphi)
		for n in range(0,int(Mphi)):
			Phi.append(np.rad2deg(2*pi*n/Mphi))
			V.append(np.rad2deg(V_current))
	return V,Phi

def n_regular_points(N=200,r=1):
	'''
	Create a regular distribution of N points on a sphere.
	Input:
		N: Number of points, defaults to 200
	Ouput:
		  V: is the polar angle (degrees)
		Phi: is the azimuth angle (degrees)
	'''
	pi = np.pi
	a = (4*pi*(r**2))/N
	d = np.sqrt(a)
	return regular_points(d)

def area_regular_points(d=4):
	'''
	Create a regular distribution of points on a sphere, where
	the average area per point is d^2 (degrees^2).
	Input:
		d: half-dimension of unit area, defaults to 4 degrees
	Ouput:
		  V: is the polar angle (degrees)
		Phi: is the azimuth angle (degrees)
	'''
	pi = np.pi
	d = d*pi/180
	return regular_points(d)

def plot3D(az,el):
	'''
	Given az/el in degrees, plot in 3d
	'''
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
	ax.set_zlim(-1,1)
	ax.set_xlabel('X')
	ax.set_ylabel('Y')
	ax.set_zlabel('Z')
	plt.show()

def test():
	# points:
	V,Phi = area_regular_points(7)
	# create az/el:
	az = Phi
	el = []
	for v in V:
		el.append(90.0-v)
	# plot:
	plot3D(az,el)

if __name__ == "__main__":
	test()