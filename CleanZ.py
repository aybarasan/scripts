import os
import sys
import subprocess
import glob
from optparse import OptionParser

options=None

# Traverse the given folder, running the given function on all files
# under it and it's subfolders that meet the condition
def ProcessFolder(path, condition, operation):
	for (root, dirnames, filenames) in os.walk(path):
		for name in filenames:
			filePath = os.path.join(root, name)
			if os.path.isfile(filePath) and condition(filePath):
				operation(filePath)

# Delete the specified files
def DeleteFiles(filePath):
	success = True
	(dirpath, wildcard) = os.path.split(filePath)
	origDir = os.getcwd()
	os.chdir(dirpath)
	for filename in glob.glob(wildcard):
		if options.verbose: print("Deleting",filename)
		if not options.test:
			try:
				os.remove(filename)
			except OSError as e:
				print("Unable to delete",filename,": ",e)
				success = False
	os.chdir(origDir)
	return success

# UnRAR the given file to the target folder
def UnRAR(filePath, targetFolder):
	if options.test: return True
	origDir = os.getcwd()
	os.chdir(targetFolder)
	retVal = subprocess.call(
		["c:\\Program Files\\WinRAR\\unRAR.exe",
		"e", "-y", filePath]) == 0
	os.chdir(origDir)
	return retVal

# Returns true if the given file is a RAR
def IsRAR(filePath):
	(basename, ext) = os.path.splitext(filePath)
	ext = ext.lower()
	return ext == '.rar'

# Find all rars, extract them to their parent folder and 
# remove all files bearing the same name as the rar (to find .r00, etc)
def ExtractRARs(filePath):
	(basename, ext) = os.path.splitext(filePath)
	(dirpath, filename) = os.path.split(filePath)
	(parentdir, dirname) = os.path.split(dirpath)
	
	if options.verbose: print("Extracting",filePath)
	if UnRAR(filePath, parentdir) == True:
		DeleteFiles(os.path.join(dirpath,basename)+".r*")
	
# Delete all samples, nfos, txt, etc
def IsUselessFile(filePath):
	(basename, ext) = os.path.splitext(filePath)
	ext = ext.lower()
	if ext in ['.nfo', '.txt', '.sfv']: return True
	if 'sample' in filePath.lower(): return True
	return False
	
# Move the specified file up one folder	
def MoveToParent(filePath):	
	(dirpath, filename) = os.path.split(filePath)
	(parentdir, dirname) = os.path.split(dirpath)
	
	if options.verbose: print("Moving",filename,"to",parentdir)
	if not options.test:
		try:
			os.rename(filePath, os.path.join(parentdir, filename))
			return True
		except OSError as e:
			print("Unable to move",filename,": ",e)
			return False	
	
# Remove the specified folder
def RemoveDir(path):
	if options.test: return True	
	if os.path.isdir(path):
		try:
			os.rmdir(path)
			return True
		except OSError as e:
			print("Unable to remove",path,": ",e)
			return False

# Remove any empty folders and move any lone files up one folder
def Cleanup(path):
	if options.verbose: print("Cleaning up", path)
	bEmpty = True
	for (root, dirnames, filenames) in os.walk(path):	
		if options.verbose: print("  Subdirs:", dirnames)
		for name in dirnames:
			dirPath = os.path.join(root, name)
			if Cleanup(dirPath) == False: 
				if options.verbose: print(path,"not empty because",dirnames,"not empty")
				bEmpty = False
		if (bEmpty and len(filenames) == 1):
			MoveToParent(os.path.join(root, filenames[0]))
		elif len(filenames) != 0:
			if options.verbose: print(path,"not empty - has",len(filenames),"files")
			bEmpty = False
	
	if bEmpty:
		if options.verbose: print("Removing empty folder", path)
		RemoveDir(path)
		return True
	
	return False
	
	
# Run all jobs over the given path
def RunAllJobs(path):
	if options.verbose: print("Extracting RARs in", path)
	ProcessFolder(path, IsRAR, ExtractRARs)
	
	if options.verbose: print("Removing useless files in", path)
	ProcessFolder(path, IsUselessFile, DeleteFiles)
	
	if options.verbose: print("Moving lone files and removing empty folders in", path)
	Cleanup(path)

####################################################
	
parser = OptionParser()
parser.add_option(
	"-q", "--quiet", 
	action="store_false", dest="verbose", 
	default=True, help="Silent processing")
parser.add_option(
	"-t", "--test",
	action="store_true", dest="test",
	default=False, help="Test run only (output which files will be processed, but do not actually process them)")
(options, args) = parser.parse_args()

for arg in args:
	RunAllJobs(arg)


