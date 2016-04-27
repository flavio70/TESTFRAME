#!/usr/bin/env python
###############################################################################
# MODULE: database.py
# 
# AUTHOR: F.Ippolito
# DATE  : 08/09/2015
#
# this module imports the DB APIs from K@TE DJANGO Framework
# and provide all K@TE database's objects access and management to the K@TE test
# developer by using DJANGO DB access
###############################################################################


import os, ast
import django
from django.db import connection, transaction
from katelibs.kprint import *

# Getting Django Setting (settings.py) and setting basic configuration for DJANGO DB connection
# settings.py file must be in ./DB_API_CONF folder
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "katelibs.DB_API_CONF.settings")

django.setup()
#import all objects defined in models.py
#models.py module must be placed in ./DB_API_LIB folder
from katelibs.DB_API_LIB.models import *






def check_DB_Author(author):
    """ check the presence of author  in the right table """
    if author.strip() == '':return False
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT count(id) as myCount from auth_user WHERE username='"+author.strip()+"'")
        row=cursor.fetchone()
        if row[0]==0:
            return False
        else:
            return True
    except Exception as eee:
        print(str(eee))
        return False




def check_DB_Topology(topology):
    """ check the presence of topology  in the right table """
    if topology.strip() == '':return False
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT count(title) as myCount from T_TOPOLOGY WHERE id_topology='"+topology.strip()+"'")
        row=cursor.fetchone()
        if row[0]==0:
            return False
        else:
            return True
    except Exception as eee:
        print(str(eee))
        return False



def get_eqpt_nodes(node_list):
    '''
    get 'eqpt' type node id from a generic node list
    '''
    _querystr = None
    for node in node_list:
        if not _querystr:
            _querystr = 'id_equipment='+ str(node)
        else:
            _querystr = _querystr + ' or id_equipment='+ str(node)
    eqpt_list=[]
    try:    
        cursor = connection.cursor()
        cursor.execute("SELECT id_equipment FROM KATE.T_EQUIPMENT JOIN KATE.T_EQUIP_TYPE on (T_EQUIP_TYPE_id_type = id_type) WHERE family = 'EQPT' and (" + _querystr + ")")
        for myitem in cursor.fetchall():
            eqpt_list.append(myitem[0])
        return eqpt_list
    except Exception as eee:
        kprint_fail(str(eee))
        return eqpt_list


def lock_eqpt_nodes(node_list):
    """
    Try to lock the node_list changing the 'inUse' value
    The procedure fails (with no-change on DB) if almost a node is already locked
    """
    sql_node_list = ""
    for node_id in node_list:
        if sql_node_list == "":
            sql_node_list = "('{}'".format(node_id)
        else:
            sql_node_list = "{},'{}'".format(sql_node_list, node_id)
    sql_node_list = "{})".format(sql_node_list)

    res = False
    with transaction.atomic():
        cursor = connection.cursor()
        query = ' '.join( ( "SELECT id_equipment, inUse",
                            "FROM T_EQUIPMENT",
                            "WHERE id_equipment IN {}".format(sql_node_list),
                            "      AND inUse='1'" ) )
        cursor.execute(query)
        result = cursor.fetchall()
        if len(result) > 0:
            print("WARNING: following node(s) already locked:")
            for row in result:
                print(row[0])
        else:
            query = "UPDATE T_EQUIPMENT SET inUse='1' WHERE id_equipment IN {}".format(sql_node_list)
            cursor.execute(query)
            print("ALL REQUIRED NODE(S) LOCKED")
            res = True

    return res


def unlock_eqpt_nodes(node_list):
    """
    Unlock the equipment in node_list changing the inUse value
    """
    sql_node_list = ""
    for node_id in node_list:
        if sql_node_list == "":
            sql_node_list = "('{}'".format(node_id)
        else:
            sql_node_list = "{},'{}'".format(sql_node_list, node_id)
    sql_node_list = "{})".format(sql_node_list)

    res = False
    with transaction.atomic():
        cursor = connection.cursor()
        query = "UPDATE T_EQUIPMENT SET inUse='0' WHERE id_equipment IN {}".format(sql_node_list)
        cursor.execute(query)
        print("ALL REQUIRED NODE(S) UNLOCKED")
        res = True

    return res


def get_RunTime_table(ID):
    rowg=None
    try:    
        localtab  = TRuntime
        rowg = localtab.objects.filter(id_run=ID)
        return rowg
    except Exception as eee:
        kprint_fail(str(eee))
        return rowg

def set_RunTime_status(ID,field_value):
    try:    
        localtab  = TRuntime
        rowg = localtab.objects.filter(id_run=ID).update(status=field_value)
    except Exception as eee:
        kprint_fail(str(eee))
        return

def set_RunTime_job_iteration(ID,field_value):
    try:    
        localtab  = TRuntime
        rowg = localtab.objects.filter(id_run=ID).update(job_iteration=field_value)
    except Exception as eee:
        kprint_fail(str(eee))
        return

def new_RunTime_entry(jobname, buildnum, jksowner, newstatus):
    try:    
        newEntry = TRuntime(job_name=jobname, job_iteration=buildnum, owner=jksowner, status=newstatus, errcount=0, runcount=0)
        newEntry.save()
        return newEntry.id_run
    except Exception as eee:
        kprint_fail(str(eee))
        return 0

def set_RunTime_errCount(ID,field_value):
    try:    
        localtab  = TRuntime
        rowg = localtab.objects.filter(id_run=ID).update(errcount=field_value)
    except Exception as eee:
        kprint_fail(str(eee))
        return

def set_RunTime_runCount(ID,field_value):
    try:    
        localtab  = TRuntime
        rowg = localtab.objects.filter(id_run=ID).update(runcount=field_value)
    except Exception as eee:
        kprint_fail(str(eee))
        return

