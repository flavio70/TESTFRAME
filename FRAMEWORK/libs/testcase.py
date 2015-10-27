#!/usr/bin/env python
"""
@MODULE: testcase.py
@AUTHOR: F.Ippolito
@DATE  : 11/09/2015
@Description: This module is used for general test case implementation.
    Provides test class definition and common functions
"""
from KateLibs.kunit import Kunit
import os
import json
import argparse


class TestCase(object):
    '''
    TestCase General class definition
    '''
    __TestDir = None  # py file Directory
    fn = None # py file name
    __xmlReport = None # Py file XML Report File
    __prsFile = None # file containing the json preset for Test
    prsValues = None # Structure containing the parsed json Test parameters
    report = None # contains reference to the current kunit file report object

    def __init__(self, filename):
        self.__TestDir, self.fn = os.path.split(os.path.abspath(filename))
        self.__xmlReport = self.__TestDir + '/../test-reports/'+ os.path.splitext(self.fn)[0] + '._Main.py'
        self.__prsFile = open(os.path.abspath(filename)+ '.prs')
        self.prsValues = json.load(self.__prsFile)
        self.report = Kunit(self.__xmlReport)

    def printPrs(self):
        '''
        Print out the json parameters
        '''
        print('\ninput values for ', self.fn, ' : \n')
        for key, values in self.prsValues.items():
            print(key + '=' + values)
        print('\n-- End of values -- \n')

    def skipSection(self, runSection):
        '''
        function used t skip test section
        '''
        print(runSection + ' Skipped\n')
        self.report.addSkipped(None, runSection, '0', runSection + " Skipped by User", runSection + " Skipped by User")

    def init(self):
        '''
        Main class constructor
        '''
        print('\nInitializing ', self.fn, ' environment ...')
        self.printPrs()
        self.report.frameOpen()
        print('DONE \n')

    def close(self):
        '''
        function used to finalize test execution
        '''
        print('\nFinalizing ', self.fn, ' ...')
        self.report.frameClose()
        print('DONE \n')

    def DUTSetUp(self):
        '''
        Empty dut setup common function
        should be overwritten by user implementation
        '''
        print('Running empty DUT SetUp...')

    def testSetUp(self):
        '''
        Empty test setup common function
        should be overwritten by user implementation
        '''
        print('Running empty test Setup...')

    def testBody(self):
        '''
        Empty test body common function
        should be overwritten by user implementation
        '''
        print('Running empty Main Test...')

    def testCleanUp(self):
        '''
        Empty test cleanup common function
        should be overwritten by user implementation
        '''
        print('Running empty Test cleanUp...')

    def DUTCleanUp(self):
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
        self.runTest(args)
        self.close()

    def runTest(self, args):
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
        self.DUTSetUp() if args.DUTSet else self.skipSection('DUT Setup')
        self.testSetUp() if args.testSet else self.skipSection('test Setup')
        self.testBody() if args.testBody else self.skipSection('test Body')
        self.testCleanUp() if args.testClean else self.skipSection('test Clean Up')
        self.DUTCleanUp() if args.DUTClean else self.skipSection('DUT Cleanup')
