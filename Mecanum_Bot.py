import time
from DriveTrain import DriveTrain


driveTrain = DriveTrain()

PERIOD = 0.02   # 20 ms = 50 updates per second
next_time = time.monotonic()

def main():
    driveTrain.update()

if __name__ == '__main__':
    try:
        while True:
            main()

            #timing stuff
            next_time += PERIOD
            delay = next_time - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            else:
                next_time = time.monotonic()   # fell behind, so reset the schedule
    finally:
        driveTrain.drive(0,0,0)