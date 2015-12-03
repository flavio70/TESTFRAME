#!/usr/bin/env python
"""
###############################################################################
# MODULE: equipment.py
#
# AUTHOR: C.Ghelfi
# DATE  : 29/07/2015
#
###############################################################################
"""


class Equipment:
    """
    Generic Equipment descriptor. Implements basic operations
    """
    def __init__(self, label, ID):
        """ label : equipment name used on Report file
            ID    : equipment ID (see T_EQUIPMENT table on K@TE DB)
        """
        self.__status = 0
        self.__label  = label
        self.__id     = ID
        self.__type   = "unknown"


    
    def get_id(self):
       """ Get Equipment Id
       """
       return str(self.__id)
        
    
    def set_label(self, the_label):
        """ Initialize equipment name
            the_label : equipment name
        """
        self.__label = the_label


    def get_label(self):
        """ Get Equipment Name
        """
        return self.__label


    def set_type(self, the_type):
        """ Initialize equipment type
            the_type = equipment type
        """
        self.__type = the_type


    def get_type(self):
        """ Get Equipment type
        """
        return self.__type


    def lock(self):
        """ Reserve current equipment
        """
        if self.__status == 0:
            self.__status = 1
        else:
            print("Equipment ", self.__id, " already locked.")


    def unlock(self):
        """ Unreserve current equipment
        """
        if self.__status == 1:
            self.__status = 0
        else:
            print("Equipment ", self.__id, " already unlocked.")


    def get_status(self):
        """ Get reserved status of equipment
        """
        return self.__status


    def debug(self):
        """ Debug information
        """
        print("ID     : ", self.__id)
        print("label  : ", self.__label)
        print("status : ", self.__status)
        print("type   : ", self.__type)



if __name__ == '__main__':
    print("DEBUG Equipment")
    nodeA = Equipment("nodeA", 1)
    nodeB = Equipment("nodeB", 5)
    print("----")
    print("Status: " + str(nodeA.get_status()))
    nodeA.lock()
    print("Status: " + str(nodeA.get_status()))
    nodeA.unlock()
    print("Status: " + str(nodeA.get_status()))
    print("----")
    print("Status: " + str(nodeB.get_status()))
    nodeB.lock()
    print("Status: " + str(nodeB.get_status()))
    nodeB.unlock()
    print("Status: " + str(nodeB.get_status()))
