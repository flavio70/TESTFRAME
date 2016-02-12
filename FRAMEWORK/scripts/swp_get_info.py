#!/usr/bin/env python  
"""
Script used to retrieve 1850TSS SWP info from KATE DB

@Script: swp_get_info.py
@AUTHOR: C.Ghelfi
@DATE  : 10/02/2016
"""

import os
import sys
import argparse

from katelibs.plugin_bm import Plugin1850BM
from katelibs.database  import *
from django.db          import connection


def get_swp_info(args):
    cursor = connection.cursor()

    query = "SELECT * FROM T_PACKAGES"

    clause = ""

    if args.swrel is not None:
        clause = clause + "T_SW_REL_id_sw_rel='{}'".format(args.swrel)

    if args.arch is not None:
        if clause != "":
            clause = clause + " AND "
        clause = clause + "arch='{}'".format(args.arch[0])

    if clause != "":
        query = query + " WHERE {}".format(clause)

    print(query)

    cursor.execute(query)
    for row in cursor.fetchall():
        print(row)


def check_swrel(args):
    if args.swrel is None:
        return True

    cursor = connection.cursor()

    query = ' '.join( ( "SELECT *",
                        "FROM   T_SW_REL",
                        "WHERE  sw_rel_name='{}'".format(args.swrel[0])) )
    cursor.execute(query)

    result = cursor.fetchall()

    if len(result) == 1:
        args.swrel = result[0][0]
        return True

    return False


def check_arch(args):
    if args.arch is None:
        return True

    return (args.arch[0] in ['gccwrp', 'gccpp', 'gccli'])


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--prod",   nargs=1, help="filter for product")
    parser.add_argument("--swrel",  nargs=1, help="filter for software release")
    parser.add_argument("--arch",   nargs=1, help="filter for architecture")
    parser.add_argument("--author", nargs=1, help="filter for author")
    parser.add_argument("--labref", nargs=1, help="filter for reference label")
    parser.add_argument("--labswp", nargs=1, help="filter for swp label")
    args = parser.parse_args()

    print(args)

    if not check_swrel(args):
        print("Invalid Software Release [{}]".format(args.swrel[0]))
        sys.exit(10)

    if not check_arch(args):
        print("Invalid architecture[{}]".format(args.arch[0]))
        sys.exit(10)

    get_swp_info(args)
