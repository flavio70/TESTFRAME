#!/usr/bin/env python
"""
###############################################################################
# MODULE: plugin_bm.py
#
# AUTHOR: C.Ghelfi
# DATE  : 24/11/2015
#
###############################################################################
"""

import time
import paramiko

from katelibs.ktracer    import KTracer


class TunnelSSH():
    """
    Generic SSH Tunnel from FLC to a Card
    """

    def __init__(self, flc_ip, card_slot, card_port, ktrc=None):
        """
        flc_ip    : IP address
        card_slot : Card slot number
        card_port : Debug port on card
        """
        self.__flc_ip    = flc_ip
        self.__card_ip   = "100.0.1.{:d}".format(card_slot)
        self.__card_port = card_port
        self.__ssh       = None
        self.__chan      = None
        self.__ktrc      = ktrc

        self.__ssh = paramiko.SSHClient()

        self.__ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.__ssh.connect(self.__flc_ip, username='root', password='alcatel', timeout=10)
        except Exception as eee:
            self.__trc_err("TunnelSSH: init error for '{:s}' - connect - ({})".format(self.__flc_ip, eee))
            self.__ssh = None
            return

        self.__chan = self.__ssh.invoke_shell()

        self.__trc_dbg("TunnelSSH for {} initiated".format(self.__card_ip))


    def clean_up(self):
        """ Closing Tunnel
        """
        try:
            self.__ssh.close()
        except Exception as eee:
            self.__trc_err("Error in closing ssh tunnel - {}".format(eee))

        self.__trc_dbg("Tunnel to {} closed.".format(self.__card_ip))


    def send_and_capture_bm_cmd(self, cmd_bm):
        """ Send a BM Command to Card and capture this output
            cmd : a BM command
        """
        self.__setup_tunnel()

        cmd = "bm {:s}".format(cmd_bm)

        self.__trc_dbg("SENDING BM COMMAND")

        res = self.__write(cmd, "SLC> ")
        if res == (False, None):
            return res  # Timeout Detected

        # Message capturing
        msg = res[1].replace(r"\r\n","\n")
        msg = "\n".join(msg.splitlines()[:-1])
        self.__trc_dbg(msg)

        return True, msg


    def __setup_tunnel(self):
        """ TODO
        """
        cmd = "telnet {:s} {:d}".format(self.__card_ip, self.__card_port)

        self.__trc_dbg("SETUP TUNNEL TO SLC")

        res = self.__write(cmd, "Shell for SLC Machine Model data")

        if res == (False, None):
            return res  # Timeout Detected



    def __write(self, string_to_send, string_to_expect):
        """ INTERNAL USAGE
        """
        self.__trc_dbg("to [{}] : send [{}], expect [{}]".format(self.__card_ip,
                                                                 string_to_send,
                                                                 string_to_expect))
        try:
            self.__chan.settimeout(3)
            self.__chan.send(string_to_send + '\n\r')

            while not self.__chan.recv_ready():
                time.sleep(1)
        except Exception as eee:
            self.__trc_err("Error using ssh tunnel for {} - {}".format(self.__flc_ip, eee))
            return False, None

        buff = ''
        while True:
            try:
                resp_b = self.__chan.recv(9999)
            except:
                self.__trc_dbg("TIMEOUT DETECTED")
                return False, None

            resp_a = str(resp_b)
            resp_a = resp_a[2:-1]
            buff += resp_a

            if resp_a.find(string_to_expect) != -1:
                self.__trc_dbg("EXPECT VALUE DETECTED")
                return True, buff


    def __trc_dbg(self, msg, level=None):
        """ INTERNAL USAGE
        """
        if self.__ktrc is not None:
            self.__ktrc.k_tracer_debug(msg, level)


    def __trc_inf(self, msg, level=None):
        """ INTERNAL USAGE
        """
        if self.__ktrc is not None:
            self.__ktrc.k_tracer_info(msg, level)


    def __trc_err(self, msg, level=None):
        """ INTERNAL USAGE
        """
        if self.__ktrc is not None:
            self.__ktrc.k_tracer_error(msg, level)




class Plugin1850BM():
    """
    BM plugin for 1850TSS Equipment
    """

    SLC_BM_PORT = 4000


    def __init__(self, flc_ip, eRef=None, krepo=None, ktrc=None, slc_a=10, slc_b=11):
        """
        Costructor for BM interface
        flc_ip : equipment's IP Address (FLC)
        eRef   : referente to Equipment
        krepo  : reference to KUnit reporting instance
        ktrc   : reference to Kate Tracer
        """
        self.__flc_ip   = flc_ip
        self.__krepo    = krepo
        self.__ktrc     = ktrc
        self.__eqpt_ref = eRef
        self.__slc_a    = slc_a
        self.__slc_b    = slc_b

        self.__tunnel   = {}
        self.__active   = None
        self.__relaxed  = False # False: force check for active SLC

        self.__tunnel[self.__slc_a] = TunnelSSH(self.__flc_ip, self.__slc_a, self.SLC_BM_PORT, ktrc=self.__ktrc)
        self.__tunnel[self.__slc_b] = TunnelSSH(self.__flc_ip, self.__slc_b, self.SLC_BM_PORT, ktrc=self.__ktrc)

        self.__trc_inf("Plugin BM available")


    def clean_up(self):
        """ TODO
        """
        self.__trc_dbg("CLEAN UP")

        if self.__tunnel[self.__slc_b] is not None:
            self.__tunnel[self.__slc_b].clean_up()

        if self.__tunnel[self.__slc_a] is not None:
            self.__tunnel[self.__slc_a].clean_up()

        self.__tunnel[self.__slc_b] = None
        self.__tunnel[self.__slc_a] = None


    def send_command(self, cmd):
        """ Send a generic BM Command
            In case of error, a (False, None) is returned
            Otherwise, a (True, command_output) is returned
            Note: shell command sent via BM doesn't collect output
        """
        if self.__active is None:
            if self.get_active_slc() is None:
                self.__trc_err("BOTH SLC ARE UNAVAILABLE")
                return False, None
        else:
            if not self.__relaxed:
                if self.get_active_slc() is None:
                    self.__trc_err("BOTH SLC ARE UNAVAILABLE")
                    return False, None

        res = self.__tunnel[self.__active].send_and_capture_bm_cmd(cmd)
        return res


    def get_active_slc(self):
        """ Get slot number of Active SLC.
            If both SLC are unavailable, a None is returned
        """
        self.__trc_dbg("\nGET ACTIVE SLC...")

        if self.__active is None:
            slc_list = [self.__slc_a, self.__slc_b]
        else:
            if self.__active == self.__slc_a:
                slc_list = [self.__slc_a, self.__slc_b]
            else:
                slc_list = [self.__slc_b, self.__slc_a]

        for slc in slc_list:
            self.__trc_dbg("\nTRYING TO REACH SLC 100.0.1.{:d}".format(slc))
            res = self.__tunnel[slc].send_and_capture_bm_cmd("matrix")
            if res != (False, None):
                if res[1].find("scSTATUS.local_controller  = KS_OPERATIVE_ACTIVE") != -1:
                    self.__trc_dbg("SLC 100.0.1.{:d} ACTIVE".format(slc))
                    self.__active = slc
                    return slc
                else:
                    self.__trc_dbg("SLC 100.0.1.{:d} AVAILABLE BUT NOT ACTIVE".format(slc))
            else:
                self.__trc_dbg("SLC 100.0.1.{:d} NOT REACHABLE".format(slc))

        self.__trc_dbg("\nBOTH SLC ARE NOT AVAILABLE.\n")
        self.__active = None
        return None


    def read_remote_inventory(self, slot, relaxed=False):
        """ Read Remote Inventory data for a card on required slot
            Return Value: <card_name, signature> or <None,None> in case of error
        """

        card_name = None
        signature = ""

        if relaxed:
            self.__relaxed = True

        res = self.send_command("read ri {:d}".format(slot))

        if relaxed:
            self.__relaxed = False

        if res[0]:
            for row in res[1].splitlines():
                pos = row.find("Card is ")
                if pos != -1:
                    card_name = row[8:].replace(':','').replace(' ','')

                row = row[36:].replace(' ','')
                if row != "":
                    signature = signature + row

        if card_name is None:
            return None, None
        else:
            return card_name, signature


    def read_complete_remote_inventory(self, slot_limit=36):
        """ Read Remote Inventory data for all available cards
            Return Value: a dictionary of tuples as
                { slot : [card_name, signature] }
        """
        result = { }

        for slot in range(slot_limit):
            info = self.read_remote_inventory(slot + 1, relaxed=True)
            if info != (None, None):
                result[slot+1] = info
            # Check for connection: skip if not present
            if self.__active is None:
                self.__trc_err("\nBOTH SLC ARE NOT AVAILABLE.\n")
                return result

        return result


    def slc_reboot(self, slot):
        """ Force a SLC reboot using BM command
        """
        if slot != self.__slc_a  and  slot != self.__slc_b:
            return False

        cmd = ": reboot".format(slot)
        res = self.__tunnel[slot].send_and_capture_bm_cmd(cmd)
        return res


    def __trc_dbg(self, msg, level=None):
        """ INTERNAL USAGE
        """
        if self.__ktrc is not None:
            self.__ktrc.k_tracer_debug(msg, level)


    def __trc_inf(self, msg, level=None):
        """ INTERNAL USAGE
        """
        if self.__ktrc is not None:
            self.__ktrc.k_tracer_info(msg, level)


    def __trc_err(self, msg, level=None):
        """ INTERNAL USAGE
        """
        if self.__ktrc is not None:
            self.__ktrc.k_tracer_error(msg, level)



if __name__ == "__main__":
    print("DEBUG")

    TRACE = KTracer(level="ERROR")

    BM = Plugin1850BM("135.221.126.41", ktrc=TRACE)
    print("connesso")

    #print(BM.get_active_slc())
    print("active slc valutata")
    #print(BM.get_active_slc())
    #print(BM.send_command("help"))
    #print(BM.send_command(": touch /tmp/PIPPO"))
    #print(BM.read_remote_inventory(11))
    print("remote inventory per 11 ricevuta")
    print(BM.read_complete_remote_inventory())
    print("completa remote inventory ricevuta")

    BM.clean_up()

    print("FINE")
