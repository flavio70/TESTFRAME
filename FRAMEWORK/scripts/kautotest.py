#!/usr/bin/env python
"""
Module used to drive Jenkins jobs

@Script: kautotest.py
@AUTHOR: F.Ippolito
@DATE  : 02/09/2015
"""
import os
import argparse
from git import Repo
from katelibs.kunit import Kunit

JenkinsHome = os.environ['JENKINS_HOME']
JobWorkspace = os.environ['WORKSPACE']

def printFRMWRKdata():
    """
    print Framework environemnt data into Kunit format
    """
    try:
        myRepo = Repo(JenkinsHome + '/KateRepo')
        git = myRepo.git
        frmwrkVersionLong = git.log('--decorate', '-1') 
    except:
        frmwrkVersionLong = 'Git infos not available' 
    try:
        frmwrkVersionShort = git.describe('--tags')
    except:
        frmwrkVersionShort = 'tags Not Available'
    print('K@TE Framework Commit used for test: ' + frmwrkVersionLong + '/n')
    print('API version: ' + frmwrkVersionShort)
    xmlReport = JobWorkspace + '/test-reports/EnvSettings.FrameworkAPI.XML'
    r = Kunit(xmlReport)
    r.frame_open()
    r.start_time()
    r.add_success(None, "KATE API: " + frmwrkVersionShort, None, frmwrkVersionLong)
    r.frame_close()


def main():
    """
    Main loop
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("inputSuite", help="The suite test file to be processed")
    args = parser.parse_args()
    print('Processing suite; ', args.inputSuite)
    printFRMWRKdata()
    with open(args.inputSuite) as f:
        for line in f:
            os.system(line)
            #subprocess.call(line, shell=True)

    print('End of execution')


if __name__ == "__main__":
    main()
