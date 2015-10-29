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


import os

# Getting Django Setting (settings.py) and setting basic configuration for DJANGO DB connection
# settings.py file must be in ./DB_API_CONF folder
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DB_API_CONF.settings")

#import all objects defined in models.py
#models.py module must be placed in ./DB_API_LIB folder
from DB_API_LIB.models import *




#global a
#a=TTest
#print(TTest.objects.all())
#print(a)
