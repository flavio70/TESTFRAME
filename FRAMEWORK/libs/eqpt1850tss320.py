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
import string
import equipment
import facility1850
import access1850
import plugin_tl1
from KateLibs.database import *



class Eqpt1850TSS320(equipment.Equipment):
    """
    1850TSS320 Equipment descriptor. Implements specific operations
    """

    def __init__(self, label, ID, krepo=None):
        """ label : equipment name used on Report file
            ID    : equipment ID (see T_EQUIPMENT table on K@TE DB)
        """
        self.__krepo    = krepo     # result report (Kunit class instance)
        self.__net_con  = None      # main 1850 IP Connection
        self.__ser_con  = None      # main 1850 Serial Connection (i.e. FLC 1 console)
        self.__net      = {}        # IP address informations (from DB)
        self.__ser      = {}        # Serial(s) informations (from DB)
        self.tl1        = None      # main TL1 channel (used to send user command to equipment)

        super().__init__(label, ID)

        self.__get_eqpt_info_from_db(ID)

        flc1ser = self.__ser.get_val(1)
        self.__ser_con = access1850.SER1850( (flc1ser[0], flc1ser[1]) )

        self.__open_main_ssh_connection()

        self.tl1 = plugin_tl1.Plugin1850TL1(self.__net.get_ip_str(), krepo=self.__krepo, eRef=self)


    def clean_up(self):
        self.tl1.thr_event_terminate()


    def flc_ip_config(self):
        """ Initialize Network configuration of Equipment
        """
        if self.__krepo:
            self.__krepo.startTime()

        if self.__is_reachable_by_ip():
            print("Equipment '" + self.get_label() + "' reachable by IP " + self.__net.get_ip_str())
            print("nothing to do.")
            self.__t_skipped("CONFIGURE IP", None, "equipment already reachable", "")
            return True
        else:
            print("Configuring IP address for equipment '" + self.get_label() + "'")
            dev     = self.__net.get_dev()
            cmd_ifdn = "ifconfig {:s} down".format(dev)
            cmd_hwet = "ifconfig {:s} hw ether {:s}".format(dev, self.__net.get_mac())
            cmd_ipad = "ifconfig {:s} {:s} netmask {:s}".format(dev, self.__net.get_ip_str(), self.__net.get_nm_str())
            cmd_ifup = "ifconfig {:s} up".format(dev)
            cmd_rout = "route add default gw {:s}".format(self.__net.get_gw_str())

            max_iterations = 50

            for i in range(1, max_iterations+1):
                self.__ser_con.send_cmd_simple(cmd_ifdn)
                time.sleep(3)
                self.__ser_con.send_cmd_simple(cmd_hwet)
                time.sleep(3)
                self.__ser_con.send_cmd_simple(cmd_ipad)
                time.sleep(5)
                self.__ser_con.send_cmd_simple(cmd_ifup)
                time.sleep(5)
                self.__ser_con.send_cmd_simple(cmd_rout)
                time.sleep(5)

                if not self.__is_ongoing_to_address(self.__net.get_gw_str()):
                    msg = "Error in IP Configuration. Retrying... [{:d}/{:d}]".format(i, max_iterations)
                    print(msg)
                else:
                    print("Equipment IP configuration OK. Waiting for external reachability")
                    break

            for i in range(1, max_iterations+1):
                if not self.__is_reachable_by_ip():
                    msg = "Equipment still not reachable. Retrying... [{:d}/{:d}]".format(i, max_iterations)
                    print(msg)
                    time.sleep(10)
                else:
                    self.__t_success("CONFIGURE IP", None, "Equipment reachable")
                    return True


            print("Error in IP CONFIG")
            self.__t_failure("CONFIGURE IP", None, "error in configuring IP", "")
            return False


    def flc_stop_dhcp(self):
        """ Shutdown DHCP daemon
        """
        print("DHCP DOWN")

        if self.__krepo:
            self.__krepo.startTime()

        res = self.__net_con.send_cmd_and_check("/etc/rc.d/init.d/dhcp stop", "Stopping DHCP server: dhcpd")
        if res == False:
            print("DHCP not stopped")
            self.__t_failure("DHCP SHUTDOWN", None, "error in DHCP shutdown", "")
        else:
            print("DHCP stopped")
            self.__t_success("DHCP SHUTDOWN", None, "DHCP shutted down")
        return res


    def flc_reboot(self):
        """ Perform FLC reboot
        """
        print("REBOOT FLC MAIN")

        if self.__krepo:
            self.__krepo.startTime()

        self.__net_con.send_cmd_simple("flc_reboot")

        klist = [b'Start BOOT image V', b'Restarting system']
        res = self.__ser_con.EXPECT(klist)
        if res[0] == 0  or  res[0] == 1:
            print("FLC RESTARTED")
            self.__t_success("FLC REBOOT", None, "FLC restarted")
            return True
        else:
            print("ERROR IN FLC REBOOT")
            self.__t_failure("FLC REBOOT", None, "error in FLC rebooting", "")
            return False


    def slc_reboot(self, slot):
        """ Perform specified SLC reboot
            slot : slc slot number
        """
        print("REBOOT SLC " + str(slot))
        flc_ip = self.__net.get_ip_str()
        slc_ip = "100.0.1.{:s}".format(slot)

        if not self.__is_reachable_by_ip(slc_ip):
            self.__t_skipped("SLC "+ str(slot) + " REBOOT", None, "SLC not present", "")
        return True

        try:
            tmpsh = access1850.SSH1850(flc_ip)
            tmpsh.telnet_tunnel(slc_ip)
            tmpsh.send_bm_command(slc_ip, "reboot")
            tmpsh.close_ssh()
        except Exception as eee:
            print(str(eee))
            self.__t_failure("SLC "+ str(slot) + " REBOOT", None, "error in SLC rebooting", "")
            return False

        self.__t_success("SLC "+ str(slot) + " REBOOT", None, "SLC restarted")

        return True


    def flc_scratch_db(self):
        """ Force a DB clean
        """
        print("SCRATCH DB...")

        if self.__krepo:
            self.__krepo.startTime()

        self.__net_con.send_cmd_simple("/bin/rm -fr /pureNeApp/FLC/DB/*")

        res = self.__net_con.send_cmd_and_check("/bin/ls -l /pureNeApp/FLC/DB", "total 0")
        if res == False:
            print("DB not scrtatched")
            self.__t_failure("SCRATCH DB", None, "error in scratching DB", "")
        else:
            print("DB scratched")
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
            self.__krepo.startTime()

        # Check for running application processes
        res = False
        for i in range(1, max_iterations+1):
            out = self.__net_con.send_cmd_and_capture("pidof bin_1850TSS_TDM320_FLC.bin")
            if out[:-1] == "":
                print("No running SWP yet. Retrying in 15s [{:d}/{:d}]".format(i, max_iterations))
                time.sleep(15)
            else:
                res = True
                break
        if not res:
            msg = "Not able to find a running SWP after {:d}s".format(15*max_iterations)
            print(msg)
            self.__t_failure("FLC IN SERVICE", None, "timeout", msg)

        # Check for TL1 agent
        res = False
        for i in range(1, max_iterations+1):
            if not self.__net_con.send_cmd_and_check("netstat -anp | grep ':3083'", "0.0.0.0:3083"):
                print("TL1 agent not ready. Retrying in 15s [{:d}/{:d}]".format(i, max_iterations))
                time.sleep(15)
            else:
                print("TL1 agent ready in {:d}s".format(15*i))
                res = True
                break
        if not res:
            msg = "Not able to find TL1 Agent after {:d}s".format(15*max_iterations)
            print(msg)
            self.__t_failure("FLC IN SERVICE", None, "timeout", msg)

        # Check for SNMP agent
        for sub_agent in 161,171:
            res = False
            for i in range(1, max_iterations+1):
                cmd = "netstat -anp | grep '{:d}'".format(sub_agent)
                if not self.__net_con.send_cmd_and_check(cmd, "bin_1850TSS_"):
                    print("SNMP:{:s} sub-agent not ready. Retrying in 15s [{:d}/{:d}]".format(sub_agent, i, max_iterations))
                    time.sleep(15)
                else:
                    print("SNMP:{:d} sub-agent ready in {:d}s".format(sub_agent, 15*i))
                    res = True
                    break
            if not res:
                msg = "Not able to find SNMP:{:d} sub-agent after {:d}s".format(sub_agent, 15*max_iterations)
                print(msg)
                self.__t_failure("FLC IN SERVICE", None, "timeout", msg)

        print("FLC IN SERVICE")

        self.__t_success("FLC IN SERVICE", None, "FLC correctly in service")

        return True


    def flc_load_swp(self, swp_string):
        """ Load the specified SWP
            swp_string : the StartApp string
        """
        print("LOADING SWP ON '" + self.get_label() + "'")
        print("SWP STRING: '" + swp_string + "'")

        if self.__krepo:
            self.__krepo.startTime()

        if self.__is_reachable_by_ip():
            print("SSH ACCESS")
            res = self.__net_con.send_cmd_and_check(swp_string, "EC_SetSwVersionActive status SUCCESS")
        else:
            print("SERIAL ACCESS")
            res = self.__ser_con.send_cmd_and_check(swp_string, "EC_SetSwVersionActive status SUCCESS")

        if res == False:
            print("SWP LOAD ERROR")
            self.__t_failure("SWP LOAD", None, "error in loading SWP", "")
        else:
            print("SWP LOADING TERMINATE")
            self.__t_success("SWP LOAD", None, "SWP correctly load")

        return res


    def flc_check_running_swp(self, swp_id):
        """ Check current SWP
            swp_id : identifier of release
        """
        pass

    def INSTALL(self, swp_string, do_format=False):
        """ Start a complete node installation
            swp_string   : the StartApp string
            do_format    : before swp loading, a complete disk format will be performed (default: False)
        """

        if not self.flc_checl_dual():
            print("INSTALL ABORTED")
            return False

        if do_format:
            print("FORMAT DISK AND INSTALL NODE")
        else:
            print("INSTALL NODE")
            if not self.flc_ip_config():
                print("INSTALL ABORTED")
                return False

            if not self.flc_load_swp(swp_string):
                print("INSTALL ABORTED")
                return False

            if not self.flc_stop_dhcp():
                print("INSTALL ABORTED")
                return False

            if not self.slc_reboot(10):
                print("INSTALL ABORTED")
                return False

            if not self.slc_reboot(11):
                print("INSTALL ABORTED")
                return False

            if not self.flc_scratch_db():
                print("INSTALL ABORTED")
                return False

            if not self.flc_reboot():
                print("INSTALL ABORTED")
                return False

        if not self.flc_checl_dual():
            print("INSTALL ABORTED")
            return False

        if not self.flc_ip_config():
            print("INSTALL ABORTED")
            return False

        if not self.flc_wait_in_service():
            print("INSTALL ABORTED")
            return False

        swp_id = ""     # sistemare

        if not self.flc_check_running_swp(""):
            print("INSTALL ABORTED")
            return False

        return True


    def __is_ongoing_to_address(self, dest_ip):
        cmd = "ping -c 4 {:s}".format(dest_ip)
        exp = "4 packets transmitted, 4 received, 0% packet loss,"
        res = self.__ser_con.send_cmd_and_check(cmd, exp)
        print(res)
        return res


    def __is_reachable_by_ip(self, eqpt_ip=None):
        if not eqpt_ip:
            eqpt_ip = self.__net.get_ip_str()
        cmd = "ping -c 4 {:s}".format(eqpt_ip)
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
        print("CONFIGURATION EQUIPMENT ID = " + str(ID))
        tabEqpt  = TEquipment

        e_name    = tabEqpt.objects.get(id_equipment=ID).name
        e_type_id = tabEqpt.objects.get(id_equipment=ID).t_equip_type_id_type.id_type
        e_type    = tabEqpt.objects.get(id_equipment=ID).t_equip_type_id_type.name

        e_ip,e_nm,e_gw  = self.__get_net_info(ID)

        print(e_ip,e_nm,e_gw)

        if   e_type_id == 1  or  e_type_id == 3:
            eth_adapter = "eth1"
        elif e_type_id == 4  or  e_type_id == 5:
            eth_adapter = "dbg"
        else:
            eth_adapter = "q"

        ip  = facility1850.IP(e_ip)
        nm  = facility1850.IP(e_nm)
        gw  = facility1850.IP(e_gw)

        print("  Name   : " + e_name)
        print("  Type   : " + e_type)
        print("  Net    : {:s} {:s} {:s} {:s} {:s}".format( eth_adapter,
                                                            ip.get_val(),
                                                            nm.get_val(),
                                                            gw.get_val(),
                                                            ip.evaluate_mac()))

        self.__net = facility1850.NetIF(ip, nm, gw, ip.evaluate_mac(), eth_adapter)
        self.__ser = facility1850.SerIF()

        tabSer = TSerial
        tabNet = TNet
        for r in tabSer.objects.all():
            if r.t_equipment_id_equipment.id_equipment == ID:
                sIP = tabNet.objects.get(id_ip=r.t_net_id_ip.id_ip)
                self.__ser.set_serial_to_slot(r.slot, facility1850.IP(sIP.ip), r.port)
                print("  Serial : {:2d} <--> {:s}:{:d}".format(r.slot, sIP.ip, r.port))


    def __open_main_ssh_connection(self):
        self.__net_con = access1850.SSH1850(self.__net.get_ip_str())


    def __close_main_ssh_connection(self):
        self.__net_con.close_ssh()
        self.__net_con = None


    def __t_success(self, title, elapsed_time, out_text):
        if self.__krepo:
            self.__krepo.add_success(self, title, elapsed_time, out_text)


    def __t_failure(self, title, e_time, outText, err_text, log_text=None):
        if self.__krepo:
            self.__krepo.add_failure(self, title, e_time, outText, err_text, log_text)


    def __t_skipped(self, title, e_time, outText, err_text, skip_text=None):
        if self.__krepo:
            self.__krepo.add_skipped(self, title, e_time, outText, err_text, skip_text)



if __name__ == '__main__':
    print("DEBUG Eqpt1850TSS320")

    #nodeA = Eqpt1850TSS320("nodeA", 1024)
    nodeB = Eqpt1850TSS320("nodeB", 1025)

    #nodeB.INSTALL("StartApp DWL 1850TSS320M 1850TSS320M V7.10.10-J041 151.98.16.7 0 /users/TOOLS/SCRIPTS/pkgStore_04/pkgStoreArea4x/alc-tss/base00.24/int/LIV_ALC-TSS_DR4-24J_BASE00.24.01__VM_PKG058/target/MAIN_RELEASE_71/swp_gccpp/1850TSS320-7.10.10-J041 4gdwl 4gdwl2k12 true")

    #nodeB.flc_reboot()
    #nodeB.flc_ip_config()
    #nodeB.flc_wait_in_service()

    if nodeB.tl1.do("ACT-USER::admin:MYTAG::Root1850;", policy="DENY"):
        print("RESULT: SUCCESS")
    else:
        print("RESULT: FAILURE")

    print("STATUS := " + nodeB.tl1.get_last_cmd_status() + "\nOUTPUT [" + nodeB.tl1.get_last_outcome() + "]")

    time.sleep(20)

    nodeB.clean_up()

    print("FINE")
