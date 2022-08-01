#!/usr/bin/env python

class IntWithUnits(int):

    def __new__(self, value, units=''):
        return int.__new__(self, value)

    def __init__(self, value, units=''):
        int.__init__(value)
        self.units = units

    def __str__(self):
        return f'{self}{self.units}'

