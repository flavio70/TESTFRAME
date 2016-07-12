#!/usr/bin/env python  
"""
Script used to store 1850TSS SWP info to KATE DB

@Script: swp_store_info.py
@AUTHOR: C.Ghelfi
@DATE  : 10/02/2016
"""

import sys
import argparse

from katelibs.database  import *
from django.db          import connection


def get_product():
    cursor = connection.cursor()

    query = "SELECT product FROM T_PROD"

    cursor.execute(query)

    result = cursor.fetchall()

    l = []

    for i in result:
        l.append(i[0])

    return l


def check_sw_rel(args):
    if args.swrel is None:
        return False

    cursor = connection.cursor()

    query = "SELECT * FROM T_SW_REL WHERE sw_rel_name='{}'".format(args.swrel[0])

    cursor.execute(query)

    result = cursor.fetchall()

    if len(result) == 1:
        args.swrel = result[0][0]
        return True

    return False


def check_product(args):
    if args.prod is None:
        return False

    cursor = connection.cursor()

    query = "SELECT * FROM T_PROD WHERE product='{}'".format(args.prod[0])

    cursor.execute(query)

    result = cursor.fetchall()

    if len(result) == 1:
        args.prod = result[0][0]
        return True

    return False


def store_swp_info(args):
    cursor = connection.cursor()

    query = ' '.join( ( "INSERT INTO T_PACKAGES",
                        "(",
                            "T_PROD_id_prod,",
                            "T_SW_REL_id_sw_rel,",
                            "label_ref,",
                            "arch,",
                            "author,",
                            "ts_build,",
                            "reference",
                        ")",
                        "VALUES",
                        "('{}','{}','{}','{}','{}','{}','{}')".format(args.prod,
                                                                      args.swrel,
                                                                      args.labref[0],
                                                                      args.arch[0],
                                                                      args.author[0],
                                                                      args.tsbuild[0],
                                                                      args.ref[0])
                    ) )

    cursor.execute(query)

    print("SWP for [{}] and [{}] CORRECTLY STORED on Kate's DB".format(args.arch[0], args.labref[0]))


if __name__ == "__main__":

    l_prod = get_product()
    l_arch = ['gccpp', 'gccwrp', 'gccli']
    the_desc = """ Create a new SWP information record on Kate DB.
               """

    parser = argparse.ArgumentParser(description=the_desc)
    parser.add_argument("--arch",    nargs=1, required=True, help="architecture", choices=l_arch)
    parser.add_argument("--prod",    nargs=1, required=True, help="product", choices=l_prod)
    parser.add_argument("--author",  nargs=1, required=True, help="author")
    parser.add_argument("--swrel",   nargs=1, required=True, help="software release")
    parser.add_argument("--labref",  nargs=1, required=True, help="reference label (like V7.20.00-0499)")
    parser.add_argument("--tsbuild", nargs=1, required=True, help="build timestamp")
    parser.add_argument("--ref",     nargs=1, required=True, help="swp reference")
    args = parser.parse_args()

    if not check_sw_rel(args):
        print("Invalid Software Release [{}]".format(args.swrel[0]))
        sys.exit(10)

    if not check_product(args):
        print("Invalid Product [{}]".format(args.prod[0]))
        sys.exit(10)

    store_swp_info(args)

    sys.exit(0)
