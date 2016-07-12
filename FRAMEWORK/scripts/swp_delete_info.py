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

    query = "DELETE FROM T_PACKAGES WHERE author='{}' AND ts_build='{}' AND label_ref='%s' AND arch='%s'".format(args.author[0], args.tsbuild[0], args.labref[0], args.arch[0])

    print(query)
    cursor.execute(query)


if __name__ == "__main__":

    l_arch = ['gccpp', 'gccwrp', 'gccli']
    the_desc = """ Delete a specified SWP from Kate DB.
                   The package must be identified by Architeture, Label Reference, Author and Build Timestamp
               """

    parser = argparse.ArgumentParser(description=the_desc)
    parser.add_argument("--arch",    nargs=1, required=True, help="architecture", choices=l_arch)
    parser.add_argument("--labref",  nargs=1, required=True, help="reference label (like V7.20.00-0499)")
    parser.add_argument("--author",  nargs=1, required=True, help="author")
    parser.add_argument("--tsbuild", nargs=1, required=True, help="build timestamp")
    args = parser.parse_args()

    delete_swp_info(args)
