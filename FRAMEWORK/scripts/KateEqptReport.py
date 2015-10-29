#!/usr/bin/env python  

import os

from database import *


def getEqptTypeName(n):
    tabEqptType = TEquipType
    return tabEqptType.objects.get(id_type=n).name

def getEqptLocation(n):
    tabLocation = TLocation
    lRow    = tabLocation.objects.get(id_location=n).row
    lRack   = tabLocation.objects.get(id_location=n).rack
    lPos    = tabLocation.objects.get(id_location=n).pos
    return '{:s}-{:d}/{:d}'.format(lRow, lRack, lPos)

def getEqptIP(n):
    tabIP = TNet

    for r in tabIP.objects.all():
        if r.t_equipment_id_equipment:
            if r.t_equipment_id_equipment.id_equipment == n:
                return r.ip

    return str(None)


if __name__ == "__main__":

    tabEqpt = TEquipment


    for r in tabEqpt.objects.all():
        eType = getEqptTypeName(r.t_equip_type_id_type.id_type)
        eLoc  = getEqptLocation(r.t_location_id_location.id_location)
        eIP   = getEqptIP(r.id_equipment)
        res='{:5s} {:10s} {:10s} {:20s} {:20s} {:20s}'.format(
                str(r.id_equipment),
                eType,
                eLoc,
                str(r.name),
                eIP,
                str(r.owner)
            )
        print(res)
