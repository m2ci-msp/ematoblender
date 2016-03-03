__author__ = 'Kristy'

from threading import Thread
import time


def main():
    print('WARNING: ensure that either NDI-WAVE or RTSERVER is running to provide the information.')
    print('You can test the NDI-WAVE or RTSERVER using scripts.ema_io.ema_staticserver.rtserver_tester')

    testing_passive = True  # simply start
    testing_active = True  # pretend to make some calls from Blender

    if testing_passive:  # for running the gameserver in a thread, to operate normally
        from scripts.ema_io.ema_gameserver import gameserver as gs
        from scripts.ema_shared.properties import game_server_cl_args

        print('About to run the gameserver with arguments in pps file')
        print('CL args are:', game_server_cl_args)

        gst = Thread(target=gs.main)
        gst.daemon = True
        gst.start()  # run the gameserver
        time.sleep(10)  # allow time for setting up head correction

        if not testing_active:
            while True:
                print('Game Server is running')
                time.sleep(30)

    # tests communication from Blender to GS
    if testing_active:  # for testing, runs here and also performs tests
        from scripts.ema_blender.blender_networking import run_game_server
#        run_game_server()
        import scripts.ema_blender.blender_networking as bn
        s = bn.setup_socket_to_gameserver(blocking=False)

        print('Performing some simple tests.')
        from scripts.ema_blender.blender_networking import send_to_gameserver
        print(send_to_gameserver(s, mode='TEST_ALIVE'))
        single_dfs = [send_to_gameserver(s) for i in range(10)]
        for df in single_dfs:
            print("\nsingle_df:", df)

        parameters = send_to_gameserver(s, mode='PARAMETERS')
        from xml.etree.ElementTree import ElementTree as ET
        print(type(parameters))
        print(parameters)

        stream_dfs = []
        mydf = send_to_gameserver(s, mode="START_STREAM")
        print('start streaming df:', mydf)

        from scripts.ema_io.rtc3d_parser import DataFrame
        while True:
            send_to_gameserver(s, mode='STREAM_DF')
            this_df = b''
            try:
                this_df = bn.recv_from_gameserver(s)
            except BlockingIOError:
                pass
            #print(this_df)
            if type(this_df) == DataFrame:

                ts = this_df.give_timestamp_secs()
                print('\n\n', ts)
                if ts > 100:
                    break
        send_to_gameserver(s, mode="STREAM_STOP")
        for df in stream_dfs:
            print("stream df:", df)

if __name__ == "__main__":
    main()