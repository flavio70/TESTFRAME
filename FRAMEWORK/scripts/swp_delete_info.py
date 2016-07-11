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

    query = "DELETE FROM T_PACKAGES WHERE author='{}' AND ts_build='{}'".format(args.author[0], args.tsbuild[0])

    print(query)
    cursor.execute(query)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--author",  nargs=1, required=True, help="author")
    parser.add_argument("--tsbuild", nargs=1, required=True, help="build timestamp")
    args = parser.parse_args()

    print(args)

    delete_swp_info(args)
