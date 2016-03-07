__author__ = 'Kristy'

import time


def main(level=2):
    """
    Run the 'static server' that imitates real-time streaming behaviour.
    Depending on the level chosen, this is run on:
    - one pre-defined datafile (level=0),
    - in the command line (level=1)
    - or as a GUI (level=2), where the datafiles are found in a .txt list in the path defined in the properties file.
    """

    if level == 0:
        # perform most basic server testing, using one static file only.
        from ematoblender.scripts.ema_io.ema_staticserver import rtserver as rts
        st, so = rts.initialise_server(datafile=datafile, loop=loop)

        print('Starting first server thread.')
        st.start()

        # let the server keep serving, verbosely
        while st.is_alive():
            print("Server still alive; emulating file '{}' with looping set to {}.".format(st.datafile, st.loop))
            time.sleep(30)
            pass

    elif level == 1:
        # use the command-line server-switcher
        from ematoblender.scripts.ema_io.ema_staticserver import rtserver_switcher as rtss
        rtss.main()

    else:
        # use the gui switcher
        from ematoblender.scripts.ema_io.ema_staticserver import rtserver_gui as rtg
        rtg.main()


if __name__ == "__main__":
    datafile = './data/Example3.tsv'
    loop = True
    main()