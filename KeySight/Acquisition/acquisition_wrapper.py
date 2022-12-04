#!/bin/python

### if sample rate or horizontal window is changed, TimingDAQ must be recompiled to account for new npoints.
import sys
import os

sampleRate = 20#GSa/s ### not sure if works for Lecroy
horizontalWindow = 30 #ns

#Hard Code these:
trigCh="2" ## or "C{N}" or "EX"
trig= 0.619 ## -0.01 V

vScale1 = 0.5
vScale2 = 0.5 
vScale3 = 0.1 
vScale4 = 0.5 
vScale5 = 0.1  
vScale6 = 0.1
vScale7 = 0.1 
vScale8 = 0.1

vPos1 = -3
vPos2 = -3
vPos3 = -3
vPos4 = -3
vPos5 = -3
vPos6 = -3
vPos7 = -3
vPos8 = -3

trigSlope = "POS"
timeoffset = 0 #ns

RunNumber = -1 ### -1 means use serial number


ScopeControlDir = "/home/daq/etltest_0721/Scope/ScopeHandler/KeySight/"

def ScopeAcquisition(NumEvents):

	print "\n ####################### Running the scope acquisition ##################################\n"
	ScopeCommand = 'python %sAcquisition/acquisition.py --runNum %s --numEvents %d --sampleRate %d --horizontalWindow %d --trigCh %s --trig %f --vScale1 %f --vScale2 %f --vScale3 %f --vScale4 %f --timeoffset %i --trigSlope %s' % (ScopeControlDir,RunNumber, NumEvents, sampleRate, horizontalWindow, trigCh, trig, vScale1, vScale2, vScale3, vScale4, timeoffset, trigSlope) 
	#ScopeCommand = 'python %s/Acquisition/acquisition.py --runNum %s --numEvents %d --sampleRate %d --horizontalWindow %d --trigCh %s --trig %f --vScale1 %f --vScale2 %f --vScale3 %f --vScale4 %f --vScale5 %f --vScale6 %f --vScale7 %f --vScale8 %f --vPos7 %f --vPos8 %f --timeoffset %i --trigSlope %s --display 0' % (ScopeControlDir,runNumber, numEvents, sampleRate, horizontalWindow, trigCh, trig, vScale1, vScale2, vScale3, vScale4,vScale5, vScale6, vScale7, vScale8, vPos7, vPos8, timeoffset,trigSlope) 


	print ScopeCommand
	os.system(ScopeCommand)
		    

if __name__ == "__main__":
	numEvents = int(sys.argv[1])
	ScopeAcquisition(numEvents)
