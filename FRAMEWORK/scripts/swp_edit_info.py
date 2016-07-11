#!/usr/bin/env python  
"""
Script used to modify 1850TSS SWP info on KATE DB

@Script: swp__info.py
@AUTHOR: C.Ghelfi
@DATE  : 10/02/2016
"""

import os
import sys
import argparse

from katelibs.plugin_bm import Plugin1850BM
from katelibs.database  import *
from django.db          import connection


def check_lab_ref(args):
    if args.labref is None:
        return False

    cursor = connection.cursor()

    query = ' '.join( ( "SELECT *",
                        "FROM   T_PACKAGES",
                        "WHERE  label_ref='{}'".format(args.labref[0])) )
    cursor.execute(query)

    result = cursor.fetchall()

    if len(result) != 0:
        return True

    return False


def get_swp_id(args):
    if args.labref is None:
        return False, None

    if args.arch is None:
        return False, None

    cursor = connection.cursor()

    query = ' '.join( ( "SELECT *",
                        "FROM   T_PACKAGES",
                        "WHERE  label_ref='{}'".format(args.labref[0]),
                        "  AND  arch='{}'".format(args.arch[0])) )
    cursor.execute(query)

    result = cursor.fetchall()

    if len(result) == 1:
        return True, result[0][0]

    return False, None


def update_label_swp(swp_id, label):
    cursor = connection.cursor()
    query = "UPDATE T_PACKAGES SET label_swp='{}' WHERE id_pack='{}'".format(label, swp_id)
    cursor.execute(query)


def update_ts_devel(swp_id, timestamp):
    cursor = connection.cursor()
    query = ' '.join( ( "UPDATE T_PACKAGES",
                        "  SET  ts_devel='{}'".format(timestamp),
                        "WHERE  id_pack='{}'".format(swp_id),
                        "  AND  `ts_build` <= '{}'".format(timestamp)) )
    cursor.execute(query)

    return (cursor.rowcount == 1)


def update_ts_valid(swp_id, timestamp):
    cursor = connection.cursor()
    query = ' '.join( ( "UPDATE T_PACKAGES",
                        "  SET  ts_valid='{}'".format(timestamp),
                        "WHERE  id_pack='{}'".format(swp_id),
                        "  AND  `ts_devel` <= '{}'".format(timestamp)) )
    cursor.execute(query)

    return (cursor.rowcount == 1)


def update_ts_valid(swp_id, timestamp):
    cursor = connection.cursor()
    query = ' '.join( ( "UPDATE T_PACKAGES",
                        "  SET  ts_final='{}'".format(timestamp),
                        "WHERE  id_pack='{}'".format(swp_id),
                        "  AND  `ts_valid` <= '{}'".format(timestamp)) )
    cursor.execute(query)

    return (cursor.rowcount == 1)


def update_swp_info(swp_id, args):
    if args.labswp is not None:
        update_label_swp(swp_id, args.labswp[0])

    if args.tsdevel is not None:
        if not update_ts_devel(swp_id, args.tsdevel[0]):
            print("Invalid date")


if __name__ == "__main__":

    l_arch = ['gccpp', 'gccwrp', 'gccli']

    parser = argparse.ArgumentParser()
    parser.add_argument("--arch",    nargs=1, required=True,  help="architecture", choices=l_arch)
    parser.add_argument("--labref",  nargs=1, required=True,  help="reference label")
    parser.add_argument("--labswp",  nargs=1, required=False, help="release label")
    parser.add_argument("--tsdevel", nargs=1, required=False, help="release timestamp")
    args = parser.parse_args()

    print(args)

    res,swp_id = get_swp_id(args)
    if not res:
        print("Package for [{}] and [{}] not found.".format(args.arch[0], args.labref[0]))
        sys.exit(10)

    update_swp_info(swp_id, args)
