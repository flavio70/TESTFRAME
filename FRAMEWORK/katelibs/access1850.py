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
import os
import inspect

#myself = lambda: "__name__" + inspect.stack()[1][3]


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
            self.__tn = telnetlib.Telnet(self.__ip, self.__port)
            self.ser_expect(self.__klConnect, 2)    # da togliere ?
        except Exception as eee:
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
                res = self.ser_expect(self.__klLogin, 10)
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
        except Exception as eee:
            print("Error in serial connecting - " + str(eee))
            return False

        try:
            self.__write(cmd)
        except Exception as eee:
            print("Error sending command - " + str(eee))
            return False


    def send_cmd_and_capture(self, cmd):
        """
        Send a specified command to equipment on serial interface; the stdout result is returned to caller
        cmd : a UNIX command
        """
        try:
            self.__write("\n")
            retry = 1
            while retry == 1:
                res = self.ser_expect(self.__klLogin, 10)
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
        except Exception as eee:
            print("Error in serial connecting - " + str(eee))
            return ""

        try:
            self.__read_all()
            self.__write(cmd)
        except Exception as eee:
            print("Error sending command - " + str(eee))
            return ""

        captured_text = ""
        discard_text = str.encode("{:s}\r\n".format(cmd))

        while True:
            res = self.ser_expect([discard_text, b"\r\n", b"root@.*#"])

            if res[0] == 0:
                # Command string detected - discard from output
                continue
            elif res[0] == 1:
                # Output text to capture
                tmp_text = str(res[2], 'utf-8')
                captured_text = captured_text + tmp_text
            elif res[0] == 2:
                # Prompt detected - closing capture
                break

        return captured_text


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
                res = self.ser_expect(self.__klLogin, 10)
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
        except Exception as eee:
            print("Error in serial connecting - " + str(eee))
            return False

        try:
            self.__write(cmd)
        except Exception as eee:
            print("Error sending command - " + str(eee))
            return False

        if check_ko is None:
            key_list = [b"root@.*#",str.encode(check_ok)]
            retry = 1
            while retry == 1:
                res = self.ser_expect(key_list, 10)
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
                res = self.ser_expect(key_list, 10)
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



    def ser_expect(self, key_list, timeout=__DEFAULT_TIMEOUT):
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


    def __read_all(self):
        """ INTERNAL USAGE
        """
        while str(self.__tn.read_very_eager().strip(), 'utf-8') != "":
            pass
        return True



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


    def close_ssh(self):
        """ TODO
        """
        self.__sh.close()
        self.__sh = None


    def send_cmd_simple(self, cmd):
        """ Send a specified command to equipment using SSH connection.
            If connection is down, a reconnection is done
            cmd : a UNIX command
        """
        if not self.__is_reachable_by_ip():
            self.__setup_ssh()
            if self.__sh is None:
                print("SSH1850::send_cmd_simple - cannot connect")
                return False

        done = False

        while not done:
            try:
                self.__sh.exec_command(cmd)
                done = True
            except Exception as eee:
                print("SSH1850: error connectind '{:s}' ({:s}). Retrying...".format(self.__ip, str(eee)))
                self.__setup_ssh()

        return True


    def send_cmd_and_check(self, cmd, check_ok):
        """ Send a specified command to equipment using SSH connection.
            If connection is down, a reconnection is done
            cmd      : a UNIX command
            check_ok : (optional) string to check on command stdout response
        """
        if not self.__is_reachable_by_ip():
            self.__setup_ssh()
            if self.__sh is None:
                print("SSH1850::send_cmd_and_check - cannot connect")
                return False

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
            stderr.close()

        return found


    def send_cmd_and_capture(self, cmd):
        """ Send a specified command to equipment using SSH connection; the stdout result is returned to caller
            If connection is down, a reconnection is done
            cmd : a UNIX command
        """
        print("SSH1850::send_cmd_and_capture in")

        if not self.__is_reachable_by_ip():
            self.__setup_ssh()
            if self.__sh is None:
                print("SSH1850::send_cmd_and_capture - cannot connect")
                return False

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
        stderr.close()

        return res.replace('\\n','\n')


    def __setup_ssh(self):
        """ INTERNAL USAGE
        """
        print("calling __setup_ssh")

        self.__sh = paramiko.SSHClient()

        self.__sh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.__sh.connect(self.__ip, username='root', password='alcatel', timeout=10)
        except Exception as eee:
            print("SSH1850: init error for '" + self.__ip + "' - connect - (" + str(eee) +")")
            self.__sh.close()
            self.__sh = None
        print("...ssh setup done")


    def __is_reachable_by_ip(self):
        """ INTERNAL USAGE
        """
        # Verify IP connection from network to this equipment
        cmd = "ping -c 2 {:s} >/dev/null".format(self.__ip)
        if os.system(cmd) == 0:
            return True
        return False



if __name__ == "__main__":
    #import facility1850

    print("DEBUG")
    #ser = SER1850(("151.98.176.6",5001))
    #s = facility1850.IP("135.221.125.125")
    #ser = SER1850( (s.get_val(), 2013) )

    #print("OPENING SSH")
    #net = SSH1850('135.221.125.79')
    #print(net.send_cmd_and_capture("date"))

    #print("DISABILITO NET")
    #ser.send_cmd_simple("ifconfig eth1 down")
    #time.sleep(1)
    #ser.send_cmd_simple("ifconfig eth1 hw ether 08:00:87:DD:7D:4f")
    #time.sleep(1)
    #ser.send_cmd_simple("ifconfig eth1 135.221.125.79 netmask 255.255.255.128")
    #time.sleep(3)
    #ser.send_cmd_simple("ifconfig eth1 up")
    #time.sleep(5)
    #ser.send_cmd_simple("route add default gw 135.221.125.1")
    #time.sleep(1)


    #print("PROVO DI NUOVO VIA SSH")
    #print(net.send_cmd_and_capture("date"))

    print("FINE")
