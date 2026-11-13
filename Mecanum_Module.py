from gpiozero import Motor, DigitalInputDevice
from simple_pid import PID

class Mecanum_Module:

    def __init__(self, enablePin, forwardPin, reversePin, sensAPin, sensBPin,pid:PID):
        self.motor = Motor(forwardPin,reversePin,enablePin)# create motor
        self.pid = pid
        
        #TODO: make encoder

    #Normalized pls
    def drive(self,speed):
        #make sure in bounds
        if speed > 1: speed = 1
        if speed < -1: speed = -1

        if speed > 0:
            self.motor.forward(speed)
        elif speed < 0:
            self.motor.backward(speed)
        else:
            self.motor.stop()
        
        


        