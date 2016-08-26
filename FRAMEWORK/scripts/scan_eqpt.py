#!/usr/bin/env python
"""
Script used to retrieve and store Remote Inventory information from all reachable
cards

@Script: scan_eqpt.py
@AUTHOR: C.Ghelfi
@DATE  : 03/12/2015
"""

import os
import sys
import argparse
import time

from katelibs.access1850 import SER1850
from katelibs.plugin_bm  import Plugin1850BM
from katelibs.database   import TNet,TEquipment,TEquipType,TBoardType
from django.db           import connection


def get_eqpt_id_by_ip(node_ip):
    """ Get node id for specified IP address
    """
    for row in ALL_IP:
        if row.ip == node_ip:
            return row.t_equipment_id_equipment.id_equipment

    return None


def get_eqpt_type_name(the_id):
    """ Get equipment node type
    """
    return TEquipType.objects.get(id_type=the_id).name


def get_eqpt_ip(the_id):
    """ Get IP address for specified node
    """
    for row in ALL_IP:
        if row.t_equipment_id_equipment:
            if row.t_equipment_id_equipment.id_equipment == the_id:
                return row.ip

    return str(None)


def get_serial(the_id):
    """ Get serial information for specified node
    """
    cursor = connection.cursor()

    query = "SELECT T_NET_id_ip,port FROM T_SERIAL WHERE T_EQUIPMENT_id_equipment='{}'".format(the_id)

    cursor.execute(query)

    result = cursor.fetchall()
    if len(result) != 1:
        return None,None

    the_port = result[0][1]
    for row in ALL_IP:
        if row.id_ip == result[0][0]:
            the_serip = row.ip

    return the_serip,the_port


def get_net_info(the_id):
    """ Get network information for specified node
    """
    for row in ALL_IP:
        if row.t_equipment_id_equipment:
            if row.t_equipment_id_equipment.id_equipment == the_id:
                return row.nm,row.gw
    return None,None


def get_net_adapter(the_id):
    """ Get ethernet adapter for node
    """
    etype = TEquipment.objects.get(id_equipment=the_id).t_equip_type_id_type
    if etype.id_type == 1 or etype.id_type == 3 or etype.id_type == 14:
        return "eth1"
    if etype.id_type == 4 or etype.id_type == 5:
        return "dbg"
    if etype.id_type == 11:
        return "oamp"
    return "invalid"


def set_ip(the_id, the_ip):
    """ Set IP address for specified node
    """
    the_serip,the_port = get_serial(the_id)
    if the_serip is None or the_port is None:
        print("serial info not available for node [{}]".format(the_id))
        return False
    the_nm,the_gw = get_net_info(the_id)
    the_adapter = get_net_adapter(the_id)
    cmd_ifdn = "ifconfig {:s} down".format(the_adapter)
    cmd_ipad = "ifconfig {:s} {:s} netmask {:s}".format(the_adapter, the_ip, the_nm)
    cmd_ifup = "ifconfig {:s} up".format(the_adapter)
    cmd_rout = "route add default gw {:s}".format(the_gw)
    serial = SER1850((the_serip,the_port))
    if not serial.send_cmd_simple(cmd_ifdn):
        return False
    time.sleep(3)
    if not serial.send_cmd_simple(cmd_ipad):
        return False
    time.sleep(3)
    if not serial.send_cmd_simple(cmd_ifup):
        return False
    time.sleep(3)
    if not serial.send_cmd_simple(cmd_rout):
        return False
    time.sleep(3)
    print("IP [{}] now configured.".format(the_ip))
    return True


def is_reachable(the_ip):
    """ Check if the node is reachable
    """
    cmd = "ping -c 2 {:s} >/dev/null".format(the_ip)
    return os.system(cmd) == 0


def write_info(the_ip, reminv, verbose):
    """ Tracing Remote Inventory on stdout
    """
    if verbose:
        print("#" * 80)
        print(the_ip)
        for the_key in sorted(reminv, key=reminv.get, reverse=False):
            card_name = reminv[the_key][0]
            signature = reminv[the_key][1]
            print("\t{:2}: {:16s} [{}]".format(the_key, card_name, signature))
    else:
        print("Info stored on DB for [{}]".format(the_ip))


def check_info_on_db(eqpt_id, reminv):
    """ Evaluation of Remote Inventory and past information on DB
    """
    cursor = connection.cursor()

    query = "SELECT * FROM T_BOARDS WHERE T_EQUIPMENT_id_equipment='{}'".format(eqpt_id)

    cursor.execute(query)

    result = cursor.fetchall()
    if len(result) == 0:
        return False

    max_slot = max(reminv.keys())

    for row in result:
        if row[3] > max_slot:
            max_slot = row[3]

    for slot_idx in range(max_slot+1):
        if slot_idx == 0:
            continue

        db_board_type = ""
        db_sign = ""
        is_in_db = False
        is_in_ri = (slot_idx in reminv)

        for row in result:
            if row[3] == slot_idx:
                is_in_db = True
                db_sign = row[5]
                db_board_type = row[1]
                break

        if not is_in_ri and not is_in_db:
            continue

        if is_in_ri and is_in_db:
            if reminv[slot_idx][1] != db_sign:
                print("card con signature differente (rimpiazzata?)")

        if is_in_ri and not is_in_db:
            print("Board type {} inserita".format(reminv[slot_idx][0]))

        if not is_in_ri and is_in_db:
            print("Board type {} rimossa".format(get_eqpt_type_name(db_board_type)))

    return True


def delete_info_from_db(eqpt_id):
    """ Clean up Remote Inventory on DB for specified node
    """
    cursor = connection.cursor()

    query = "DELETE FROM T_BOARDS WHERE T_EQUIPMENT_id_equipment='{}'".format(eqpt_id)

    cursor.execute(query)


def insert_info_on_db(eqpt_id, reminv):
    """ Insert Remote Inventory on DB
    """
    if check_info_on_db(eqpt_id, reminv):
        delete_info_from_db(eqpt_id)

    for the_key in sorted(reminv, key=reminv.get, reverse=False):
        card_name = reminv[the_key][0]
        signature = reminv[the_key][1]
        card_id = None
        for row in ALL_BOARD_TYPE:
            if row.name == card_name:
                card_id = row.id_board_type
                break
        if card_id is None:
            print("UNKNOWN card type on node[{}], slot[{}]".format(eqpt_id, the_key))
            continue

        cursor = connection.cursor()

        query = ' '.join( ( "INSERT INTO T_BOARDS"
                            "   (",
                            "       T_BOARD_TYPE_id_board_type,"
                            "       T_EQUIPMENT_id_equipment,"
                            "       slot,"
                            "       remote_inventory",
                            "   )",
                            "   VALUES ('{}','{}','{}','{}')".format(card_id,
                                                                     eqpt_id,
                                                                     the_key,
                                                                     signature) ) )

        cursor.execute(query)


def is_a_new_node(eqpt_id):
    """ Verify if the specified node is a new one
    """
    cursor = connection.cursor()

    query = "SELECT id_board FROM T_BOARDS WHERE T_EQUIPMENT_id_equipment='{}'".format(eqpt_id)

    cursor.execute(query)

    result = cursor.fetchall()

    return len(result) == 0


def manage_node(the_id, the_ip, verbose):
    """ Analyze the specified node
    """
    try:
        bm_access = Plugin1850BM(the_ip)
    except Exception as eee:
        print("Exception on BM connecting - [{}]".format(eee))
        return

    try:
        reminv = bm_access.read_complete_remote_inventory()
    except Exception as eee:
        print("Exception on retrieving Remote Inventory - [{}]".format(eee))
        bm_access.clean_up()
        return

    bm_access.clean_up()

    if len(reminv) == 0:
        print("Empty remote inventory")
        return

    write_info(the_ip, reminv, verbose)
    insert_info_on_db(the_id, reminv)




if __name__ == "__main__":

    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("--fast", help="get only new nodes info", action="store_true")
    PARSER.add_argument("--nodeip", nargs=1, help="analyze only specified node IP")
    PARSER.add_argument("--setip", help="set IP address to node is not reachable", action="store_true")
    PARSER.add_argument("--verbose", help="print a detailed activity report", action="store_true")
    ARGS = PARSER.parse_args()

    ALL_IP = TNet.objects.all()
    ALL_BOARD_TYPE = TBoardType.objects.all()

    ##
    ## Manage only a specified Node
    ##
    if ARGS.nodeip is not None:
        IP_EQPT = ARGS.nodeip[0]
        ID_EQPT = get_eqpt_id_by_ip(IP_EQPT)
        if ID_EQPT is None:
            print("Node [{}] not found on DB".format(IP_EQPT))
            sys.exit(0)

        if not is_reachable(IP_EQPT):
            if ARGS.setip:
                if not set_ip(ID_EQPT, IP_EQPT):
                    print("Node [{}] not reachable (serial)".format(IP_EQPT))
                    sys.exit(0)
            else:
                print("Node [{}] not reachable (IP)".format(IP_EQPT))
                sys.exit(0)

        print("Connecting [{}]...".format(IP_EQPT))
        manage_node(ID_EQPT, IP_EQPT, ARGS.verbose)
        sys.exit(0)

    ##
    ## Manage all nodes
    ##
    for entry in TEquipment.objects.all():
        ID_EQPT = entry.id_equipment

        print("Analyzing eqpt id [{:5}]... ".format(ID_EQPT), end='')

        IP_EQPT = get_eqpt_ip(ID_EQPT)
        if IP_EQPT == "None":
            print("incomplete record - skip")
            continue

        eType = get_eqpt_type_name(entry.t_equip_type_id_type.id_type)
        if eType.find("1850TSS") == -1:
            print("remote inventory not managed [{}]- skip".format(eType))
            continue

        if ARGS.fast:
            if not is_a_new_node(ID_EQPT):
                print("[{}: {}] already checked - skip".format(ID_EQPT, IP_EQPT))
                continue
            else:
                print("[{}: {}] to be checked".format(ID_EQPT, IP_EQPT))

        if not is_reachable(IP_EQPT):
            if ARGS.setip:
                print("IP not set - try to configure it...")
                if not set_ip(ID_EQPT, IP_EQPT):
                    print("[{}: {}] not reachable (serial)".format(ID_EQPT, IP_EQPT))
                    continue
            else:
                print("[{}: {}] not reachable (IP)".format(ID_EQPT, IP_EQPT))
                continue

        print("connecting [{}: {}]...".format(ID_EQPT, IP_EQPT))
        manage_node(ID_EQPT, IP_EQPT, ARGS.verbose)
