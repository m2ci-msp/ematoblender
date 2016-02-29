import threading
import random
import time
from collections import deque

class Producer(threading.Thread):
    """
    Produces the curret line of data from the static file.
    """
    def __init__(self, framelist, condition, mocap_parser):
        """
        Constructor.
        @param framelist deque with current frame
        @param condition condition synchronization object
        @param mocap_parser, to ge
        """
        threading.Thread.__init__(self)
        self.current_frame = framelist
        self.condition = condition
        self.mocap_parser = mocap_parser

    def run(self):
        """
        Thread run method. Append most recent frame to deque, sleep some.
        """
        while True:
            line = self.mocap_parser.give_motion_frame()
            self.condition.acquire()
            self.current_frame.append(line)
            self.condition.notify()
            self.condition.release()
            time.sleep(1) #TODO: Integrate timer here

class Consumer(threading.Thread):
    """
    Consumes the available mocap data.
    """
    def __init__(self, framelist, condition):
        """
        Constructor.
        @param framelist deque with current frame data
        @param condition condition synchronization object
        """
        threading.Thread.__init__(self)
        self.frames = framelist
        self.condition = condition

    def run(self):
        """
        Thread run method. Consumes integers from list
        """
        while True:
            self.condition.acquire()
            while True:
                if self.frames:
                    frame = self.frames.pop()
                    # TODO: return frame to server
                    break
                self.condition.wait()
            self.condition.release()


def main():
    frames = deque(maxlen=1) # only most recent frame kept
    condition = threading.Condition()
    t1 = Producer(frames, condition, mocap_object) #TODO: Add in mocap object
    t2 = Consumer(frames, condition)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

if __name__ == '__main__':
    main()
