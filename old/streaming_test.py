import threading

from old.repeatedtimer import RepeatTimer


class Streamer(threading.Thread):
    """
    Streams data from a file, one line at a time
    """
    def __init__(self, condition):
        """
        Constructor.

        @param integers list of integers
        @param condition condition synchronization object
        """
        threading.Thread.__init__(self)
        # self.integers = integers
        self.condition = condition

    def run(self):
        """
        Thread run method. Consumes integers from list
        """
        while True:
            self.condition.acquire()
            print( 'condition acquired by %s' % self.name)
            while True:
                print("Streamer gives data")
                # if self.integers:
                #     integer = self.integers.pop()
                #     print( '%d popped from list by %s' % (integer, self.name))
                break
                # print('condition wait by %s' % self.name)
                # self.condition.wait()
            print('condition released by %s' % self.name)
            self.condition.release()

def acquire_release_condition(some_condition):
    some_condition.acquire()
    some_condition.notify()
    some_condition.release()


def main():
    condition = threading.Condition()
    t1 = RepeatTimer(1, acquire_release_condition, condition)
    t2 = Streamer(condition)
    t1.start()
    t2.start()
    # t1.join()
    # t2.join()