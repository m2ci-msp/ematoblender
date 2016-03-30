__author__ = 'Kristy'

import sys, os

#import scripts.ema_io.ema_gameserver.gameserver as gs
if True:
        from scripts.ema_io.ema_gameserver import gameserver_gui as gg
        sys.stdout = open(os.devnull, "w")
        gg.main(sys.argv[1:]) # command line args are pre-defined as those in properties file

else:
	from scripts.ema_io.ema_gameserver import gameserver as gs
	gs.main(sys.argv[1:])
