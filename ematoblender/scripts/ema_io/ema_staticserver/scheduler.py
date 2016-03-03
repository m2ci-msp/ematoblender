from datetime import datetime
import threading
from time import time, sleep
import sys

"""
Module with different timer options. These control how often a callable is called.
"""


# this is adapted code from the original gist
class RepeatTimer(threading.Thread):
    """
    This timer creates a thread. When the time limit has passed, execute the callable.
    It is inspired by:
    This class created on 2011-02-10
    @author: Bohdan Mushkevych
    @author: Brian Curtin
    http://code.activestate.com/lists/python-ideas/8982/
    """

    def __init__(self, interval, callable, args=None, kwargs=None):
        """
        Initiate the timer, with the interval in seconds, callable function, optional function arguments and kwargs.
        """
        threading.Thread.__init__(self)

        # note: interval_current and interval_new currently the same, only useful if changing interval implemented
        # interval_current shows number of seconds in currently triggered <tick>
        self.interval_current = interval

        # interval_new shows number of seconds for next <tick>
        self.interval_new = interval

        # the function called when the timer expires and its args
        self.callable = callable
        self.args = args
        self.kwargs = kwargs

        # create and start the timer event
        self.event = threading.Event()
        self.event.set()

        # placeholders for the time each repeattimer was activated, the timer object
        self.activation_dt = None
        self.__timer = None

    def run(self):
        """
        Run the timer and execute the callable upon completion, then reset until it is cancelled.
        """
        while self.event.is_set():
            self.activation_dt = datetime.utcnow()
            print('the time at running is ', self.activation_dt)
            self.__timer = threading.Timer(self.interval_new,
                                           self.callable,
                                           self.args,
                                           self.kwargs)
            self.interval_current = self.interval_new
            self.__timer.start()
            self.__timer.join()

    def cancel(self):
        """
        Cancel the timer.
        """
        self.event.clear()
        if self.__timer is not None:
            self.__timer.cancel()

    def trigger(self):
        """
        Perform the callable function with arguments self.args and self.kwargs.
        """
        self.callable(*self.args, **self.kwargs)
        if self.__timer is not None:
            self.__timer.cancel()

    # unused in this application
    def change_interval(self, value):
        """Change the timer interval. Unused in this application."""
        self.interval_new = value


class EfficientRepeatTimer(RepeatTimer):
    """Repeat timer that doesn't waste ms creating stuff outside the timed loop."""
    def run(self):
        self.__timer = threading.Timer(self.interval_new,
                                       self.callable,
                                       self.args,
                                       self.kwargs)
        while self.event.is_set():
            self.__timer.start()  # starts working timer
            self.activation_dt = datetime.utcnow()
            print('the time at running before ', self.activation_dt)

            # while timer is working, next timer is prepared
            self.new_timer = threading.Timer(self.interval_new,
                                             self.callable,
                                             self.args,
                                             self.kwargs)
            self.__timer.join()
            self.__timer = self.new_timer


class BusyWaitingRepeatTimer(RepeatTimer):
    """
    Timer class that performs busy waiting.
    This records the starting time, and continually checks until the next execution time is reached.
    """
    def run(self):
        self.activation_dt = time()
        while self.event.is_set():
            self.next_exec = self.activation_dt + self.interval_new
            streamthread = threading.Thread(group=None, target=self.callable, args=[self.args], kwargs=self.kwargs)
            while time() < self.next_exec:
                sleep(0)  # sleep for the least possible time

            # when the relevant time is reached, launch the thread to send the data
            streamthread.start()
            self.activation_dt = self.next_exec
            print('threader activation time is', self.activation_dt,  file=sys.stderr)