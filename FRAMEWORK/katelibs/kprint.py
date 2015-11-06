#!/usr/bin/env python
"""
###############################################################################
# MODULE: kwrit.py
#
# AUTHOR: F.Ippolito
# DATE  : 06/11/2015
#
###############################################################################

Some useful function to print ANSI COLORED Output

"""
class bcolors:
	"""
	this class implements the ANSI COLOR escape codes
	"""
	ONBLUE = '\033[34m\n'
	OKGREEN = '\033[32m\n'
	WARNING = '\033[33m\n'
	FAIL = '\033[31m\n'
	ENDC = '\033[0m\n'
	BOLD = '\033[1m\n'
	UNDERLINE = '\033[4m\n'

def kprint_warning(str):
	"""
	print str in warning format
	"""
	print(bcolors.WARNING + str + bcolors.ENDC)

def kprint_fail(str):
	"""
	print str in fail format
	"""
	print(bcolors.FAIL + str + bcolors.ENDC)

def kprint_info(str):
	"""
	print str in info format
	"""
	print(bcolors.ONBLUE + str + bcolors.ENDC)

def kprint_green(str):
	"""
	print str in okgreen format
	"""
	print(bcolors.OKGREEN + str + bcolors.ENDC)