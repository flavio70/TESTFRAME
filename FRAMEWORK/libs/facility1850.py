#!/usr/bin/env python


class IP:
    """
    IP type for K@TE
    """

    def __init__(self):
        """ Empty Constructor
        """
        self.__ip       = None
        self.__protocol = None

    def __init__(self, ip, protocol="v4"):
        """ Constructor
            ip       : value (string)
            protocol : "v4" or "v6" (default "v4")
        """
        self.__ip       = ip
        self.__protocol = protocol

    def get_val(self):
        """ Return IP value (string) """
        return self.__ip

    def set_val(self, ip):
        """ Set IP value (string) """
        self.__ip = ip

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
            print(self.__ip)
            ip_num = self.__ip.split('.')
            print(ip_num)
            msg = "08:00:{:02X}:{:02X}:{:02X}:{:02X}".format(int(ip_num[0]),
                                                             int(ip_num[1]),
                                                             int(ip_num[2]),
                                                             int(ip_num[3]))
            return msg
        else:
            return str(None)

    def __debug(self):
        print("DEBUG IP:")
        print(self.__ip)
        print("END IP:")


class NetIF:
    """
    Describe a IP connection
    """

    def __init__(self):
        """ Empty Constructor
        """
        self.__protocol        = None
        self.__net_info        = { }
        self.__net_info['IP']  = IP()
        self.__net_info['NM']  = IP()
        self.__net_info['GW']  = IP()
        self.__net_info['MAC'] = None
        self.__net_info['DEV'] = None

    def __init__(self, ip, nm, gw, mac, dev):
        """ Constructor
            ip  : ip value (IP type)
            nm  : ip value (IP type)
            gw  : gw value (IP type)
            mac : MAC address (string, as "00:00:00:00:00:00" for ipV4)
            dev : ethernet device ("eth1", "q", "dbg", ...)
        """
        self.__protocol        = ip.get_protocol()
        self.__net_info        = { }
        self.__net_info['IP']  = ip
        self.__net_info['NM']  = nm
        self.__net_info['GW']  = gw
        self.__net_info['DEV'] = dev
        self.set_mac(mac)

    def set_ip(self, ip):
        """ Set IP value (IP class type)"""
        self.__net_info['IP']  = ip

    def set_nm(self, nm):
        """ Set Netmask value (IP class type)"""
        self.__net_info['NM']  = nm

    def set_gw(self, gw):
        """ Set Gateway value (IP class type)"""
        self.__net_info['GW']  = gw

    def set_mac(self, mac):
        """ Set MAC Address (string, as "00:00:00:00:00:00" for ipV4) """
        self.__net_info['MAC'] = mac.upper()

    def set_dev(self, dev):
        """ Set ethernet device adapter """
        self.__net_info['DEV'] = dev

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

    def set_serial_to_slot(self, slot, ip, port):
        """ Constructor
            slot : equipment's slot number
            ip   : IP address of serial server
            port : port number on serial server
        """
        self.__ser_info[slot] = { 'IP' : ip, 'port' : port }

    def get_val(self, slot):
        """ Return the couple (IP, PORT) for specified slot number
        """
        return ( (self.__ser_info[slot]['IP']).get_val(), self.__ser_info[slot]['port'] )

    def __debug(self):
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
