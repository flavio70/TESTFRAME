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

from katelibs.kexception import KUserException, KFrameException
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
        self.trc_inf(run_section + ' Skipped\n')
        self.kenvironment.krepo.add_skipped(None, run_section, '0', run_section + " Skipped by User", run_section + " Skipped by User")


    def init(self):
        '''
        Main class constructor
        '''
        self.trc_inf('\nInitializing {:s} environment ...'.format(self.kenvironment.get_test_file_name()))
        self.trc_inf('DONE \n')


    def close(self):
        '''
        function used to finalize test execution
        '''
        self.trc_inf('\nFinalizing  ...')
        self.kenvironment.clean_up()
        self.trc_inf('DONE \n')


    def dut_setup(self):
        '''
        Empty dut setup common function
        should be overwritten by user implementation
        '''
        self.trc_inf('Running empty DUT SetUp...')


    def test_setup(self):
        '''
        Empty test setup common function
        should be overwritten by user implementation
        '''
        self.trc_inf('Running empty test Setup...')


    def test_body(self):
        '''
        Empty test body common function
        should be overwritten by user implementation
        '''
        self.trc_inf('Running empty Main Test...')


    def test_cleanup(self):
        '''
        Empty test cleanup common function
        should be overwritten by user implementation
        '''
        self.trc_inf('Running empty Test cleanUp...')


    def dut_cleanup(self):
        '''
        Empty dut cleanup common function
        should be overwritten by user implementation
        '''
        self.trc_inf('Running empty DUT cleanUp...')


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

        try:
            self.init()
            self.run_test(args)
            self.close()

        except KFrameException as eee:
            msg = "KATE FRAMEWORK EXCEPTION CAUGHT - {}".format(eee)
            self.trc_err(msg)

        except KUserException as eee:
            msg = "KATE USER EXCEPTION CAUGHT - {}".format(eee)
            self.trc_err(msg)
            self.close()

        except Exception as eee:
            msg = "GENERIC EXCEPTION CAUGHT - {}".format(eee)
            self.trc_err(msg)
            self.close()


    def run_test(self, args):
        '''
        test sections run
        '''
        self.trc_inf('\n----Main Test flow execution----\n')
        if (args.DUTSet == False) and (args.testSet == False) and (args.testBody == False) and (args.testClean == False) and (args.DUTClean == False):
            args.DUTSet = True
            args.testSet = True
            args.testBody = True
            args.testClean = True
            args.DUTClean = True

        self.trc_inf(str(args))

        self.dut_setup() if args.DUTSet else self.skip_section('DUT Setup')
        self.test_setup() if args.testSet else self.skip_section('test Setup')
        self.test_body() if args.testBody else self.skip_section('test Body')
        self.test_cleanup() if args.testClean else self.skip_section('test Clean Up')
        self.dut_cleanup() if args.DUTClean else self.skip_section('DUT Cleanup')


    def start_tps_block(self, dut_id, tps_area, tps_name):
        '''
        Start an official block containg all code related to aspecific TPS (Test Procedure)
        calling this function into testcase object will generate a specific XML report file for each TPSName provided
        '''
        self.kenvironment.krepo.start_tps_block(dut_id, tps_area, tps_name)


    def stop_tps_block(self, dut_id, tps_area, tps_name):
        """ 
        Stop the block containing the code related to the specific TPS (test Procedure)
        This function will terminate the specific XML report file related to TPSName test id
        """ 
        self.kenvironment.krepo.stop_tps_block(dut_id, tps_area, tps_name)


    def trc_dbg(self, msg):
        """ Perform a debug message trace. The supplied message will be logged with a time stamp
            and module, row and function/method
        """
        self.kenvironment.ktrc.k_tracer_debug(msg)


    def trc_inf(self, msg):
        """ Perform an information message trace. The supplied message will be logged with a time stamp
            and module, row and function/method
        """
        self.kenvironment.ktrc.k_tracer_info(msg)


    def trc_err(self, msg):
        """ Perform an error message trace. The supplied message will be logged with a time stamp
            and module, row and function/method
        """
        self.kenvironment.ktrc.k_tracer_error(msg)
