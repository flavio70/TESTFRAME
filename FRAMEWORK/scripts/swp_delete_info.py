#!/usr/bin/env python
"""
Script used to delete 1850TSS SWP info to KATE DB

@Script: swp_store_info.py
@AUTHOR: C.Ghelfi
@DATE  : 11/07/2016
"""

import argparse

from katelibs.database  import *
from django.db          import connection


def delete_swp_info(args):
    cursor = connection.cursor()

    query = "DELETE FROM T_PACKAGES WHERE label_ref='{}' AND arch='{}'".format(args.labref[0], args.arch[0])

    print(query)
    cursor.execute(query)


if __name__ == "__main__":

    L_ARCH = ['gccpp', 'gccwrp', 'gccli']

    parser = argparse.ArgumentParser()
    parser.add_argument("--arch",    nargs=1, required=True, help="architecture", choices=L_ARCH)
    parser.add_argument("--labref",  nargs=1, required=True, help="reference label")
    args = parser.parse_args()

    print(args)

    delete_swp_info(args)
