__author__ = 'Kristy'

from threading import Thread
import time
import socket

def main():
    print('WARNING: ensure that either NDI-WAVE or RTSERVER is running to provide the information.')
    print('You can test the NDI-WAVE or RTSERVER using scripts.ema_io.ema_staticserver.rtserver_tester')

    testing_passive = False  # simply start
    testing_active = True  # pretend to make some calls from Blender

    if testing_passive:  # for running the gameserver in a thread, to operate normally
        from ematoblender.scripts.ema_io.ema_gameserver import gameserver as gs
        from ematoblender.scripts.ema_shared.properties import game_server_cl_args

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

        from ematoblender.scripts.ema_shared.properties import gameserver_host, gameserver_port
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        SHOST = gameserver_host
        SPORT = gameserver_port
        data = 'TEST_ALIVE'
        sock.sendto(bytes(data + "\n", encoding='ascii'), (SHOST, SPORT))
        received = sock.recv(1024)
        print('I received', received)
        exit()



        import ematoblender.scripts.ema_blender.blender_networking as bn

        gs_soc_blocking = bn.setup_socket_to_gameserver(blocking=True, port=9444)
        bn.send_to_gameserver(gs_soc_blocking, mode='TEST_ALIVE')
        time.sleep(0.2)  # wait for game server to reply before making a query
        reply = bn.recv_from_gameserver(gs_soc_blocking)

        exit()



        from ematoblender.scripts.ema_blender.blender_networking import run_game_server
#        run_game_server()

        import ematoblender.scripts.ema_blender.blender_networking as bn
        ## debugging s = bn.setup_socket_to_gameserver(blocking=False)
        s = bn.setup_socket_to_gameserver(blocking=True)

        print('Performing some simple tests.')

        # check that the gameserver is alive
        from ematoblender.scripts.ema_blender.blender_networking import send_to_gameserver
        from ematoblender.scripts.ema_blender.blender_networking import wait_til_recv

        send_to_gameserver(s, mode='TEST_ALIVE')
        response = wait_til_recv(s)
        exit()


        confirm = [send_to_gameserver(s, mode='SINGLE_DF') for i in range(10)]
        #assert str(type(single_dfs[0])) == 'DataFrame'
        response = wait_til_recv(s)
        for i in response:
            print(i)
        exit()

        parameters = send_to_gameserver(s, mode='PARAMETERS')
        from xml.etree.ElementTree import ElementTree as ET
        print(type(parameters))
        print(parameters)

        stream_dfs = []
        mydf = send_to_gameserver(s, mode="START_STREAM")
        print('start streaming df:', mydf)

        from ematoblender.scripts.ema_io.rtc3d_parser import DataFrame
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
