from gpiozero import Motor, DigitalInputDevice
from simple_pid import PID
from Mecanum_Module import Mecanum_Module

class DriveTrain:
    #DriveTrain Constants
    # [enable,forward,reverse,sensor A, sensor B]
    #FRONT LEFT 
    FRONT_LEFT_PINS = [12,5,6,2,3]
    #FRONT RIGHT 
    FRONT_RIGHT_PINS = [13,16,26,4,14]
    #REAR LEFT
    REAR_LEFT_PINS = [19,23,24,15,17]
    #REAR RIGHT
    REAR_RIGHT_PINS = [18,25,11,27,22]

    #PID
    pid = PID(0,0,0)

    def __init__(self):
        frontLeftModule = Mecanum_Module(self.FRONT_LEFT_PINS[0],self.FRONT_LEFT_PINS[1],self.FRONT_LEFT_PINS[2],self.FRONT_LEFT_PINS[3],self.FRONT_LEFT_PINS[4],self.pid)
        frontRightModule = Mecanum_Module(self.FRONT_RIGHT_PINS[0],self.FRONT_RIGHT_PINS[1],self.FRONT_RIGHT_PINS[2],self.FRONT_RIGHT_PINS[3],self.FRONT_RIGHT_PINS[4],self.pid)
        rearLeftModule = Mecanum_Module(self.REAR_LEFT_PINS[0],self.REAR_LEFT_PINS[1],self.REAR_LEFT_PINS[2],self.REAR_LEFT_PINS[3],self.REAR_LEFT_PINS[4],self.pid)
        rearRightModule = Mecanum_Module(self.REAR_RIGHT_PINS[0],self.REAR_RIGHT_PINS[1],self.REAR_RIGHT_PINS[2],self.REAR_RIGHT_PINS[3],self.REAR_RIGHT_PINS[4],self.pid)

    