#!/usr/bin/env python
"""
###############################################################################
# MODULE: kexception.py
#
# AUTHOR: C.Ghelfi
# DATE  : 9/12/2015
#
###############################################################################
"""


class KException(Exception):
    """
    Kate Exception base class
    """
    def __init__(self, message):
        """ message : User defined message
        """
        self.__msg = message

    def __str__(self):
        return repr(self.__msg)



class KUserException(KException):
    """
    Kate Exception for User application code
    """
    def __init__(self, message):
        """ message : User defined message
        """
        self.__msg = message

    def __str__(self):
        return repr(self.__msg)



if __name__ == '__main__':
    try:
        for i in range(10):
            print(i)
            if i == 3:
                raise KUserException("ERRORE UTENTE")
            if i == 4:
                raise KException("ERRORE GENERICO")
    except KUserException as eee:
        print("USER - {}".format(eee))
    except KException as eee:
        print("STD - {}".format(eee))
