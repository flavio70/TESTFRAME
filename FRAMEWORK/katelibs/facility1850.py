#!/usr/bin/env python
"""
###############################################################################
# MODULE: facility1850.py
#
# AUTHOR: C.Ghelfi
# DATE  : 29/07/2015
#
###############################################################################
"""


class IP:
    """
    IP type for K@TE
    """

    def __init__(self, the_ip=None, protocol=None):
        """ Constructor
            the_ip   : value (string)
            protocol : "v4" or "v6" (default "v4")
        """
        self.__ip = the_ip

        if the_ip is None:
            self.__protocol = None
        else:
            if protocol is None:
                self.__protocol = "v4"
            else:
                self.__protocol = protocol


    def get_val(self):
        """ Return IP value (string) """
        return self.__ip

    def set_val(self, the_ip):
        """ Set IP value (string) """
        self.__ip = the_ip

    def set_protocol(self, protocol):
        """ Set protocol type
            protocol : "v4" or "v6"
        """
        self.__protocol = protocol

    def get_protocol(self):
        """ Get protocol type (string, "v4" or "v6")
        """
        return self.__protocol

    def evaluate_mac(self):
        """ Get unique MAC Address using IP value
        """
        if self.__ip:
            ip_num = self.__ip.split('.')
            msg = "08:00:{:02X}:{:02X}:{:02X}:{:02X}".format(int(ip_num[0]),
                                                             int(ip_num[1]),
                                                             int(ip_num[2]),
                                                             int(ip_num[3]))
            return msg
        else:
            return str(None)

    def __debug(self):
        """ INTERNAL USAGE
        """
        print("DEBUG IP:")
        print(self.__ip)
        print("END IP:")


class NetIF:
    """
    Describe a IP connection
    """

    #pylint: disable=too-many-arguments
    def __init__(self, ip=None, nm=None, gw=None, mac=None, dev=None):
        """ Constructor
            ip  : ip value (IP type)
            nm  : ip value (IP type)
            gw  : gw value (IP type)
            mac : MAC address (string, as "00:00:00:00:00:00" for ipV4)
            dev : ethernet device ("eth1", "q", "dbg", ...)
        """
        if not (ip is None  or  nm is None  or  gw is None  or  mac is None  or  dev is None):
            self.__protocol        = ip.get_protocol()
            self.__net_info        = { }
            self.__net_info['IP']  = ip
            self.__net_info['NM']  = nm
            self.__net_info['GW']  = gw
            self.__net_info['DEV'] = dev
            self.set_mac(mac)
        else:
            self.__protocol        = None
            self.__net_info        = { }
            self.__net_info['IP']  = IP()
            self.__net_info['NM']  = IP()
            self.__net_info['GW']  = IP()
            self.__net_info['MAC'] = None
            self.__net_info['DEV'] = None

            if not (ip is None  and  nm is None  and  gw is None  and  mac is None  and  dev is None):
                print("ERROR: some parameters are None")
    #pylint: enable=too-many-arguments

    def set_ip(self, value):
        """ Set IP value (IP class type)"""
        self.__net_info['IP']  = value

    def set_nm(self, value):
        """ Set Netmask value (IP class type)"""
        self.__net_info['NM']  = value

    def set_gw(self, value):
        """ Set Gateway value (IP class type)"""
        self.__net_info['GW']  = value

    def set_mac(self, value):
        """ Set MAC Address (string, as "00:00:00:00:00:00" for ipV4) """
        self.__net_info['MAC'] = value.upper()

    def set_dev(self, value):
        """ Set ethernet device adapter """
        self.__net_info['DEV'] = value

    def get_ip(self):
        """ Get IP (IP class type)"""
        return self.__net_info['IP']

    def get_ip_str(self):
        """ Get IP (string)"""
        return self.__net_info['IP'].get_val()

    def get_nm(self):
        """ Get Netmask (IP class type)"""
        return self.__net_info['NM']

    def get_nm_str(self):
        """ Get Netmask (sring)"""
        return self.__net_info['NM'].get_val()

    def get_gw(self):
        """ Get Gateway (IP class type)"""
        return self.__net_info['GW']

    def get_gw_str(self):
        """ Get Gateway (string)"""
        return self.__net_info['GW'].get_val()

    def get_mac(self):
        """ Get MAC Address (string) """
        return self.__net_info['MAC']

    def get_dev(self):
        """ Get ethernet device adapter"""
        return self.__net_info['DEV']

    def __debug(self):
        """ INTERNAL USAGE
        """
        print("IP : " + self.get_ip())
        print("NM : " + self.get_nm())
        print("GW : " + self.get_gw())
        print("MAC: " + self.get_mac())



class SerIF:
    """
    Describe a Serial Interface to 1850TSS320 Equipment
    """

    def __init__(self):
        """ Empty Constructor
        """
        self.__ser_info = {}

    def set_serial_to_slot(self, slot, the_ip, the_port):
        """ Constructor
            slot     : equipment's slot number
            the_ip   : IP address of serial server
            the_port : port number on serial server
        """
        self.__ser_info[slot] = { 'IP' : the_ip, 'port' : the_port }

    def get_val(self, slot):
        """ Return the couple (IP, PORT) for specified slot number
        """
        return ( (self.__ser_info[slot]['IP']).get_val(), self.__ser_info[slot]['port'] )

    def __debug(self):
        """ INTERNAL USAGE
        """
        print(self.__ser_info)




if __name__ == "__main__":
    print("DEBUG")
    #ip = IP("135.221.125.66")
    #print(ip.get_val())
    #print(ip.evaluate_mac())

    #ip = IP("10.10.10.10")
    #nm = IP("255.255.255.0")
    #gw = IP("10.10.10.1")

    #elem = NetIF(ip, nm, gw, "00:aa:bb:cc:11:22")
    #print(elem.__debug())

    serIP = IP("192.168.1.25")
    mySer = SerIF()
    mySer.set_serial_to_slot( 1, serIP, 1001)
    serIP = IP("192.168.80.12")
    mySer.set_serial_to_slot(10, serIP, 1012)
    print("---")
    print("seriale  1: " + str(mySer.get_val(1)))
    print("---")
    print("seriale 10: " + str(mySer.get_val(10)))
    print("---")
    #print(mySer.__debug())
