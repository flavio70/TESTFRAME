#!/usr/bin/env python
"""
@MODULE: testcase.py
@AUTHOR: F.Ippolito
@DATE  : 11/09/2015
@Description: This module is used for general test case implementation.
    Provides test class definition and common functions
"""
from katelibs.kunit import Kunit
import os
import json
import argparse


class TestCase(object):
	
	'''
	TestCase General class definition
	'''
	__testdir = None  # py file Directory
	fn = None # py file name
	__xml_report = None # Py file XML Report File
	__prs_file = None # file containing the json preset for Test
	prs_values = None # Structure containing the parsed json Test parameters
	report = None # contains reference to the current kunit file report object

	def __init__(self, filename):
		
		self.__testdir, self.fn = os.path.split(os.path.abspath(filename))
		self.__xml_report = self.__testdir + '/../test-reports/'+ os.path.splitext(self.fn)[0] + '._Main.py'
		self.__prs_file = open(os.path.abspath(filename)+ '.prs')
		self.prs_values = json.load(self.__prs_file)
		self.report = Kunit(self.__xml_report)

	def get_prs(self):
		return self.prs_values

	def print_prs(self):
		'''
		Print out the json parameters
		'''
		print('\ninput valid Keys for ', self.fn, ' : \n')
		for key, values in self.prs_values.items():
			print('Key: ' + key + ' with current value: ' + values)
		#for key, values in self.prs_values.items():
		#	print(key + '=' + values)
		print('\n-- End of input valid keys -- \n')

	def skip_section(self, run_section):
		'''
		function used t skip test section
		'''
		print(run_section + ' Skipped\n')
		self.report.add_skipped(None, run_section, '0', run_section + " Skipped by User", run_section + " Skipped by User")

	def init(self):
		'''
		Main class constructor
		'''
		print('\nInitializing ', self.fn, ' environment ...')
		self.print_prs()
		print('DONE \n')

	def close(self):
		'''
		function used to finalize test execution
		'''
		print('\nFinalizing ', self.fn, ' ...')
		self.report.frame_close()
		print('DONE \n')

	def dut_setup(self):
		'''
		Empty dut setup common function
		should be overwritten by user implementation
		'''
		print('Running empty DUT SetUp...')

	def test_setup(self):
		'''
		Empty test setup common function
		should be overwritten by user implementation
		'''
		print('Running empty test Setup...')

	def test_body(self):
		'''
		Empty test body common function
		should be overwritten by user implementation
		'''
		print('Running empty Main Test...')

	def test_cleanup(self):
		'''
		Empty test cleanup common function
		should be overwritten by user implementation
		'''
		print('Running empty Test cleanUp...')

	def dut_cleanup(self):
		'''
		Empty dut cleanup common function
		should be overwritten by user implementation
		'''
		print('Running empty DUT cleanUp...')

	def run(self):
		'''
		Main run etry point
		test parameter parser and initializaton
		'''
		parser = argparse.ArgumentParser()
		parser.add_argument("--DUTSet", help="Run the DUTs SetUp", action="store_true")
		parser.add_argument("--testSet", help="Run the Test SetUp", action="store_true")
		parser.add_argument("--testBody", help="Run the Test Main Body", action="store_true")
		parser.add_argument("--testClean", help="Run the Test Clean Up", action="store_true")
		parser.add_argument("--DUTClean", help="Run the DUTs Clean Up", action="store_true")
		args = parser.parse_args()
		self.init()
		self.run_test(args)
		self.close()

	def run_test(self, args):
		'''
		test sections run
		'''
		print('\n----Main Test flow execution----\n')
		if (args.DUTSet == False) and (args.testSet == False) and (args.testBody == False) and (args.testClean == False) and (args.DUTClean == False):
			args.DUTSet = True
			args.testSet = True
			args.testBody = True
			args.testClean = True
			args.DUTClean = True
		print(args)
		self.dut_setup() if args.DUTSet else self.skip_section('DUT Setup')
		self.test_setup() if args.testSet else self.skip_section('test Setup')
		self.test_body() if args.testBody else self.skip_section('test Body')
		self.test_cleanup() if args.testClean else self.skip_section('test Clean Up')
		self.dut_cleanup() if args.DUTClean else self.skip_section('DUT Cleanup')

