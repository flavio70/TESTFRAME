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

from katelibs.plugin_bm import Plugin1850BM
from katelibs.database  import *
from django.db          import connection


def getEqptIdByIP(node_ip):
    for r in allIP:
        if r.ip == node_ip:
            return r.t_equipment_id_equipment.id_equipment

    return None


def getEqptTypeName(n):
    return tab_eqpt_type.objects.get(id_type=n).name


def getEqptIP(n):
    for r in allIP:
        if r.t_equipment_id_equipment:
            if r.t_equipment_id_equipment.id_equipment == n:
                return r.ip

    return str(None)


def is_reachable(ip):
    cmd = "ping -c 2 {:s} >/dev/null".format(ip)
    return (os.system(cmd) == 0)


def write_info(ip, reminv, verbose):
    if verbose:
        print("#" * 80)
        print(ip)
        for the_key in sorted(reminv, key=reminv.get, reverse=False):
            card_name = reminv[the_key][0]
            signature = reminv[the_key][1]
            print("\t{:2}: {:16s} [{}]".format(the_key, card_name, signature))
    else:
        print("Info stored on DB for [{}]".format(ip))


def check_info_on_db(eqpt_id, reminv):
    cursor = connection.cursor()

    query = ' '.join( ( "SELECT *",
                        "FROM   T_BOARDS",
                        "WHERE  T_EQUIPMENT_id_equipment='{}'".format(eqpt_id) ) )

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

        is_in_ri = False
        is_in_db = False
        db_sign = ""
        db_board_type = ""

        if slot_idx in reminv:
            is_in_ri = True

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
                print("signature differente")

        if is_in_ri and not is_in_db:
            print("Board type {} inserita".format(reminv[slot_idx][0]))

        if not is_in_ri and is_in_db:
            print("Board type {} rimossa".format(db_board_type))

    return True


def delete_info_from_db(eqpt_id):
    cursor = connection.cursor()

    query = "DELETE FROM T_BOARDS WHERE T_EQUIPMENT_id_equipment='{}'".format(eqpt_id)

    cursor.execute(query)


def insert_info_on_db(eqpt_id, reminv):
    if check_info_on_db(eqpt_id, reminv):
        delete_info_from_db(eqpt_id)

    for the_key in sorted(reminv, key=reminv.get, reverse=False):
        card_name = reminv[the_key][0]
        signature = reminv[the_key][1]
        id_board_type = None
        card_id = None
        for r in tab_board_type.objects.all():
            if r.name == card_name:
                card_id = r.id_board_type
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
                                                                     signature)
                        ) )

        cursor.execute(query)

        result = cursor.fetchall()


def is_a_new_node(eqpt_id):
    cursor = connection.cursor()

    query = ' '.join( ( "SELECT id_board",
                        "FROM   T_BOARDS",
                        "WHERE  T_EQUIPMENT_id_equipment='{}'".format(eqpt_id) ) )

    cursor.execute(query)

    result = cursor.fetchall()

    return (len(result) == 0)


def get_info_for_node_ip(node_ip, verbose):
    eIP = node_ip[0]

    id_eqpt = getEqptIdByIP(eIP)
    if id_eqpt is None:
        print("Node [{}] not found on DB".format(eIP))
        sys.exit(0)

    if is_reachable(eIP):
        print("Connecting [{}]...".format(eIP))
        try:
            bm = Plugin1850BM(eIP)
        except Exception as eee:
            print("Exception on connecting [{}]".format(eee))
            return

        try:
            reminv = bm.read_complete_remote_inventory()
        except Exception as eee:
            print("Exception on retrieving info [{}]".format(eee))
            bm.clean_up()
            return

        if len(reminv) != 0:
            write_info(eIP, reminv, True)
            insert_info_on_db(id_eqpt, reminv)
        else:
            print("Empty remote inventory")

        bm.clean_up()
    else:
        print("Node [{}] not reachable".format(eIP))



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", help="get only new nodes info", action="store_true")
    parser.add_argument("--verbose", help="print a detailed activity report", action="store_true")
    parser.add_argument("--nodeip", nargs=1, help="can only specified node ip")
    #parser.add_argument("--all", help="get full info", action="store_true")
    args = parser.parse_args()

    tab_eqpt_type = TEquipType
    tab_board_type = TBoardType
    allIP = TNet.objects.all()

    if args.nodeip is not None:
        get_info_for_node_ip(args.nodeip, args.verbose)
    else:
        for r in TEquipment.objects.all():
            eType = getEqptTypeName(r.t_equip_type_id_type.id_type)
            eIP   = getEqptIP(r.id_equipment)

            if eIP != "None":
                if eType.find("1850TSS") != -1:
                    if args.fast:
                        if not is_a_new_node(r.id_equipment):
                            print("Node [{}: {}] already checked - skip".format(r.id_equipment, eIP))
                            continue
                        else:
                            print("Node [{}: {}] to be checked".format(r.id_equipment, eIP))

                    if is_reachable(eIP):
                        print("Connecting [{}: {}]...".format(r.id_equipment, eIP))
                        try:
                            bm = Plugin1850BM(eIP)
                        except Exception as eee:
                            print("Exception on connecting [{}]".format(eee))
                            continue

                        try:
                            reminv = bm.read_complete_remote_inventory()
                        except Exception as eee:
                            print("Exception on retrieving info [{}]".format(eee))
                            bm.clean_up()
                            continue

                        if len(reminv) != 0:
                            write_info(eIP, reminv, args.verbose)
                            insert_info_on_db(r.id_equipment, reminv)

                        bm.clean_up()
                    else:
                        print("Node [{}: {}] not reachable".format(r.id_equipment, eIP))
