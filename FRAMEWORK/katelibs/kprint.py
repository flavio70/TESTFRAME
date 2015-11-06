class bcolors:
	ONBLUE = '\033[34m\n'
	OKGREEN = '\033[32m\n'
	WARNING = '\033[33m\n'
	FAIL = '\033[31m\n'
	ENDC = '\033[0m\n'
	BOLD = '\033[1m\n'
	UNDERLINE = '\033[4m\n'

def kprint_warning(str):
	print(bcolors.WARNING + str + bcolors.ENDC)

def kprint_fail(str):
	print(bcolors.FAIL + str + bcolors.ENDC)

def kprint_info(str):
	print(bcolors.ONBLUE + str + bcolors.ENDC)

def kprint_green(str):
	print(bcolors.OKGREEN + str + bcolors.ENDC)