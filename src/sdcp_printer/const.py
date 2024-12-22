'''Constants used in the project'''

from enum import Enum

BROADCAST_PORT = 3000
PRINTER_PORT = 3030

MESSAGE_ENCODING = 'utf-8'


class SDCPCommand(Enum):
    '''Values for the Cmd field.'''
    STATUS = 0,

class SDCPFrom(Enum):
    '''Values for the From field.'''
    PC = 0,
