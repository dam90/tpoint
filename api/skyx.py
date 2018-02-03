''' Module to handle connections to TheSkyX

The classes are defined to match the classes in Script TheSkyX. This isn't
really necessary as they all just send the javascript to TheSkyX via
SkyXConnection._send().
'''
from __future__ import print_function

import logging
import time
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR, error


logger = logging.getLogger(__name__)

class Singleton(object):
    ''' Singleton class so we dont have to keep specifing host and port'''
    def __init__(self, klass):
        ''' Initiator '''
        self.klass = klass
        self.instance = None

    def __call__(self, *args, **kwds):
        ''' When called as a function return our singleton instance. '''
        if self.instance is None:
            self.instance = self.klass(*args, **kwds)
        return self.instance


class SkyxObjectNotFoundError(Exception):
    ''' Exception for objects not found in SkyX.
    '''
    def __init__(self, value):
        ''' init'''
        super(SkyxObjectNotFoundError, self).__init__(value)
        self.value = value

    def __str__(self):
        ''' returns the error string '''
        return repr(self.value)


class SkyxConnectionError(Exception):
    ''' Exception for Failures to Connect to SkyX
    '''
    def __init__(self, value):
        ''' init'''
        super(SkyxConnectionError, self).__init__(value)
        self.value = value

    def __str__(self):
        ''' returns the error string '''
        return repr(self.value)

class SkyxTypeError(Exception):
    ''' Exception for Failures to Connect to SkyX
    '''
    def __init__(self, value):
        ''' init'''
        super(SkyxTypeError, self).__init__(value)
        self.value = value

    def __str__(self):
        ''' returns the error string '''
        return repr(self.value)
    
@Singleton
class SkyXConnection(object):
    ''' Class to handle connections to TheSkyX
    '''
    def __init__(self, host="localhost", port=3040):
        ''' define host and port for TheSkyX.
        '''
        self.host = host
        self.port = port
        
    def reconfigure(self,host="localhost", port=3040):
        ''' If we need to chane ip we can do so this way'''
        self.host = host
        self.port = port
                
    def _send(self, command):
        ''' sends a js script to TheSkyX and returns the output.
        '''
        try:
            logger.debug(command)
            sockobj = socket(AF_INET, SOCK_STREAM)
            sockobj.connect((self.host, self.port))
            sockobj.send(bytes('/* Java Script */\n' +
                               '/* Socket Start Packet */\n' + command +
                               '\n/* Socket End Packet */\n'))
            oput = sockobj.recv(2048)
            logger.debug(oput)
            sockobj.shutdown(SHUT_RDWR)
            sockobj.close()
            return oput.split("|")[0]
        except error as msg:
            raise SkyxConnectionError("Connection to " + self.host + ":" + \
                                      str(self.port) + " failed. :" + str(msg))

    def find(self, target):
        ''' Find a target
            target can be a defined object or a decimal ra,dec
        '''
        output = self._send('sky6StarChart.Find("' + target + '")')
        if output == "undefined":
            return True
        else:
            raise SkyxObjectNotFoundError(target)
                                    
    def closedloopslew(self, target=None):
        ''' Perform a closed loop slew.
            You really need to have the Automated ImageLink Settings set up
            right for this to work.
            UNTESTED
        '''
        if target != None:
            self.find(target)
        command = '''
            var nErr=0;
            ccdsoftCamera.Connect();
            ccdsoftCamera.AutoSaveOn = 1;
            ImageLink.unknownScale = 1;
            ClosedLoopSlew.Asynchronous = 1;
            ClosedLoopSlew.exec();
            nErr = ClosedLoopSlew.exec();
            '''
        oput = self._send(command)
        for line in oput.splitlines():
            print(line)
            if "Error" in line:
                raise SkyxTypeError(line)
        return True

    def takeimages(self, exposure, nimages):
        ''' Take a given number of images of a specified exposure.
        '''
        # TODO
        command = """
        var Imager = ccdsoftCamera;
        function TakeOnePhoto()
        {
            Imager.Connect();
            Imager.ExposureTime = """+str(exposure)+"""
            Imager.Asynchronous = 0;
            Imager.TakeImage();
        }

        function Main()
        {
            for (i=0; i<"""+str(nimages)+"""; ++i)
            {
                TakeOnePhoto();
            }
        }

        Main();
        """


class TheSkyXAction(object):
    ''' Class to implement the TheSkyXAction script class
    '''
    def __init__(self, host="localhost", port=3040):
        ''' Define connection
        '''
        self.conn = SkyXConnection(host, port)
        
    def TheSkyXAction(self, action):
        ''' The TheSkyXAction object allows a script to invoke a subset of
            commands listed under Preferences, Toolbars, Customize.
        '''
        command = "TheSkyXAction.execute(\"" + action + "\")"
        oput = self.conn._send(command)
        if oput == "undefined":
            return True
        else:
            raise SkyxObjectNotFoundError(oput)

class sky6ObjectInformation(object):
    ''' Class to implement the sky6ObjectInformation script class
    '''
    def __init__(self, host="localhost", port=3040):
        ''' Define connection
        '''
        self.conn = SkyXConnection(host, port)
        
    def property(self, prop):
        ''' Returns a value for the desired Sk6ObjectInformationProperty
            argument.
        '''
        command = """
                var Out = "";
                sky6ObjectInformation.Property(""" + str(prop) + """);
                Out = String(sky6ObjectInformation.ObjInfoPropOut);"""
        oput = self.conn._send(command)
        return oput

    def PropertyApplies(self, prop):
        pass

    def PropertyName(self, prop):
        pass


    def currentTargetRaDec(self, j="now"):
        ''' Attempt to get info on the current target
        '''
        if j == "now":
            command = """
                    var Out = "";
                    var Target54 = 0;
                    var Target55 = 0;
                    sky6ObjectInformation.Property(54);
                    Target54 = sky6ObjectInformation.ObjInfoPropOut;
                    sky6ObjectInformation.Property(55);
                    Target55 = sky6ObjectInformation.ObjInfoPropOut;
                    Out = String(Target54) + " " + String(Target55);
                      """        
        elif j == "2000":
            command = """
                    var Out = "";
                    var Target56 = 0;
                    var Target57 = 0;
                    sky6ObjectInformation.Property(56);
                    Target56 = sky6ObjectInformation.ObjInfoPropOut;
                    sky6ObjectInformation.Property(57);
                    Target57 = sky6ObjectInformation.ObjInfoPropOut;
                    Out = String(Target56) + " " + String(Target57);
                      """
        else:
            raise SkyxTypeError("Unknown epoch: " + j)
        output = self.conn._send(command).splitlines()[0].split()    
        return output
    
    def sky6ObjectInformation(self, target):
        ''' Method to return basic SkyX position information on a target.
        '''
        # TODO: make target optional
        # TODO: return all data
        command = """
                var Target = \"""" + target + """\";
                var Target56 = 0;
                var Target57 = 0;
                var Target58 = 0;
                var Target59 = 0;
                var Target77 = 0;
                var Target78 = 0;
                var Out = "";
                var err;
                sky6StarChart.LASTCOMERROR = 0;
                sky6StarChart.Find(Target);
                err = sky6StarChart.LASTCOMERROR;
                if (err != 0) {
                            Out = Target + " not found."
                } else {
                            sky6ObjectInformation.Property(56);
                            Target56 = sky6ObjectInformation.ObjInfoPropOut;
                            sky6ObjectInformation.Property(57);
                            Target57 = sky6ObjectInformation.ObjInfoPropOut;
                            sky6ObjectInformation.Property(58);
                            Target58 = sky6ObjectInformation.ObjInfoPropOut;
                            sky6ObjectInformation.Property(59);
                            Target59 = sky6ObjectInformation.ObjInfoPropOut;
                            sky6ObjectInformation.Property(77);
                            Target77 = sky6ObjectInformation.ObjInfoPropOut;
                            sky6ObjectInformation.Property(78);
                            Target78 = sky6ObjectInformation.ObjInfoPropOut;
                            Out = "sk6ObjInfoProp_RA_2000:"+String(Target56)+
                            "\\nsk6ObjInfoProp_DEC_2000:"+String(Target57)+
                            "\\nsk6ObjInfoProp_AZM:"+String(Target58)+
                            "\\nsk6ObjInfoProp_ALT:"+String(Target59)+
                            "\\nsk6ObjInfoProp_RA_RATE_ASPERSEC:"+String(Target77)+
                            "\\nsk6ObjInfoProp_DEC_RATE_ASPERSEC:"+String(Target78)+"\\n";

                }
                """
        results = {}
        oput = self.conn._send(command)
        for line in oput.splitlines():
            if "Object not found" in line:
                raise SkyxObjectNotFoundError("Object not found.")
            if ":" in line:
                info = line.split(":")[0]
                val = line.split(":")[1]
                results[info] = val
        return results


class ccdsoftCamera(object):
    ''' Class to implement the ccdsoftCamera script class
    '''
    def __init__(self, host="localhost", port=3040):
        ''' Define connection
        '''
        self.conn = SkyXConnection(host, port)
        self.frames = {1:"Light", 2:"Bias", 3:"Dark", 4:"Flat Field"}
        
    def Connect(self, async=0):
        ''' Connect to the camera defined in the TheSkyX profile
      
            Returns True on success or throws a SkyxTypeError
        '''
        command = """
                    var Imager = ccdsoftCamera;
                    var Out = "";
                    Imager.Connect();
                    Imager.Asynchronous = """ + str(async) + """;
                    Out = Imager.Status;
                    """
        output = self.conn._send(command).splitlines()
        if "Ready" not in output[0]:
            raise SkyxTypeError(output[0])
        return True

    def Disconnect(self):
        ''' Disconnect the camera
            Returns True on success or throws a SkyxTypeError
        '''
        command = """
                    var Imager = ccdsoftCamera;
                    var Out = "";
                    Imager.Disconnect();
                    Out = Imager.Status;
                  """
        output = self.conn._send(command).splitlines()
        if "Not Connected" not in output[0]:
            raise SkyxTypeError(output[0])
        return True
    
    def ExposureTime(self, exptime=None):
        ''' Set the exposure time to the given argument or return the 
            current exposure time.
        '''
        if exptime == None:
            command = "ccdsoftCamera.ExposureTime"
            return(self.conn._send(command).splitlines()[0])

        command = "ccdsoftCamera.ExposureTime = " + str(exptime) + ";"
        output = self.conn._send(command).splitlines()
        if output[0] != str(exptime):
            raise SkyxTypeError(output[0])
        return(output[0])
    
    def Bin(self, binning=None):
        ''' Set the binning or return the current binning
        
            We assume NxN binning so just set/get BinX
        '''
        if binning == None:
            command = "ccdsoftCamera.BinX"
            return(self.conn._send(command).splitlines()[0])
        command = "ccdsoftCamera.BinX = " + str(binning) + ";"
        output = self.conn._send(command).splitlines()
        if output[0] != str(binning):
            raise SkyxTypeError(output[0])
        return(output[0])
            
    def Frame(self, frame=None):
        ''' Set the Frame type or return the current type

            Be careful setting 'Dark' as the frame as this will open
            a dialog on screen.
        '''
        if frame == None:
            command = "ccdsoftCamera.Frame"
            itype = self.conn._send(command).splitlines()[0]
            return(self.frames[int(itype)])
        try:
            frameid = [x for x in self.frames if self.frames[x] == frame][0]
        except:
            raise SkyxTypeError("Unknown Frame type. Must be one of: " +
                                str(self.frames))
        command = "ccdsoftCamera.Frame = " + str(frameid) + ";"
        output = self.conn._send(command).splitlines()
        if output[0] != str(frameid):
            raise SkyxTypeError(output[0])
        return(frame)
                               
    def Series(self, num=None):
        ''' Set the number of images in a series to num or return the
            current number.
        '''
        #TODO
        pass
    
    def TakeImage(self):
        ''' Takes an image.
        '''
        #TODO
        pass


class sky6RASCOMTele(object):
    ''' Class to implement the ccdsoftCamera script class
    '''
    def __init__(self, host="localhost", port=3040):
        ''' Define connection
        '''
        self.conn = SkyXConnection(host, port)
        
    def Connect(self):
        ''' Connect to the telescope
        '''
        command = """
                  var Out;
                  sky6RASCOMTele.Connect();
                  Out = sky6RASCOMTele.IsConnected"""
        output = self.conn._send(command).splitlines()
        if int(output[0]) != 1:
            raise SkyxTypeError("Telescope not connected. "+\
                                "sky6RASCOMTele.IsConnected=" + output[0])
        return True
        
    def Disconnect(self):
        ''' Disconnect the telescope
            Whatever this actually does...
        '''
        command = """
                  var Out;
                  sky6RASCOMTele.Disconnect();
                  Out = sky6RASCOMTele.IsConnected"""
        output = self.conn._send(command).splitlines()
        if int(output[0]) != 0:
            raise SkyxTypeError("Telescope still connected. " +\
                                "sky6RASCOMTele.IsConnected=" + output[0])
        return True

    def GetRaDec(self):
        ''' Get the current RA and Dec
        '''
        command = """
                  var Out;
                  sky6RASCOMTele.GetRaDec();
                  Out = String(sky6RASCOMTele.dRa) + " " + String(sky6RASCOMTele.dDec);
                  """
        output = self.conn._send(command).splitlines()[0].split()      
        return output

    def GetAzAlt(self):
        ''' Get the current Az and Alt
        '''
        command = """
                  var Out;
                  sky6RASCOMTele.GetAzAlt();
                  Out = String(sky6RASCOMTele.dAz) + " " + String(sky6RASCOMTele.dAlt);
                  """
        output = self.conn._send(command).splitlines()[0].split()      
        return output

    def GetPointing(self):
        ''' Get the current RA and Dec and az/alt
        '''
        command = """
                  var Out;
                  sky6RASCOMTele.GetRaDec();
                  sky6RASCOMTele.GetAzAlt();
                  Out = String(sky6RASCOMTele.dRa) + " " + String(sky6RASCOMTele.dDec) + " " + String(sky6RASCOMTele.dAz) + " " + String(sky6RASCOMTele.dAlt);
                  """
        output = self.conn._send(command).splitlines()[0].split()      
        return output
    
    def Sync(self, pos):
        ''' Sync to a given pos [ra, dec]
            ra, dec should be Jnow coordinates
        '''
        command = """
                var Out = "";
                sky6RASCOMTele.Sync(""" + pos[0] + "," + pos[1] + """, "pyskyx");
                """
        output = self.conn._send(command).splitlines()
        print(output)
        time.sleep(1)
        print(self.GetRaDec())

    def SlewToRaDec(self, pos):
        ''' Sync to a given pos [ra, dec]
            ra, dec should be Jnow coordinates
        '''
        command = """
                var Out = "";
                sky6RASCOMTele.SlewToRaDec(""" + str(pos[0]) + "," + str(pos[1]) + ""","");
                """
        output = self.conn._send(command).splitlines()
        #print(output)
        time.sleep(1)
        #print(self.GetRaDec())

    def SlewToAzAlt(self, pos):
        ''' Sync to a given pos [ra, dec]
            ra, dec should be Jnow coordinates
        '''
        command = """
                var Out = "";
                sky6RASCOMTele.SlewToAzAlt(""" + str(pos[0]) + "," + str(pos[1]) + ""","");
                """
        output = self.conn._send(command).splitlines()
        #print(output)
        time.sleep(1)
        #print(self.GetAzAlt())

    def GetTime(self):
        ''' Get the current RA and Dec and az/alt
        '''
        command = """
                  var Out;
                  Out = sky6Web.TimeString;
                  """
        output = self.conn._send(command)#.splitlines()[0].split()      
        return output