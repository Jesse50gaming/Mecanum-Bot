from gpiozero import Motor, DigitalInputDevice
from simple_pid import PID
from Mecanum_Module import Mecanum_Module

class DriveTrain:
    #DriveTrain Constants
    MAX_MOTOR_RPM = 400
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
    pid = PID(0,0,0, setpoint=0, sample_time=None, output_limits=(-1, 1))

    def __init__(self):
        self.frontLeftModule = Mecanum_Module(self.FRONT_LEFT_PINS[0],self.FRONT_LEFT_PINS[1],self.FRONT_LEFT_PINS[2],self.FRONT_LEFT_PINS[3],self.FRONT_LEFT_PINS[4],self.MAX_MOTOR_RPM,self.pid)
        self.frontRightModule = Mecanum_Module(self.FRONT_RIGHT_PINS[0],self.FRONT_RIGHT_PINS[1],self.FRONT_RIGHT_PINS[2],self.FRONT_RIGHT_PINS[3],self.FRONT_RIGHT_PINS[4],self.MAX_MOTOR_RPM,self.pid)
        self.rearLeftModule = Mecanum_Module(self.REAR_LEFT_PINS[0],self.REAR_LEFT_PINS[1],self.REAR_LEFT_PINS[2],self.REAR_LEFT_PINS[3],self.REAR_LEFT_PINS[4],self.pid)
        self.rearRightModule = Mecanum_Module(self.REAR_RIGHT_PINS[0],self.REAR_RIGHT_PINS[1],self.REAR_RIGHT_PINS[2],self.REAR_RIGHT_PINS[3],self.REAR_RIGHT_PINS[4],self.MAX_MOTOR_RPM,self.pid)

    #Normalized Values
    def drive(self,forward,strafe,rotation):
        if forward > 1 : forward = 1
        if forward < -1 : forward = -1
        if strafe > 1 : strafe = 1
        if strafe < -1 : strafe = -1
        if rotation > 1 : rotation = 1
        if rotation < -1 : rotation = -1

        FL_Speed = forward + strafe + rotation
        FR_Speed = forward - strafe - rotation
        RL_Speed = forward - strafe + rotation
        RR_Speed = forward + strafe - rotation

        maxSpeed = max(FL_Speed,FR_Speed,RL_Speed,RR_Speed)

        if maxSpeed > 1:
            FL_Speed /= maxSpeed
            FR_Speed /= maxSpeed
            RL_Speed /= maxSpeed
            RR_Speed /= maxSpeed

        self.frontLeftModule.set_target_rpm(FL_Speed)
        self.frontRightModule.set_target_rpm(FR_Speed)
        self.rearLeftModule.set_target_rpm(RL_Speed)
        self.rearRightModule.set_target_rpm(RR_Speed)

    