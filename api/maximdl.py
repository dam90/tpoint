import time
import win32com.client
 
ERROR = True
NOERROR = False
 
class Camera:
	def __init__(self):
		print "Connecting to MaxIm DL..."
		self.__CAMERA = win32com.client.Dispatch("MaxIm.CCDCamera")
		self.__CAMERA.DisableAutoShutdown = True
		try:
			self.__CAMERA.LinkEnabled = True
		except:
			print "... cannot connect to camera"
			print "--> Is camera hardware attached?"
			print "--> Is some other application already using camera hardware?"
			raise EnvironmentError, 'Halting program'
		if not self.__CAMERA.LinkEnabled:
			print "... camera link DID NOT TURN ON; CANNOT CONTINUE"
			raise EnvironmentError, 'Halting program'
 
	def expose(self,length,filterSlot=0):
		print "Exposing light frame..."
		self.__CAMERA.Expose(length,1,filterSlot)
		while not self.__CAMERA.ImageReady:
			time.sleep(1)
		print "Light frame exposure and download complete!"
 
	def setFullFrame(self):
		self.__CAMERA.SetFullFrame()
		print "Camera set to full-frame mode"

	def saveImage(self,directory_path):
		print "saving FITS image to: " + directory_path
		return self.__CAMERA.SaveImage(directory_path)
		
	def setFitsKey(self,key,value):
		print "Setting FITS value: {",key,":",value,"}"
		self.__CAMERA.SetFITSKey(key,value)
		
	def setBinning(self,binmode):
		tup = (1,2,3)
		if binmode in tup:
			self.__CAMERA.BinX = binmode
			self.__CAMERA.BinY = binmode
			print "Camera binning set to %dx%d" % (binmode,binmode)
			return NOERROR
		else:
			print "ERROR: Invalid binning specified"
			return ERROR

if __name__ == "__main__":
	c = Camera()
	c.setFullFrame()
	c.expose(0.1)
	c.setFitsKey("keyA","ValueA")
	c.setFitsKey("keyB",1232.12312)
	c.saveImage("C:\\Users\\Dave\\Desktop\\test.fit")
