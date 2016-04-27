#!/usr/bin/env python
"""
Script used to retrieve equipment informations from KATE DB

@Script: KateEqptReport.py
@AUTHOR: C.Ghelfi
@DATE  : 16/09/2015
"""

import argparse

from katelibs.database import TEquipment, TNet, TSerial, TLocation, TEquipType, connection


def get_eqpt_type_name(tabEqptType, ident):
    """ tbd """
    return tabEqptType.objects.get(id_type=ident).name


def get_eqpt_location(t_location, ident):
    """ tbd """
    l_row  = t_location.objects.get(id_location=ident).row
    l_rack = t_location.objects.get(id_location=ident).rack
    l_pos  = t_location.objects.get(id_location=ident).pos
    if l_row is None:
        return 'NULL'
    else:
        return '{}-{}/{}'.format(l_row, l_rack, l_pos)


def get_eqpt_ip(list_ip, ident):
    """ tbd """
    for _row in list_ip:
        if _row.t_equipment_id_equipment:
            if _row.t_equipment_id_equipment.id_equipment == ident:
                return _row.ip

    return str(None)


def get_eqpt_serial(list_ser, ident):
    """ tbd """
    msg = ""
    for _row in list_ser:
        if _row.t_equipment_id_equipment.id_equipment == ident:
            msg = "{:s} {:d} <-> {:s}:{:d} ".format(msg, _row.slot, _row.t_net_id_ip.ip, _row.port)

    return msg


def get_board_type_list():
    """tbd  """
    cursor = connection.cursor()
    query = "SELECT id_board_type,name FROM T_BOARD_TYPE"
    cursor.execute(query)

    result = cursor.fetchall()

    board_type_list = {}

    if len(result) > 0:
        for _row in result:
            board_type_list[_row[0]] = _row[1]

    return board_type_list


def get_eqpt_boards(eqpt_id, eqpt_type, board_type_list):
    """ tbd """
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
        for _row in result:
            slot = _row[1]
            board_name = board_type_list[_row[0]]

            if list_boards is None:
                list_boards = "{}:{}".format(slot, board_name)
            else:
                list_boards = "{} {}:{}".format(list_boards, slot, board_name)

    return list_boards


def get_new_location(eqpt_id):
    """ tbd """
    cursor = connection.cursor()
    query = "SELECT id_loc_new FROM T_EQUIPMENT WHERE id_equipment='{}'".format(eqpt_id)
    cursor.execute(query)

    result = cursor.fetchall()

    return result[0][0]



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--serials", help="get serials info", action="store_true")
    parser.add_argument("--boards", help="get boards info", action="store_true")
    parser.add_argument("--newpos", help="get new location info", action="store_true")
    args = parser.parse_args()

    list_ip  = TNet.objects.all()
    list_ser = TSerial.objects.all()
    board_type_list = get_board_type_list()

    t_location = TLocation
    tabEqptType = TEquipType

    for row in TEquipment.objects.all():
        eType = get_eqpt_type_name(tabEqptType, row.t_equip_type_id_type.id_type)
        eLoc  = get_eqpt_location(t_location, row.t_location_id_location.id_location)
        eIP   = get_eqpt_ip(list_ip, row.id_equipment)

        if args.newpos:
            new_loc_id = get_new_location(row.id_equipment)
            if new_loc_id is not None:
                eLoc_new = get_eqpt_location(t_location, new_loc_id)
            else:
                eLoc_new = "NULL"
            location = "{:10s} [{:10s}]".format(eLoc, eLoc_new)
        else:
            location = "{:10s}".format(eLoc)

        if args.serials:
            eSer = get_eqpt_serial(list_ser, row.id_equipment)
            res='{:5s} {:12s} {} {:20s} {:20s} {:16} {:s}'.format(str(row.id_equipment),
                                                                  eType,
                                                                  location,
                                                                  str(row.name),
                                                                  eIP,
                                                                  str(row.owner),
                                                                  eSer
                                                                 )
        elif args.boards:
            board_list = get_eqpt_boards(row.id_equipment, eType, board_type_list)
            if board_list is None:
                board_list = ""
            else:
                board_list = "[{}]".format(board_list)

            res='{:5s} {:12s} {} {:20s} {:20s} {:16} {}'.format(str(row.id_equipment),
                                                                eType,
                                                                location,
                                                                str(row.name),
                                                                eIP,
                                                                str(row.owner),
                                                                board_list
                                                               )
        else:
            res='{:5s} {:12s} {} {:20s} {:20s} {:16}'.format(str(row.id_equipment),
                                                             eType,
                                                             location,
                                                             str(row.name),
                                                             eIP,
                                                             str(row.owner)
                                                            )
        print(res)
