#!/usr/bin/env python  
"""
Script used to retrieve equipment informations from KATE DB

@Script: KateEqptReport.py
@AUTHOR: C.Ghelfi
@DATE  : 16/09/2015
"""

import os
import argparse

from django.db.models import F
from katelibs.database import *


def getEqptTypeName(tabEqptType, n):
    return tabEqptType.objects.get(id_type=n).name


def getEqptLocation(tabLocation, n):
    lRow    = tabLocation.objects.get(id_location=n).row
    lRack   = tabLocation.objects.get(id_location=n).rack
    lPos    = tabLocation.objects.get(id_location=n).pos
    return '{:s}-{:d}/{:d}'.format(lRow, lRack, lPos)


def getEqptIP(allIP, n):
    for r in allIP:
        if r.t_equipment_id_equipment:
            if r.t_equipment_id_equipment.id_equipment == n:
                return r.ip

    return str(None)


def getEqptSerial(allSer, n):
    msg = ""
    for r in allSer:
        if r.t_equipment_id_equipment.id_equipment == n:
            msg = "{:s} {:d} <-> {:s}:{:d} ".format(\
                        msg,
                        r.slot,
                        r.t_net_id_ip.ip,
                        r.port
                        )

    return msg


def getBoardTypeList():
    cursor = connection.cursor()
    query = "SELECT id_board_type,name FROM T_BOARD_TYPE"
    cursor.execute(query)

    result = cursor.fetchall()

    board_type_list = {}

    if len(result) > 0:
        for row in result:
            board_type_list[row[0]] = row[1]

    return board_type_list


def getEqptBoards(eqpt_id, eqpt_type, board_type_list):
    if not eqpt_type in ['1850TSS320', '1850TSS320H', '1850TSS160', '1850TSS160H', 'TSS-320T']:
        return None

    cursor = connection.cursor()

    query = ' '.join( ( "SELECT T_BOARD_TYPE_id_board_type, slot",
                        "FROM   T_BOARDS",
                        "WHERE  T_EQUIPMENT_id_equipment='{}'".format(eqpt_id) ) )
    cursor.execute(query)

    result = cursor.fetchall()

    list_boards = None

    if len(result) > 0:
        for row in result:
            slot = row[1]
            board_name = board_type_list[row[0]]

            if list_boards is None:
                list_boards = "{}:{}".format(slot, board_name)
            else:
                list_boards = "{} {}:{}".format(list_boards, slot, board_name)

    return list_boards


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--serials", help="get serials info", action="store_true")
    parser.add_argument("--boards", help="get boards info", action="store_true")
    args = parser.parse_args()

    allIP  = TNet.objects.all()
    allSer = TSerial.objects.all()
    board_type_list = getBoardTypeList()

    tabLocation = TLocation
    tabEqptType = TEquipType

    for r in TEquipment.objects.all():
        eType = getEqptTypeName(tabEqptType, r.t_equip_type_id_type.id_type)
        eLoc  = getEqptLocation(tabLocation, r.t_location_id_location.id_location)
        eIP   = getEqptIP(allIP, r.id_equipment)

        if args.serials:
            eSer = getEqptSerial(allSer, r.id_equipment)
            res='{:5s} {:12s} {:10s} {:20s} {:20s} {:16} {:s}'.format(
                    str(r.id_equipment),
                    eType,
                    eLoc,
                    str(r.name),
                    eIP,
                    str(r.owner),
                    eSer
                )
        elif args.boards:
            board_list = getEqptBoards(r.id_equipment, eType, board_type_list)
            if board_list is None:
                board_list = ""
            else:
                board_list = "[{}]".format(board_list)

            res='{:5s} {:12s} {:10s} {:20s} {:20s} {:16} {}'.format(
                    str(r.id_equipment),
                    eType,
                    eLoc,
                    str(r.name),
                    eIP,
                    str(r.owner),
                    board_list
                )
        else:
            res='{:5s} {:12s} {:10s} {:20s} {:20s} {:16}'.format(
                    str(r.id_equipment),
                    eType,
                    eLoc,
                    str(r.name),
                    eIP,
                    str(r.owner)
                )
        print(res)
