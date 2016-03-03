__author__ = 'Kristy'

"""
Module that runs rtserver in the command line, switching between different datafiles as experiment progresses.
Use KeyboardInterrupt to see the file list to choose another file.
A second KeyboardInterrupt closes the program.
"""

import os
import sys
import time
import scripts.ema_shared.properties as pps
import scripts.ema_io.ema_staticserver.rtserver as rts

sys.path.insert(0, os.getcwd())


def main():
    """Run the script in the console."""
    # open the file of filenames
    abspath = os.path.abspath(pps.mocap_list_of_files)
    print('reading mocap file list from', abspath)
    with open(abspath, 'r') as f:
        files = [fi.rstrip('\t\r\n') for fi in f.readlines()]
    print(files)

    # start the server
    loop_status = True
    server_thread, server = rts.initialise_server(datafile=files[0], loop=loop_status)
    server_thread.start()

    while server_thread.is_alive():
        try:
            print('Server is still alive, file:{}, loop: {}'
                  .format(rts.FakeRTRequestHandler.datafile, rts.FakeRTRequestHandler.loop))
            time.sleep(5)
        except KeyboardInterrupt as e:
            print('\nChoose a file to stream from the list by its number,\n'
                  'LOOP to toggle looping,\n '
                  'or nothing to quit.:')
            for i, fn in enumerate(files):
                print(i, '\t', fn)
            next_index = input('Next file index:')

            if next_index.isnumeric():
                if int(next_index) < 0 or int(next_index) >= len(files):
                    print('Invalid index')
                    continue
                else:
                    server.change_datafile(files[int(next_index)])

            elif next_index.lower().startswith('loop'):
                loop_status = not loop_status
                server.change_loop(loop_status)

            elif next_index == '':
                exit()
                break
        finally:
            pass

    print('Server closed. Now exiting.')

if __name__ == "__main__":
    main()