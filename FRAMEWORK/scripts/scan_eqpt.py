#!/usr/bin/env python  

import os
import argparse

from katelibs.database  import *
from katelibs.plugin_bm import Plugin1850BM


def getEqptTypeName(tabEqptType, n):
    return tabEqptType.objects.get(id_type=n).name


def getEqptIP(allIP, n):
    for r in allIP:
        if r.t_equipment_id_equipment:
            if r.t_equipment_id_equipment.id_equipment == n:
                return r.ip

    return str(None)


def is_reachable(ip):
    cmd = "ping -c 2 {:s} >/dev/null".format(ip)
    return (os.system(cmd) == 0)


def write_info(ip, reminv):
    if reminv.len() == 0:
        return

    print("#" * 80)
    print(ip)
    for the_key in sorted(reminv, key=reminv.get, reverse=False):
        card_name = reminv[the_key][0]
        signature = reminv[the_key][1]
        print("\t{:2}: {:16s} [{}]".format(the_key, card_name, signature))

if __name__ == "__main__":

    #parser = argparse.ArgumentParser()
    #parser.add_argument("--all", help="get full info", action="store_true")
    #args = parser.parse_args()

    tabEqptType = TEquipType

    allIP  = TNet.objects.all()

    for r in TEquipment.objects.all():
        eType = getEqptTypeName(tabEqptType, r.t_equip_type_id_type.id_type)
        eIP   = getEqptIP(allIP, r.id_equipment)

        if eIP != "None":
            if eType.find("1850TSS") != -1:
                if is_reachable(eIP):
                    bm = Plugin1850BM(eIP)
                    reminv = bm.read_complete_remote_inventory()
                    write_info(eIP, reminv)
                    bm.clean_up()
