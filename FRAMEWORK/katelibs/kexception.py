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
    Kate Exception base class - Please use a derived Exception Class
    """
    def __init__(self, message):
        """ message : exception message
        """
        super().__init__()
        self.__msg = message
        self.__lvl = "KATE_BASE"

    def __str__(self):
        return repr("{}[{}]".format(self.get_level(), self.get_message()))

    def get_message(self):
        """ Get exception message
        """
        return self.__msg

    def get_level(self):
        """ Get exception level
        """
        return self.__lvl

    def set_level(self, level):
        """ Set exception level
        """
        self.__lvl = level



class KUserException(KException):
    """
    Kate Exception for User application code
    """
    def __init__(self, message):
        """ message : exception message
        """
        super().__init__(message)
        self.set_level("KATE_USER")



class KFrameException(KException):
    """
    Kate Exception for Environmental issues
    """
    def __init__(self, message):
        """ message : exception message
        """
        super().__init__(message)
        self.set_level("KATE_FRAME")



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
    except Exception as eee:
        print("PYTHON - {}".format(eee))
