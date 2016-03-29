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
        sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        SHOST = gameserver_host
        SPORT = gameserver_port

        # basic tests for connectivity
        data = ['TEST_ALIVE', 'SINGLE_DF', 'SINGLE_DF', 'SINGLE_DF']
        for d in data:
            print('I sent', d)
            sock.sendto(bytes(d + "\n", encoding='ascii'), (SHOST, SPORT))
            received = sock.recv(1024)
            print('I received', received)
            
        sock2.sendto(bytes(data[0] + "\n", encoding='ascii'), (SHOST, SPORT))
        received = sock2.recv(1024)
        
      
        # bests using the blender_networking module
        from ematoblender.scripts.ema_blender.blender_networking import main as bnmain
        bnmain()


if __name__ == "__main__":
    main()
