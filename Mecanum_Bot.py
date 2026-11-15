import time
from DriveTrain import DriveTrain
from Website import Website

driveTrain = DriveTrain()
website = Website(port=8000)          # add token="yourpassword" to require a password

PERIOD = 0.02   # 20 ms = 50 updates per second
next_time = time.monotonic()


def main():
    # 1. Get the latest command from the web page (zeros if disconnected or stopped)
    forward, strafe, rotation = website.get_command()

    # 2. Drive
    driveTrain.drive(forward, strafe, rotation)
    driveTrain.update()

    # 3. Send data to the page and the log file
    website.set_telemetry({
        "cmd": {"forward": forward, "strafe": strafe, "rotation": rotation},
        "estop": int(website.estopped),
        # Add your own values from DriveTrain, for example:
        # "rpm": {"fl": driveTrain.fl.encoder.rpm, "fr": driveTrain.fr.encoder.rpm,
        #         "rl": driveTrain.rl.encoder.rpm, "rr": driveTrain.rr.encoder.rpm},
    })


if __name__ == '__main__':
    website.start()
    try:
        while True:
            main()

            # timing stuff
            next_time += PERIOD
            delay = next_time - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            else:
                next_time = time.monotonic()   # fell behind, so reset the schedule
    finally:
        driveTrain.drive(0, 0, 0)
        website.stop()
