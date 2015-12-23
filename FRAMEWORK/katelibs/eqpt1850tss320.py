#!/usr/bin/env python
###############################################################################
# MODULE: eqpt1850tss320.py
#
# AUTHOR: C.Ghelfi
# DATE  : 29/07/2015
#
###############################################################################

import os
import time

from katelibs.kenviron      import KEnvironment
from katelibs.kpreset       import KPreset
from katelibs.kunit         import Kunit
from katelibs.equipment     import Equipment
from katelibs.facility1850  import IP, NetIF, SerIF
from katelibs.access1850    import SER1850, SSH1850
from katelibs.facility_tl1  import TL1message
from katelibs.plugin_tl1    import Plugin1850TL1
from katelibs.plugin_cli    import Plugin1850CLI
from katelibs.plugin_bm     import Plugin1850BM
from katelibs.database      import *



class Eqpt1850TSS320(Equipment):
    """
    1850TSS320 Equipment descriptor. Implements specific operations
    """

    def __init__(self, label, kenv):
        """ label   : equipment name used on Report file
            kenv    : instance of KEnvironment (initialized by K@TE FRAMEWORK)
        """
        # Public members:
        self.tl1        = None          # TL1 plugin (used to send TL1 command to equipment)
        self.cli        = None          # CLI plugin (used to send CLI command to equipment)
        self.bm         = None          # BM  plugin (used to send BM command to equipment)
        self.id         = None          # 1850 Database ID
        # Private members:
        self.__kenv     = kenv          # Kate Environment
        self.__krepo    = kenv.krepo    # result report (Kunit class instance)
        self.__prs      = kenv.kprs     # Presets for running environment
        self.__arch     = None          # Architecture of current Equipment ("STD"/"ENH"/"SIM")
        self.__swp      = None          # SWP Descriptor
        self.__net_con  = None          # main 1850 IP Connection
        self.__ser_con  = None          # main 1850 Serial Connection (i.e. FLC 1 console)
        self.__net      = {}            # IP address informations (from DB)
        self.__ser      = {}            # Serial(s) informations (from DB)

        super().__init__(label, self.__prs.get_id(label))

        self.id = self.get_id()
        
        self.__get_eqpt_info_from_db(self.__prs.get_id(label))

        flc1ser = self.__ser.get_val(1)
        self.__ser_con = SER1850( (flc1ser[0], flc1ser[1]) )

        self.__net_con = SSH1850(self.__net.get_ip_str())

        tl1_event = "{:s}/{:s}_tl1_event.log".format(kenv.path_collector(), label)

        self.tl1 = Plugin1850TL1(   self.__net.get_ip_str(),
                                    eRef=self,
                                    krepo=self.__krepo,
                                    ktrc=self.__kenv.ktrc,
                                    collector=tl1_event)

        self.cli = Plugin1850CLI(   self.__net.get_ip_str(),
                                    eRef=self,
                                    ktrc=self.__kenv.ktrc,
                                    krepo=self.__krepo)

        self.bm  = Plugin1850BM(    self.__net.get_ip_str(),
                                    eRef=self,
                                    krepo=self.__krepo,
                                    ktrc=self.__kenv.ktrc)


    def clean_up(self):
        self.tl1.thr_event_terminate()
        self.cli.disconnect()
        self.bm.clean_up()


    def get_preset(self, name):
        """ Get current value for specified presetting
        """
        return self.__kenv.kprs.get_elem(self.get_label(), name)


    def flc_ip_config(self):
        """ Initialize Network configuration of Equipment
        """
        if self.__krepo:
            self.__krepo.start_time()

        if self.__is_reachable_by_ip():
            self.__trc_dbg("Equipment '{}' reachable by IP {}\nnothing to do.".format(\
                                self.get_label(), self.__net.get_ip_str()))
            self.__t_skipped("CONFIGURE IP", None, "equipment already reachable", "")
            return True
        else:
            self.__trc_dbg("Configuring IP address for equipment '{}'".format(self.get_label()))
            dev = self.__net.get_dev()
            cmd_ifdn = "ifconfig {:s} down".format(dev)
            cmd_ipad = "ifconfig {:s} {:s} netmask {:s} hw ether {:s}".format(\
                            dev,
                            self.__net.get_ip_str(),
                            self.__net.get_nm_str(),
                            self.__net.get_mac())
            cmd_ifup = "ifconfig {:s} up".format(dev)
            cmd_rout = "route add default gw {:s}".format(self.__net.get_gw_str())

            max_iterations = 50

            for i in range(1, max_iterations+1):
                self.__trc_dbg("trying to connect (#{:d}/{:d})".format(i, max_iterations))
                self.__ser_con.send_cmd_simple(cmd_ifdn)
                time.sleep(3)
                self.__ser_con.send_cmd_simple(cmd_ipad)
                time.sleep(5)
                self.__ser_con.send_cmd_simple(cmd_ifup)
                time.sleep(5)
                self.__ser_con.send_cmd_simple(cmd_rout)
                time.sleep(5)

                if not self.__is_ongoing_to_address(self.__net.get_gw_str()):
                    self.__trc_err("Error in IP Configuration. Retrying... [{:d}/{:d}]".format(i, max_iterations))
                else:
                    self.__trc_dbg("Equipment IP configuration OK. Waiting for external reachability")
                    break

            for i in range(1, max_iterations+1):
                if not self.__is_reachable_by_ip():
                    self.__trc_dbg("Equipment still not reachable. Retrying... [{:02d}/{:d}]".format(i, max_iterations))
                    time.sleep(15)
                else:
                    self.__t_success("CONFIGURE IP", None, "Equipment reachable")
                    return True


            self.__trc_err("Error in IP CONFIG")
            self.__t_failure("CONFIGURE IP", None, "error in configuring IP", "")
            return False


    def flc_stop_dhcp(self):
        """ Shutdown DHCP daemon
        """
        self.__trc_dbg("DHCP DOWN")

        if self.__krepo:
            self.__krepo.start_time()

        res = self.__net_con.send_cmd_and_check("/etc/rc.d/init.d/dhcp stop", "Stopping DHCP server: dhcpd")
        if res == False:
            self.__trc_err("DHCP not stopped")
            self.__t_failure("DHCP SHUTDOWN", None, "error in DHCP shutdown", "")
        else:
            self.__trc_dbg("DHCP stopped")
            self.__t_success("DHCP SHUTDOWN", None, "DHCP shutted down")
        return res


    def flc_reboot(self):
        """ Perform FLC reboot
        """
        self.__trc_dbg("REBOOT FLC MAIN")

        if self.__krepo:
            self.__krepo.start_time()

        self.__net_con.send_cmd_simple("flc_reboot")

        klist = [b'Start BOOT image V', b'Restarting system']
        res = self.__ser_con.expect(klist)
        if res[0] == 0  or  res[0] == 1:
            self.__trc_dbg("FLC RESTARTED")
            self.__t_success("FLC REBOOT", None, "FLC restarted")
            return True
        else:
            self.__trc_err("ERROR IN FLC REBOOT")
            self.__t_failure("FLC REBOOT", None, "error in FLC rebooting", "")
            return False


    def slc_reboot(self, slot):
        """ Perform specified SLC reboot
            slot : slc slot number
        """
        slc_ip = "100.0.1.{:d}".format(slot)

        if not self.__is_ongoing_to_address(slc_ip):
            self.__trc_dbg("SLC {:s} NOT PRESENT ".format(slot))
            self.__t_skipped("SLC {:d} REBOOT".format(slot), None, "SLC not present", "")
            return True

        self.__trc_dbg("REBOOT SLC {:s}".format(slot))

        self.bm.slc_reboot(slot)
        print("BM COMMAND SENT")

        self.__t_success("SLC {:s} REBOOT".format(slot), None, "SLC restarted")

        return True


    def flc_scratch_db(self):
        """ Force a DB clean
        """
        self.__trc_dbg("SCRATCH DB...")

        if self.__krepo:
            self.__krepo.start_time()

        self.__net_con.send_cmd_simple("/bin/rm -fr /pureNeApp/FLC/DB/*")

        res = self.__net_con.send_cmd_and_check("/bin/ls -l /pureNeApp/FLC/DB", "total 0")
        if res == False:
            self.__trc_err("DB not scrtatched")
            self.__t_failure("SCRATCH DB", None, "error in scratching DB", "")
        else:
            self.__trc_dbg("DB scratched")
            self.__t_success("SCRATCH DB", None, "DB correctly scratched")
        return res


    def flc_checl_dual(self):
        """ Check for DUAL FLC configuration.
            Force FLC 1 to be active
        """
        pass


    def flc_wait_in_service(self):
        """ Waiting for FLC In Service
        """
        max_iterations = 50

        if self.__krepo:
            self.__krepo.start_time()

        # Check for running application processes
        res = False
        for i in range(1, max_iterations+1):
            out = self.__net_con.send_cmd_and_capture("pidof bin_1850TSS_TDM320_FLC.bin")
            if out[:-1] == "":
                self.__trc_dbg("No running SWP yet. Retrying in 15s [{:d}/{:d}]".format(i, max_iterations))
                time.sleep(15)
            else:
                res = True
                break
        if not res:
            msg = "Not able to find a running SWP after {:d}s".format(15*max_iterations)
            self.__trc_err(msg)
            self.__t_failure("FLC IN SERVICE", None, "timeout", msg)

        # Check for TL1 agent
        res = False
        for i in range(1, max_iterations+1):
            if not self.__net_con.send_cmd_and_check("netstat -anp | grep ':3083'", "0.0.0.0:3083"):
                self.__trc_dbg("TL1 agent not ready. Retrying in 15s [{:d}/{:d}]".format(i, max_iterations))
                time.sleep(15)
            else:
                self.__trc_dbg("TL1 agent ready in {:d}s".format(15*i))
                res = True
                break
        if not res:
            msg = "Not able to find TL1 Agent after {:d}s".format(15*max_iterations)
            self.__trc_err(msg)
            self.__t_failure("FLC IN SERVICE", None, "timeout", msg)

        # Check for SNMP agent
        for sub_agent in 161,171:
            res = False
            for i in range(1, max_iterations+1):
                cmd = "netstat -anp | grep '{:d}'".format(sub_agent)
                if not self.__net_con.send_cmd_and_check(cmd, "bin_1850TSS_"):
                    self.__trc_dbg("SNMP:{:s} sub-agent not ready. Retrying in 15s [{:d}/{:d}]".format(sub_agent,
                                                                                                       i,
                                                                                                       max_iterations))
                    time.sleep(15)
                else:
                    self.__trc_dbg("SNMP:{:d} sub-agent ready in {:d}s".format(sub_agent, 15*i))
                    res = True
                    break
            if not res:
                msg = "Not able to find SNMP:{:d} sub-agent after {:d}s".format(sub_agent, 15*max_iterations)
                self.__trc_err(msg)
                self.__t_failure("FLC IN SERVICE", None, "timeout", msg)

        self.__trc_dbg("FLC IN SERVICE")

        self.__t_success("FLC IN SERVICE", None, "FLC correctly in service")

        return True


    def flc_load_swp(self, swp):
        """ Load the specified SWP. The equipment must be reachable by ip address
            swp : an instance of SWP1850TSS class
        """
        self.__swp = swp
        if self.__krepo:
            self.__krepo.start_time()

        if not self.__is_reachable_by_ip():
            self.flc_ip_config()

        if self.flc_check_running_swp():
            self.__trc_dbg("SWP '{:s}' ALREADY RUNNING\n".format(self.__swp.get_swp_ref()))
            res = True
            self.__t_skipped("SWP LOAD", None, "SWP already running", "")
        else:
            swp_string = self.__swp.get_startapp(self.__arch)

            self.__trc_dbg("LOADING SWP ON '{:s}\nSWP STRING: '{:s}'".format(self.get_label(), swp_string))

            res = self.__net_con.send_cmd_and_check(swp_string, "EC_SetSwVersionActive status SUCCESS")

            if res == False:
                self.__trc_err("SWP LOAD ERROR\n")
                self.__t_failure("SWP LOAD", None, "error in loading SWP", "")
            else:
                self.__trc_dbg("SWP LOADING TERMINATE\n")
                self.__t_success("SWP LOAD", None, "SWP correctly load")

        return res


    def flc_check_running_swp(self):
        """ Check running SWP with expected one
        """
        if self.__swp is None:
            self.__trc_err("SWP INFORMATION NOT PRESENT")
            return True

        # Using 'bootcmd r' in order to detect running SWP
        if self.__arch == "ENH":
            # Enhanced Shelf
            cmd = "bootcmd r | grep ACT:"
            res = self.__ser_con.send_cmd_and_capture(cmd)
            current_swp_id = res.split()[1]
        else:
            # Standard and Simulated shelves
            cmd = "bootcmd r | grep ACTIVE"
            res = self.__ser_con.send_cmd_and_capture(cmd)
            current_swp_id = res.split()[0]

        return (current_swp_id == self.__swp.get_swp_ref())


    def INSTALL(self, swp, do_format=False):
        """ Start a complete node installation
            swp       : an instance of SWP1850TSS class
            do_format : before swp loading, a complete disk format will be performed (default: False)
        """

        if not self.flc_checl_dual():
            self.__trc_err("INSTALL ABORTED")
            return False

        if do_format:
            self.__trc_dbg("FORMAT DISK AND INSTALL NODE")
        else:
            self.__trc_dbg("INSTALL NODE")
            if not self.flc_ip_config():
                self.__trc_err("INSTALL ABORTED")
                return False

            if not self.flc_load_swp(swp):
                self.__trc_err("INSTALL ABORTED")
                return False

            if not self.flc_stop_dhcp():
                self.__trc_err("INSTALL ABORTED")
                return False

            if not self.slc_reboot(10):
                self.__trc_err("INSTALL ABORTED")
                return False

            if not self.slc_reboot(11):
                self.__trc_err("INSTALL ABORTED")
                return False

            if not self.flc_scratch_db():
                self.__trc_err("INSTALL ABORTED")
                return False

            if not self.flc_reboot():
                self.__trc_err("INSTALL ABORTED")
                return False

        if not self.flc_checl_dual():
            self.__trc_err("INSTALL ABORTED")
            return False

        if not self.flc_ip_config():
            self.__trc_err("INSTALL ABORTED")
            return False

        if not self.flc_wait_in_service():
            self.__trc_err("INSTALL ABORTED")
            return False

        swp_id = ""     # sistemare

        if not self.flc_check_running_swp():
            self.__trc_err("INSTALL ABORTED")
            return False

        return True


    def __is_ongoing_to_address(self, dest_ip):
        # Check if this equipment is able to reach a specified IP address - Command sent to console interface
        cmd = "ping -c 4 {:s}".format(dest_ip)
        exp = "4 packets transmitted, 4 received, 0% packet loss,"
        res = self.__ser_con.send_cmd_and_check(cmd, exp)
        return res


    def __is_reachable_by_ip(self):
        # Verify IP connection from network to this equipment
        cmd = "ping -c 2 {:s} >/dev/null".format(self.__net.get_ip_str())
        if os.system(cmd) == 0:
            return True
        return False


    def __get_net_info(self, n):
        tabNet = TNet

        for r in tabNet.objects.all():
            if r.t_equipment_id_equipment:
                if r.t_equipment_id_equipment.id_equipment == n:
                    return r.ip,r.nm,r.gw

        return str(None),str(None),str(None)


    def __get_eqpt_info_from_db(self, ID):
        self.__trc_inf("CONFIGURATION EQUIPMENT ID := {:d}".format(ID))
        tabEqpt  = TEquipment

        e_name    = tabEqpt.objects.get(id_equipment=ID).name
        e_type_id = tabEqpt.objects.get(id_equipment=ID).t_equip_type_id_type.id_type
        e_type    = tabEqpt.objects.get(id_equipment=ID).t_equip_type_id_type.name

        e_ip,e_nm,e_gw  = self.__get_net_info(ID)

        if   e_type_id == 1  or  e_type_id == 3:
            self.__arch = "STD"
            eth_adapter = "eth1"
        elif e_type_id == 4  or  e_type_id == 5:
            self.__arch = "ENH"
            eth_adapter = "dbg"
        else:
            self.__arch = "SIM"
            eth_adapter = "q"

        ip  = IP(e_ip)
        nm  = IP(e_nm)
        gw  = IP(e_gw)

        self.__trc_inf("  Name   : {:s}".format(e_name))
        self.__trc_inf("  Type   : {:s}".format(e_type))
        self.__trc_inf("  Net    : {:s} {:s} {:s} {:s} {:s}".format(eth_adapter,
                                                                    ip.get_val(),
                                                                    nm.get_val(),
                                                                    gw.get_val(),
                                                                    ip.evaluate_mac()))

        self.__net = NetIF(ip, nm, gw, ip.evaluate_mac(), eth_adapter)
        self.__ser = SerIF()

        tabSer = TSerial
        tabNet = TNet
        for r in tabSer.objects.all():
            if r.t_equipment_id_equipment.id_equipment == ID:
                sIP = tabNet.objects.get(id_ip=r.t_net_id_ip.id_ip)
                self.__ser.set_serial_to_slot(r.slot, IP(sIP.ip), r.port)
                self.__trc_inf("  Serial : {:2d} <--> {:s}:{:d}".format(r.slot, sIP.ip, r.port))

        self.__trc_inf("CONFIGURATION END\n")


    def __open_main_ssh_connection(self):
        self.__net_con = SSH1850(self.__net.get_ip_str())


    def __close_main_ssh_connection(self):
        self.__net_con.close_ssh()
        self.__net_con = None


    def __t_success(self, title, elapsed_time, out_text):
        """ INTERNAL USAGE
        """
        if self.__krepo:
            self.__krepo.add_success(self, title, elapsed_time, out_text)


    def __t_failure(self, title, e_time, out_text, err_text, log_text=None):
        """ INTERNAL USAGE
        """
        if self.__krepo:
            self.__krepo.add_failure(self, title, e_time, out_text, err_text, log_text)


    def __t_skipped(self, title, e_time, out_text, err_text, skip_text=None):
        """ INTERNAL USAGE
        """
        if self.__krepo:
            self.__krepo.add_skipped(self, title, e_time, out_text, err_text, skip_text)


    def __trc_dbg(self, msg):
        """ INTERNAL USAGE
        """
        self.__kenv.ktrc.k_tracer_debug(msg, level=1)


    def __trc_inf(self, msg):
        """ INTERNAL USAGE
        """
        self.__kenv.ktrc.k_tracer_info(msg, level=1)


    def __trc_err(self, msg):
        """ INTERNAL USAGE
        """
        self.__kenv.ktrc.k_tracer_error(msg, level=1)



if __name__ == '__main__':
    print("DEBUG Eqpt1850TSS320")
    #r=Kunit('pippo')
    kenvironment = KEnvironment(testfilename="PROVA.py")
    #nodeA = Eqpt1850TSS320("nodeA", 1024)
    nodeB = Eqpt1850TSS320("nodeB", 1025)

    THE_SWP = SWP1850TSS()
    THE_SWP.init_from_db(swp_flv="FLV_ALC-TSS__BASE00.25.FD0491__VM")

    #nodeB.INSTALL(THE_SWP)

    #nodeB.flc_ip_config()
    #nodeB.flc_reboot()
    nodeB.slc_reboot(11)
    #nodeB.flc_ip_config()
    #nodeB.flc_wait_in_service()

    time.sleep(2)

    nodeB.clean_up()

    #r.frame_close()

    print("FINE")
