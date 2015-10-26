#!/usr/bin/env python

import paramiko
import telnetlib
import facility1850



class SER1850:
    """
    Describe a Telnet interface to 1850TSS320 console
    """
    __DEFAULT_TIMEOUT = 120
    __klConnect = [ b'Escape character is' ]
    __klLogin   = [ b"FLC320-1 login:",
                    b"P1013FLC-1 login:",
                    b"FLC160-1 login:",
                    b"Password:",
                    b"root.*#" ]
    __klPrompt  = [ b"root.*#" ]


    def __init__(self, IPandPORT):
        """
        IPandPORT : tuple of serial interface IP address and port
        """
        self.__ip   = IPandPORT[0]
        self.__port = IPandPORT[1]
        self.__tn   = None

        try:
            self.__tn = telnetlib.Telnet()
            self.__tn.open(self.__ip, self.__port)
            self.EXPECT(self.__klConnect, 2)    # da togliere ?
        except Exception as eee:
            print(str(eee))


    def send_cmd_simple(self, cmd):
        """
        Execute the specified command on serial interface
        cmd : a UNIX command
        """
        try:
            self.WRITE("\n")
            retry = 1
            while retry == 1:
                res = self.EXPECT(self.__klLogin, 10)
                if   res[0] == 0:
                    self.WRITE("root\n")
                elif res[0] == 1:
                    self.WRITE("root\n")
                elif res[0] == 2:
                    self.WRITE("root\n")
                elif res[0] == 3:
                    self.WRITE("alcatel\n")
                elif res[0] == 4:
                    retry = 0
        except Exception as eee:
            print("Error in serial connecting - " + str(eee))
            return False

        the_command = cmd + "\n"

        try:
            self.WRITE(the_command)
        except Exception as eee:
            print("Error sending command - " + str(eee))
            return False


    def send_cmd_and_check(self, cmd, check_ok, check_ko=None):
        """
        Execute the specified command on serial interface
        Return True if the the specified string will be detected
        cmd      : a UNIX command
        check_ok : positive check string
        check_ko : negative check string (optional)
        """
        try:
            self.WRITE("\n")
            retry = 1
            while retry == 1:
                res = self.EXPECT(self.__klLogin, 10)
                if   res[0] == 0:
                    self.WRITE("root\n")
                elif res[0] == 1:
                    self.WRITE("root\n")
                elif res[0] == 2:
                    self.WRITE("root\n")
                elif res[0] == 3:
                    self.WRITE("alcatel\n")
                elif res[0] == 4:
                    retry = 0
        except Exception as eee:
            print("Error in serial connecting - " + str(eee))
            return False

        the_command = cmd + "\n"

        try:
            self.WRITE(the_command)
        except Exception as eee:
            print("Error sending command - " + str(eee))
            return False

        if check_ko is None:
            key_list = [b"root@.*#",str.encode(check_ok)]
            retry = 1
            while retry == 1:
                res = self.EXPECT(key_list, 10)
                if   res[0] == 0:
                    is_detected = False
                elif res[0] == 1:
                    retry = 0
                    is_detected = True
                else:
                    print("TIMEOUT DETECTED")
        else:
            key_list = [b"root@.*#", str.encode(check_ok), str.encode(check_ko)]
            retry = 1
            while retry == 1:
                res = self.EXPECT(key_list, 10)
                if   res[0] == 0:
                    is_detected = False
                elif res[0] == 1:
                    retry = 0
                    is_detected = True
                elif res[0] == 2:
                    retry = 0
                    is_detected = False
                else:
                    print("TIMEOUT DETECTED")

        return is_detected



    def EXPECT(self, key_list, timeout=__DEFAULT_TIMEOUT):
        """ Wait on stream until an element of key_list will be detected
        """
        self.res  = self.__tn.expect(key_list, timeout=timeout)
        return self.res


    def WRITE(self, msg):
        """ Send a string on connection
        """
        return self.__tn.write(str.encode(msg))


    def debug(self):
        print("debug")



class SSH1850():
    """
    Describe a SSH interface to 1850TSS320
    """

    def __init__(self, IP):
        """
        IP : IP address
        """
        self.__ip   = IP
        self.__sh   = None

        self.__setup_ssh()


    def close_ssh(self):
        try:
            self.__sh.close()
            self.__sh = None
        except Exception as eee:
            print("SSH1850: error in close_ssh() (" + str(eee) + ")")


    def send_cmd_simple(self, cmd):
        done = False

        while not done:
            try:
                stdin,stdout,stderr = self.__sh.exec_command(cmd)
                done = True
            except Exception as eee:
                msg = "SSH1850: error connectind '{:s}' ({:s}). Retrying...".format(self.__ip, str(eee))
                print(msg)
                self.__setup_ssh()

        stdin.close()

        return True


    def send_cmd_and_check(self, cmd, check_ok):
        done = False

        while not done:
            try:
                stdin,stdout,stderr = self.__sh.exec_command(cmd)
                done = True
            except Exception as eee:
                msg = "SSH1850: error connectind '{:s}' ({:s}). Retrying...".format(self.__ip, str(eee))
                print(msg)
                self.__setup_ssh()

        if not check_ok:
            found = True
        else:
            found = False
            for line in stdout.read().splitlines():
                res = str(line)[2:-1]
                if res.find(check_ok) != -1:
                    found = True

            stdin.close()

        return found


    def send_cmd_and_capture(self, cmd):
        done = False

        while not done:
            try:
                print("provo ad eseguire [" + cmd + "]")
                stdin,stdout,stderr = self.__sh.exec_command(cmd)
                print("eseguito [" + cmd + "]")
                done = True
            except Exception as eee:
                msg = "SSH1850: error connectind '{:s}' ({:s}). Retrying...".format(self.__ip, str(eee))
                print(msg)
                self.__setup_ssh()

        res = str(stdout.read())[2:-1]

        stdin.close()

        return res.replace('\\n','\n')


    def telnet_tunnel(self, dest_ip, port=23):
        if not self.__sh.get_transport():
            try:
                self.__sh.connect(self.__ip, username='root', password='alcatel', timeout=10)
            except Exception as eee:
                print("SSH1850: error connecting '" + self.__ip + "' (" + str(eee) +")")
                self.__sh.close()
                self.__sh = None
                return

        chan = self.__sh.invoke_shell()

        cmd = "telnet {:s} {:d}".format(dest_ip, port)
        print("setup tunnel for " + cmd)

        self.__send_string(chan, cmd,            'login: ')
        self.__send_string(chan, 'root',         'Password: ')
        self.__send_string(chan, 'alcatel',      ':~# ')
        #self.__send_string(chan, 'reboot',  ':~# ')
        #self.__send_string(chan, 'uptime',       ':~# ')


    def send_bm_command(self, dest_ip, cmd):
        if not self.__sh.get_transport():
            try:
                self.__sh.connect(self.__ip, username='root', password='alcatel', timeout=10)
            except Exception as eee:
                print("SSH1850: error connectind '" + self.__ip + "' (" + str(eee) +")")
                self.__sh.close()
                self.__sh = None
                return

        chan = self.__sh.invoke_shell()

        telnet_cmd = "telnet {:s} 4000".format(dest_ip)

        self.__send_string(chan, telnet_cmd,  'SLC> ')

        cmd = "bm : {:s}".format(cmd)
        print("Sending BM command '" + cmd + "'")

        self.__send_string(chan, cmd,        'SLC> ')


    def __send_string(self, chan, string_to_send, string_to_expect):
        chan.send(string_to_send + '\n\r')

        buff = ''
        while not buff.endswith(string_to_expect):
            resp_b = chan.recv(9999)
            resp_a = str(resp_b)
            resp_a = resp_a[2:-1]
            buff += resp_a

        print("@@@@" + buff + "@@@@")


    def __setup_ssh(self):
        print("calling __setup_ssh")
        try:
            self.__sh = paramiko.SSHClient()
        except Exception as eee:
            print("SSH1850: init error for '" + self.__ip + "' - setup -(" + str(eee) +")")
            self.__sh = None

        try:
            self.__sh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        except Exception as eee:
            print("SSH1850: init error for '" + self.__ip + "' - key - (" + str(eee) +")")
            self.__sh.close()
            self.__sh = None

        try:
            self.__sh.connect(self.__ip, username='root', password='alcatel', timeout=10)
        except Exception as eee:
            print("SSH1850: init error for '" + self.__ip + "' - connect - (" + str(eee) +")")
            self.__sh.close()
            self.__sh = None



if __name__ == "__main__":
    print("DEBUG")
    ser = SER1850(("151.98.176.6",5001))
    #s = facility1850.IP("135.221.125.125")
    #ser = SER1850( (s.getVal(), 2013) )

    #print("OPENING SSH")
    #net = SSH1850('135.221.125.80')
    #print(net.send_cmd_and_capture("date"))

    #print("DISABILITO NET")
    #ser.send_cmd_simple("ifconfig eth1 down")
    #time.sleep(1)
    #ser.send_cmd_simple("ifconfig eth1 hw ether 08:00:87:DD:7D:50")
    #time.sleep(1)
    #ser.send_cmd_simple("ifconfig eth1 135.221.125.80 netmask 255.255.255.128")
    #time.sleep(3)
    #ser.send_cmd_simple("ifconfig eth1 up")
    #time.sleep(5)
    #ser.send_cmd_simple("route add default gw 135.221.125.1")
    #time.sleep(1)


    #print("PROVO DI NUOVO VIA SSH")
    #print(net.send_cmd_and_capture("date"))

    print("FINE")
