import math
import time
from gpiozero import DigitalInputDevice


class Encoder:
    # The forward order of settings, as (A, B) pairs
    FORWARD = [(0, 0), (0, 1), (1, 1), (1, 0)]

    def __init__(self, a_pin, b_pin, counts_per_rev=640,wheel_diameter_mm=60, reverse=False):
        self.counts_per_rev = counts_per_rev
        self.wheel_circumference_mm = math.pi * wheel_diameter_mm
        self.direction_sign = -1 if reverse else 1  # set reverse=True to flip direction

        self.a = DigitalInputDevice(a_pin, pull_up=None, active_state=True)
        self.b = DigitalInputDevice(b_pin, pull_up=None, active_state=True)
        self.count = 0
        self.last = (self.a.value, self.b.value)

        # Used for speed measurement
        self._speed_last_count = 0
        self._speed_last_time = time.monotonic()
        self._speed_cps = 0.0

        for pin in (self.a, self.b):
            pin.when_activated = self._update_count
            pin.when_deactivated = self._update_count

    # ---------- Counting (runs automatically on every edge) ----------

    def _update_count(self):
        new = (self.a.value, self.b.value)
        if new == self.last:
            return  # nothing changed

        last_position = self.FORWARD.index(self.last)
        new_position = self.FORWARD.index(new)

        if new_position == (last_position + 1) % 4:
            self.count += self.direction_sign   # next setting in the forward list
        elif new_position == (last_position - 1) % 4:
            self.count -= self.direction_sign   # previous setting in the list
        # anything else means a missed step, so ignore it

        self.last = new

    # ---------- Position getters (use any time) ----------

    @property
    def position_counts(self):
        """Raw count since start or last reset."""
        return self.count

    @property
    def revolutions(self):
        """Wheel revolutions since start or last reset."""
        return self.count / self.counts_per_rev

    @property
    def degrees(self):
        """Wheel angle in degrees since start or last reset."""
        return self.revolutions * 360

    @property
    def distance_mm(self):
        """Distance the wheel has rolled, in millimetres."""
        return self.revolutions * self.wheel_circumference_mm

    def reset(self):
        """Set the position back to zero."""
        self.count = 0
        self._speed_last_count = 0

    # ---------- Speed getters (call update() once per loop first) ----------

    def update(self):
        """Measure speed since the last call to update()."""
        now = time.monotonic()
        elapsed = now - self._speed_last_time
        if elapsed < 0.001:
            return  # too soon to measure
        counts_moved = self.count - self._speed_last_count
        self._speed_cps = counts_moved / elapsed
        self._speed_last_count = self.count
        self._speed_last_time = now

    @property
    def speed_cps(self):
        """Speed in counts per second (negative means backward)."""
        return self._speed_cps

    @property
    def rpm(self):
        """Wheel speed in revolutions per minute."""
        return self._speed_cps / self.counts_per_rev * 60

    @property
    def speed_mm_s(self):
        """Wheel rim speed in millimetres per second."""
        return self._speed_cps / self.counts_per_rev * self.wheel_circumference_mm

    @property
    def direction(self):
        """'forward', 'backward' or 'stopped'."""
        if self._speed_cps > 0:
            return "forward"
        if self._speed_cps < 0:
            return "backward"
        return "stopped"