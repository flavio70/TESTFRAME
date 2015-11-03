#!/usr/bin/env python  

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


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--all", help="get full info", action="store_true")
    args = parser.parse_args()

    allIP  = TNet.objects.all()
    allSer = TSerial.objects.all()

    tabLocation = TLocation
    tabEqptType = TEquipType

    if True:
        for r in TEquipment.objects.all():
            eType = getEqptTypeName(tabEqptType, r.t_equip_type_id_type.id_type)
            eLoc  = getEqptLocation(tabLocation, r.t_location_id_location.id_location)
            eIP   = getEqptIP(allIP, r.id_equipment)
            if args.all:
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
    else:
        if True:
            for r in TEquipment.objects.filter(1==F(TEquipment__T_EQUIP_TYPE_id_type)):
                print(r.name)
        else:
            tt = TEquipType
            for r in tt.objects.all().order_by('name'):
                print(r.name)
