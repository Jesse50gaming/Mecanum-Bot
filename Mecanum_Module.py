import time
from gpiozero import Motor
from simple_pid import PID
from Encoder import Encoder


class Mecanum_Module:
    """One motor + its encoder + a PID controller that holds a target speed."""

    def __init__(self, enable, in1, in2, enc_a, enc_b, max_rpm=400, pid = PID(0,0,setpoint=0, sample_time=None, output_limits=(-1, 1)), reverse_encoder=False):
        self.motor = Motor(forward=in1, backward=in2, enable=enable)
        self.encoder = Encoder(enc_a, enc_b, reverse=reverse_encoder)
        self.max_rpm = max_rpm
        self.target_rpm = 0

        # The PID works with speeds as a fraction of max_rpm (-1 to 1),
        # and its output is motor power (-1 to 1).
        self.pid = pid
        self._full_power_since = None   # used by the safety check

    def set_target_rpm(self, rpm):
        """Set the wheel speed you want. Negative is backward."""
        self.target_rpm = max(-self.max_rpm, min(self.max_rpm, rpm))
        self.pid.setpoint = self.target_rpm / self.max_rpm

    def update(self):
        """Call this about 50 times a second."""
        self.encoder.update()                       # measure speed

        if self.target_rpm == 0:                    # asked to stop
            self.motor.stop()
            self.pid.reset()
            self._full_power_since = None
            return

        measured = self.encoder.rpm / self.max_rpm  # how fast it is going now
        power = self.pid(measured)                  # PID decides the power
        self._drive(power)
        self._safety_check(power)

    def _drive(self, power):
        if power > 0:
            self.motor.forward(power)
        elif power < 0:
            self.motor.backward(-power)
        else:
            self.motor.stop()

    def _safety_check(self, power):
        """If the motor is at full power but the wheel isn't moving
        (encoder unplugged, wheel jammed), stop instead of running away."""
        stuck = abs(power) > 0.9 and abs(self.encoder.rpm) < 5
        if not stuck:
            self._full_power_since = None
            return
        if self._full_power_since is None:
            self._full_power_since = time.monotonic()
        elif time.monotonic() - self._full_power_since > 1.0:
            self.stop()
            raise RuntimeError("Motor stalled or encoder not counting. Stopped.")

    def stop(self):
        self.set_target_rpm(0)
        self.motor.stop()
        self.pid.reset()