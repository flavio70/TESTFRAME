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
from django.db import connection
from katelibs.kprint import *

# Getting Django Setting (settings.py) and setting basic configuration for DJANGO DB connection
# settings.py file must be in ./DB_API_CONF folder
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "katelibs.DB_API_CONF.settings")

#import all objects defined in models.py
#models.py module must be placed in ./DB_API_LIB folder
from katelibs.DB_API_LIB.models import *



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
	'''
	try to lock the node_list changing the insue value
	'''
	res=False
	try:
		localtab = TEquipment
		if len(node_list) == len(localtab.objects.filter(id_equipment__in=node_list, inuse=0)):
			#in this case all nodes in the list ar free and can be locked
			localtab.objects.filter(id_equipment__in=node_list).update(inuse=1)
			res=True
			kprint_green('Nodes '+ str(node_list) + ' locked!')
		else:
			#in this case at least one node is used by others and the node_list cannot be locked
			kprint_warning('WARNING!! Nodes '+ str(node_list) + ' CANNOT be locked! One or more node already in use.')
		return res
	except Exception as eee:
		kprint_fail(str(eee))
		return res


def unlock_eqpt_nodes(node_list):
	'''
	try to unlock the node_list changing the insue value
	'''
	res=False
	try:
		localtab = TEquipment 
		localtab.objects.filter(id_equipment__in=node_list).update(inuse=0)
		res=True
		kprint_green('Nodes '+ str(node_list) + ' unlocked!')
		return res
	except Exception as eee:
		kprint_fail(str(eee))
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

