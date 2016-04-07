#!/usr/bin/env python
"""
Module used to drive Jenkins jobs

@Script: kautotest.py
@AUTHOR: F.Ippolito
@DATE  : 02/09/2015
"""
import os, sys, time
import json, glob
import argparse
import signal
from git import Repo
from katelibs.kunit import Kunit
from katelibs.database import *
from katelibs.kprint import *
from django.db import connection


gRunId = ''

def handler_signal(signum, stack):
		print ('Received:%s SIGTERM Signal/n...Aborting K@TE suite execution...'%signum)
		set_RunTime_status(gRunId, 'ABORTED')
		print('...Done!!')


def printFRMWRKdata(JenkinsHome, JobWorkspace):
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
	xmlReportPath = JobWorkspace + '/test-reports'
	xmlReportFile = 'EnvSettings.FrameworkAPI.XML'
	r = Kunit(xmlReportPath,xmlReportFile)
	r.start_time()
	r.add_success(None, "KATE API: " + frmwrkVersionShort, None, frmwrkVersionLong)
	r.frame_close()

def get_file_bytype(file_path,file_type):
	'''
	get al files from a folder with a selected type
	'''
	_res=[file for file in glob.glob(os.path.join(file_path, '*.' + file_type))]
	return _res

def get_job_nodelist(file_list):
	'''
	get the K@TE node list from presets
	file_list: [Names of prs files]
	'''
	res = []
	for file in file_list:
		_file_descr = open(os.path.abspath(file))	
		_prs_values = json.load(_file_descr)
		_file_descr.close()
		for key, values in _prs_values.items():
			if '_' not in key and values not in res: res.append(values)
	return res

def guaranted_flow(args):
	"""
	main flow control in case of policy = GUA
	in this case all suite resources shall be locked before suite execution and relased at the end
	if one or more resource are not available the entire suite will be stopped
	"""
	prs_list = get_file_bytype(args.JobWorkspace,'prs')
	#node_list = get_job_nodelist(prs_list)
	#kprint_info('Getting Job Node indexes... '+ str(node_list))
	#eqpt_list = get_eqpt_nodes(node_list)	
	#kprint_info('Getting EQPT Node indexes... '+ str(eqpt_list))
	#kprint_info('Locking EQPT Items...')
	#if not lock_eqpt_nodes(eqpt_list): sys.exit('Exiting ... \nNodes cannot be locked for execution')
	err_count = 0
	run_count = 0
	try:
		#setting runtime entry to running 
		if args.DBMode : 
			set_RunTime_status(args.KateRunId, 'RUNNING')
			set_RunTime_job_iteration(args.KateRunId, args.jobBuildN)
		else:
			args.KateRunId = new_RunTime_entry(args.jobName, args.jobBuildN, args.UserId, 'RUNNING')
			print ('new RunId : ' + str(args.KateRunId))

		with open(args.inputSuite) as f:
			for line in f:
				run_count +=1
				_a=os.system(line)
				#time.sleep(60)
				if _a != 0:
					err_count +=1 
					set_RunTime_status(args.KateRunId, 'FAILING')
					set_RunTime_errCount(args.KateRunId, err_count)
					#time.sleep(60)
				set_RunTime_runCount(args.KateRunId, run_count)
		set_RunTime_status(args.KateRunId, 'FAILED') if err_count > 0 else set_RunTime_status(args.KateRunId, 'COMPLETED')
		#unlock_eqpt_nodes(eqpt_list)
		print('End of execution')

	except Exception as eee:
		print('Exception Detected: ' + str(eee))
		#unlock_eqpt_nodes(eqpt_list)
		set_RunTime_status(args.KateRunId, 'ABORTED')

def besteffort_flow(args):
	"""
	Main flow control in case of policy = BE
	Only Tests with evailable resources will be executed, others will be skipped
	"""
	print('Exiting ... \nBest effort case not yet implemented')

def main():
	"""
	Main loop
	"""
	global gRunId
	parser = argparse.ArgumentParser()
	parser.add_argument("inputSuite", help="The suite test file to be processed")
	parser.add_argument("jobName", help="Jenkins Job Name", nargs='?', default='Local')
	parser.add_argument("jobBuildN", help="Jenkins Job Build Number", nargs='?', default=0)
	parser.add_argument("KateRunId", help="K@TE istance ID (filled automatically by K@TE interface)", nargs='?', default=None)
	parser.add_argument("--UserId", help="K@TE UserId", nargs='?', default='Local')
	parser.add_argument("--policy", help="K@TE suite policy", nargs='?', choices=['GUA','BE'], default='GUA')
	
	args = parser.parse_args()
	print(args)
	args.DBMode = False
	gRunId = args.KateRunId
	
	signal.signal(signal.SIGTERM, handler_signal)
 
	try:
		args.JenkinsHome = os.environ['JENKINS_HOME']
		args.JobWorkspace = os.environ['WORKSPACE']
		printFRMWRKdata(args.JenkinsHome, args.JobWorkspace)
	except Exception as e:
		print(str(e))
		#sys.exit('Exiting ... \nError getting os environment JENKINS Data')
		print('JENKINS ENV NOT DETECTED\nASSUME you are Calling me for DEBUG SCOPE...')
		args.JobWorkspace = input("Please enter equivalent workspace: ")
		args.JenkinsHome = ''
		print ('workspace set to ' + args.JobWorkspace)

	
	print('Checking K@TE DB RunTime Entries...')

	row_group=get_RunTime_table(args.KateRunId)
	print('Entries: '+ str(row_group))
	
	if row_group.exists(): args.DBMode =True
	print('K@TE Mode set to: ' + str(args.DBMode))
	print('Processing suite; ', args.inputSuite)

	functionName = {'GUA':guaranted_flow,
								 'BE':besteffort_flow,
								 }
	functionName[args.policy](args)

if __name__ == "__main__":
	main()
