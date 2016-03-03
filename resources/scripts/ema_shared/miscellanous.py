__author__ = 'Kristy'

import random
import importlib

def get_random_color():
    """Generate rgb using a list comprehension """
    r, g, b = [random.random() for i in range(3)]
    return r, g, b, 1


def reload_modules_for_testing(*nss):
    for ns in nss:
        importlib.reload(ns)



class ReeevalIter(object):
    """Give the iterator some lists by entering their variable names as strings.
    You can then iterate over a concatenation of these lists,
    where the sub-lists are re-evaluated at the beginning of the iteration.
    This is used for my application where the application maintains many shorter lists,
    but occasionally I want to iterate all of these, making sure values are current."""
    def __init__(self, *listnames):
        self.names = listnames
        self.outerind, self.innerind = 0, 0

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        # when restarting iteration, reload lists
        if self.innerind == 0 and self.outerind == 0:
            print('about to eval names', self.names)
            #from .blender_shared_objects import name
            self.outerlists = [eval(name) for name in self.names]
            #print(self.outerlists)

        # within original list len
        if self.outerind < len(self.outerlists):
            # something else in innerlist
            if self.innerind < len(self.outerlists[self.outerind]):
                output = self.outerlists[self.outerind][self.innerind]
                self.innerind +=1
                return output
            else:
                #nothing else in innerlist, move to next outerlist, get next item
                self.innerind = 0
                self.outerind += 1
                return self.next()
        # no more outer lists, reset indices
        else:
            self.innerind, self.outerind = 0, 0
            raise StopIteration()
