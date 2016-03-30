__author__ = 'Kristy'

import sys, os
import time
import argparse
import scripts.ema_io.ema_staticserver.rtserver as rts


def main(level=2):
    """
    Run the 'static server' that imitates real-time streaming behaviour.
    Depending on the level chosen, this is run on:
    - one pre-defined datafile (level=0),
    - in the command line (level=1)
    - or as a GUI (level=2), where the datafiles are found in a .txt list in the path defined in the properties file.
    """

    if not args.gui and args.collection is None:
        if args.file is not None:
            # perform most basic server testing, using a given file only.
            st, so = rts.initialise_server(datafile=args.file, loop=loop)
        else: # no args.file given, use the default
            st, so = rts.initialise_server(datafile=datafile, loop=loop)

        print('Starting first server thread.')
        st.start()

        # let the server keep serving, verbosely
        while st.is_alive():
            print("Server still alive; emulating file '{}' with looping set to {}.".format(so.datafile, so.server_loop))
            try:
                time.sleep(30)
            except KeyboardInterrupt:
                break

    elif not args.gui and args.collection is not None:
        # use the command-line server-switcher with the given collection
        import scripts.ema_io.ema_staticserver.rtserver_switcher as rtss
        rtss.main(collection=args.collection)

    elif args.gui and args.collection is not None:
        sys.stdout = open(os.devnull, "w")
        # use the GUI with a custom collection
        import scripts.ema_io.ema_staticserver.rtserver_gui as rtg
        rtg.main(collection=args.collection)

    else:
        sys.stdout = open(os.devnull, "w")
        # use the gui switcher with the default collection
        import scripts.ema_io.ema_staticserver.rtserver_gui as rtg
        rtg.main()


if __name__ == "__main__":
    datafile = './data/Example3.tsv'
    loop = True

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-c", "--collection", help="specify a text file with EMA datafiles for switching")
    group.add_argument("-f", "--file", help="stream a single file only ")
    parser.add_argument("-g", "--gui", help="use the GUI", action="store_true")
    args = parser.parse_args()
    print(args)

    main()
