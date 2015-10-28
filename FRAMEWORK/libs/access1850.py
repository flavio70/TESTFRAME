#!/usr/bin/env python
"""
###############################################################################
# MODULE: access1850.py
#
# AUTHOR: C.Ghelfi
# DATE  : 29/07/2015
#
###############################################################################
"""

import paramiko
import telnetlib



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
            self.__expect(self.__klConnect, 2)    # da togliere ?
        except EOFError as eee:
            print(str(eee))


    def send_cmd_simple(self, cmd):
        """
        Execute the specified command on serial interface
        cmd : a UNIX command
        """
        try:
            self.__write("\n")
            retry = 1
            while retry == 1:
                res = self.__expect(self.__klLogin, 10)
                if   res[0] == 0:
                    self.__write("root")
                elif res[0] == 1:
                    self.__write("root")
                elif res[0] == 2:
                    self.__write("root")
                elif res[0] == 3:
                    self.__write("alcatel")
                elif res[0] == 4:
                    retry = 0
        except (EOFError, OSError) as eee:
            print("Error in serial connecting - " + str(eee))
            return False

        try:
            self.__write(cmd)
        except OSError as eee:
            print("Error sending command - " + str(eee))
            return False


    #pylint: disable=too-many-branches
    def send_cmd_and_check(self, cmd, check_ok, check_ko=None):
        """
        Execute the specified command on serial interface
        Return True if the the specified string will be detected
        cmd      : a UNIX command
        check_ok : positive check string
        check_ko : negative check string (optional)
        """
        try:
            self.__write("\n")
            retry = 1
            while retry == 1:
                res = self.__expect(self.__klLogin, 10)
                if   res[0] == 0:
                    self.__write("root")
                elif res[0] == 1:
                    self.__write("root")
                elif res[0] == 2:
                    self.__write("root")
                elif res[0] == 3:
                    self.__write("alcatel")
                elif res[0] == 4:
                    retry = 0
        except (EOFError, OSError) as eee:
            print("Error in serial connecting - " + str(eee))
            return False

        try:
            self.__write(cmd)
        except OSError as eee:
            print("Error sending command - " + str(eee))
            return False

        if check_ko is None:
            key_list = [b"root@.*#",str.encode(check_ok)]
            retry = 1
            while retry == 1:
                res = self.__expect(key_list, 10)
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
                res = self.__expect(key_list, 10)
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
    #pylint: enable=too-many-branches



    def __expect(self, key_list, timeout=__DEFAULT_TIMEOUT):
        """ Wait on stream until an element of key_list will be detected
        """
        self.res  = self.__tn.expect(key_list, timeout=timeout)
        return self.res


    def __write(self, msg):
        """ Send a string on connection
        """
        if msg.find("\n") == -1:
            msg = msg + "\n"

        return self.__tn.write(str.encode(msg))




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
        """ TODO
        """
        self.__sh.close()
        self.__sh = None


    def send_cmd_simple(self, cmd):
        """ TODO
        """
        done = False

        while not done:
            try:
                self.__sh.exec_command(cmd)
                done = True
            except paramiko.SSHException as eee:
                msg = "SSH1850: error connectind '{:s}' ({:s}). Retrying...".format(self.__ip, str(eee))
                print(msg)
                self.__setup_ssh()

        return True


    def send_cmd_and_check(self, cmd, check_ok):
        """ TODO
        """
        done = False

        while not done:
            try:
                stdin,stdout,stderr = self.__sh.exec_command(cmd)
                done = True
            except paramiko.SSHException as eee:
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
            stderr.close()

        return found


    def send_cmd_and_capture(self, cmd):
        """ TODO
        """
        done = False

        while not done:
            try:
                print("provo ad eseguire [" + cmd + "]")
                stdin,stdout,stderr = self.__sh.exec_command(cmd)
                print("eseguito [" + cmd + "]")
                done = True
            except paramiko.SSHException as eee:
                msg = "SSH1850: error connectind '{:s}' ({:s}). Retrying...".format(self.__ip, str(eee))
                print(msg)
                self.__setup_ssh()

        res = str(stdout.read())[2:-1]

        stdin.close()
        stderr.close()

        return res.replace('\\n','\n')


    def telnet_tunnel(self, dest_ip, port=23):
        """ TODO
        """
        if not self.__sh.get_transport():
            try:
                self.__sh.connect(self.__ip, username='root', password='alcatel', timeout=10)
            except (paramiko.BadHostKeyException,
                    paramiko.AuthenticationException,
                    paramiko.SSHException) as eee:
                print("SSH1850: error connecting '" + self.__ip + "' (" + str(eee) +")")
                self.__sh.close()
                self.__sh = None
                return

        cmd = "telnet {:s} {:d}".format(dest_ip, port)
        print("setup tunnel for " + cmd)

        self.__send_string(cmd,       'login: ')
        self.__send_string('root',    'Password: ')
        self.__send_string('alcatel', ':~# ')


    def send_bm_command(self, dest_ip, cmd):
        """ TODO
        """
        if not self.__sh.get_transport():
            try:
                self.__sh.connect(self.__ip, username='root', password='alcatel', timeout=10)
            except (paramiko.BadHostKeyException,
                    paramiko.AuthenticationException,
                    paramiko.SSHException) as eee:
                print("SSH1850: error connectind '" + self.__ip + "' (" + str(eee) +")")
                self.__sh.close()
                self.__sh = None
                return

        telnet_cmd = "telnet {:s} 4000".format(dest_ip)

        self.__send_string(telnet_cmd, 'SLC> ')

        cmd = "bm : {:s}".format(cmd)
        print("Sending BM command '" + cmd + "'")

        self.__send_string(cmd, 'SLC> ')


    def __send_string(self, string_to_send, string_to_expect):
        """ INTERNAL USAGE
        """
        chan = self.__sh.invoke_shell()

        chan.send(string_to_send + '\n\r')

        buff = ''
        while not buff.endswith(string_to_expect):
            resp_b = chan.recv(9999)
            resp_a = str(resp_b)
            resp_a = resp_a[2:-1]
            buff += resp_a

        print("@@@@" + buff + "@@@@")


    def __setup_ssh(self):
        """ INTERNAL USAGE
        """
        print("calling __setup_ssh")

        self.__sh = paramiko.SSHClient()

        self.__sh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.__sh.connect(self.__ip, username='root', password='alcatel', timeout=10)
        except (paramiko.BadHostKeyException,
                paramiko.AuthenticationException,
                paramiko.SSHException) as eee:
            print("SSH1850: init error for '" + self.__ip + "' - connect - (" + str(eee) +")")
            self.__sh.close()
            self.__sh = None



if __name__ == "__main__":
    #import facility1850

    print("DEBUG")
    #ser = SER1850(("151.98.176.6",5001))
    #s = facility1850.IP("135.221.125.125")
    #ser = SER1850( (s.get_val(), 2013) )

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
