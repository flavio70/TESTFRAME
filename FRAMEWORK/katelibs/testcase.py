#!/usr/bin/env python
"""
@MODULE: testcase.py
@AUTHOR: F.Ippolito
@DATE  : 11/09/2015
@Description: This module is used for general test case implementation.
    Provides test class definition and common functions
"""

import os
import argparse

from katelibs.kenviron import KEnvironment


class TestCase(object):
    '''
    TestCase General class definition
    '''

    def __init__(self, filename):
        """ Costructor of TestCase. Initialize kenvironment variable
            filename : the test file name
        """
        self.kenvironment = KEnvironment(testfilename=filename)


    def skip_section(self, run_section):
        '''
        function used t skip test section
        '''
        print(run_section + ' Skipped\n')
        self.kenvironment.krepo.add_skipped(None, run_section, '0', run_section + " Skipped by User", run_section + " Skipped by User")


    def init(self):
        '''
        Main class constructor
        '''
        print('\nInitializing ', self.kenvironment.get_test_file_name(), ' environment ...')
        print('DONE \n')


    def close(self):
        '''
        function used to finalize test execution
        '''
        print('\nFinalizing  ...')
        self.kenvironment.clean_up()
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
        Main run entry point
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
