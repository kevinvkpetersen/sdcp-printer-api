'''Constants used in the project'''

from enum import Enum


class SDCPCommand(Enum):
    '''Values for the Cmd field.'''
    STATUS = 0


class SDCPFrom(Enum):
    '''Values for the From field.'''
    PC = 0
