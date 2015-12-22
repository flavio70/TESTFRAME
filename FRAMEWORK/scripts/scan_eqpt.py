#!/usr/bin/env python  

import os
import sys
import argparse

from katelibs.plugin_bm import Plugin1850BM
from katelibs.database  import *
from django.db          import connection


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


def write_info(ip, reminv):
    print("#" * 80)
    print(ip)
    for the_key in sorted(reminv, key=reminv.get, reverse=False):
        card_name = reminv[the_key][0]
        signature = reminv[the_key][1]
        print("\t{:2}: {:16s} [{}]".format(the_key, card_name, signature))


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
        for r in tab_board_type.objects.all():
            if r.name == card_name:
                card_id = r.id_board_type
                break
        if card_id is None:
            card_id = 0     # UNKNOWN card type

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


if __name__ == "__main__":

    #parser = argparse.ArgumentParser()
    #parser.add_argument("--all", help="get full info", action="store_true")
    #args = parser.parse_args()

    tab_eqpt_type = TEquipType
    tab_board_type = TBoardType

    if False:
        reminv = {}
        reminv[2]   = "10X1GEPP","32324149544131305831474550504E47433541464B46414138444730383035314141414130312D2D2D2D2D2D2D2D2D2D2D2D2D2D434C2020434C303832303930333330202020202030303038313032312D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2DE6BB"
        reminv[22]  = "1P10GSO","3232414954413150313047534F204E4749374143394D414133414C39323131314141414130312020202020202020202020202020434C2020434C3036323839303831352020202020303030363037323120202020202020202020202020202020202020202020202020202020202020202020202020202020202020202020E9E9"
        reminv[33]  = "1P10GSO","3232414954413150313047534F204E4749374146324D414133414C39323131314141414130332D2D2D2D2D2D2D2D2D2D2D2D2D2D434C2020434C303631353930373037202020202030303037303632322D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2DE6E2"
        reminv[12]  = "1X10GEPP","2324149544131583130474550504E47433541464A46414138444730383034394141414130312D2D2D2D2D2D2D2D2D2D2D2D2D2D434C2020434C303831373930353439202020202030303038303730332D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2DE69D"
        reminv[9]   = "1X10GEPP","2324149544131583130474550504E47433541464A46414138444730383034394141414130312D2D2D2D2D2D2D2D2D2D2D2D2D2D434C2020434C303832303930313038202020202030303038303532362D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2DE6A9"
        reminv[1]   = "EC320","32324149544145433332302020204E47433541473246414133414C39323131304141414530362D2D2D2D2D2D2D2D2D2D2D2D2D2D434C2020434C303932373931323938202020202030303131303531302D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2DE755"
        reminv[10]  = "MT160LO","3232414954414D543136304C4F204E47433541473046414133414C39323130384146414130342D2D2D2D2D2D2D2D2D2D2D2D2D2D434C2020434C303934303930383430202020202030303039313030322D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2D2DE6E4"
        reminv[32]  = "PP10GEX2","FFFFFFFFFFF5050313047455832FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF885F"
        reminv[15]  = "PP10GEX2","FFFFFFFFFFF5050313047455832FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF885F"

        insert_info_on_db(1009, reminv)
        sys.exit(0)


    allIP = TNet.objects.all()

    for r in TEquipment.objects.all():
        eType = getEqptTypeName(r.t_equip_type_id_type.id_type)
        eIP   = getEqptIP(r.id_equipment)

        if eIP != "None":
            if eType.find("1850TSS") != -1:
                if is_reachable(eIP):
                    bm = Plugin1850BM(eIP)
                    reminv = bm.read_complete_remote_inventory()
                    if len(reminv) != 0:
                        write_info(eIP, reminv)
                        insert_info_on_db(r.id_equipment, reminv)
                    bm.clean_up()
