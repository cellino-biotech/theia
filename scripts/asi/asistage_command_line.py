# ===============================================================================
#    Send serial commands to ASI stage
# ===============================================================================

from asistage import MS2000


def main():
    stage = MS2000("COM3", 115200)

    while True:
        cmd = input("--> ")

        if cmd != "q" and cmd != "Q": 
            stage.send_command(cmd)
            stage.read_response()
        else:
            break
    stage.close()


if __name__ == "__main__":
    print(
        "Welcome to the ASI serial command program. Common commands include"
        "'MOVE X=? Y=?' and 'WHERE X Y'. When finished, press 'q' to quit."
    )

    main()
