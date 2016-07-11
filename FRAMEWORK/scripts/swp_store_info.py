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


def check_sw_rel(args):
    if args.swrel is None:
        return False

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


def check_product(args):
    if args.prod is None:
        return False

    cursor = connection.cursor()

    query = ' '.join( ( "SELECT *",
                        "FROM   T_PROD",
                        "WHERE  product='{}'".format(args.prod[0])) )
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


if __name__ == "__main__":

    l_arch = ['gccpp', 'gccwrp', 'gccli']

    parser = argparse.ArgumentParser()
    parser.add_argument("--prod",    nargs=1, required=True, help="product")
    parser.add_argument("--swrel",   nargs=1, required=True, help="software release")
    parser.add_argument("--arch",    nargs=1, required=True, help="architecture", choices=l_arch)
    parser.add_argument("--author",  nargs=1, required=True, help="author")
    parser.add_argument("--labref",  nargs=1, required=True, help="reference label")
    parser.add_argument("--tsbuild", nargs=1, required=True, help="build timestamp")
    parser.add_argument("--ref",     nargs=1, required=True, help="swp reference")
    args = parser.parse_args()

    print(args)

    if not check_sw_rel(args):
        print("Invalid Software Release [{}]".format(args.swrel[0]))
        sys.exit(10)

    if not check_product(args):
        print("Invalid Product [{}]".format(args.prod[0]))
        sys.exit(10)

    print(args)

    store_swp_info(args)
