### if sample rate or horizontal window is changed, TimingDAQ must be recompiled to account for new npoints.
import sys
import os

sampleRate = 10#GSa/s ### not sure if works for Lecroy
horizontalWindow = 200 #ns

#Hard Code these:
trigCh="C8" ## or "C{N}" or "EX"
trig= 0.001 ## -0.01 V

vScale1 = 0.03
vScale2 = 0.03 
vScale3 = 0.03 
vScale4 = 0.03 
vScale5 = 0.03  
vScale6 = 0.03
vScale7 = 0.25 
vScale8 = 0.05

vPos7 = -3
vPos8 = -3

trigSlope = "POS"
timeoffset = 0 #ns

runNumber = -1 ### -1 means use serial number


ScopeControlDir = "/home/daq/SensorBeam2022/ScopeHandler/Lecroy/"

def ScopeAcquisition(numEvents):

	print "\n ####################### Running the scope acquisition ##################################\n"
	#ScopeCommand = 'python %sAcquisition/acquisition.py --runNum %s --numEvents %d --sampleRate %d --horizontalWindow %d --trigCh %s --trig %f --vScale1 %f --vScale2 %f --vScale3 %f --vScale4 %f --timeoffset %i --trigSlope %s' % (ScopeControlDir,RunNumber, NumEvents, sampleRate, horizontalWindow, trigCh, trig, vScale1, vScale2, vScale3, vScale4, timeoffset, trigSlope) 
	ScopeCommand = 'python %s/Acquisition/acquisition.py --runNum %s --numEvents %d --sampleRate %d --horizontalWindow %d --trigCh %s --trig %f --vScale1 %f --vScale2 %f --vScale3 %f --vScale4 %f --vScale5 %f --vScale6 %f --vScale7 %f --vScale8 %f --vPos7 %f --vPos8 %f --timeoffset %i --trigSlope %s --display 0' % (ScopeControlDir,runNumber, numEvents, sampleRate, horizontalWindow, trigCh, trig, vScale1, vScale2, vScale3, vScale4,vScale5, vScale6, vScale7, vScale8, vPos7, vPos8, timeoffset,trigSlope) 


	print ScopeCommand
	os.system(ScopeCommand)
		    

if __name__ == "__main__":
	numEvents = int(sys.argv[1])
	ScopeAcquisition(numEvents)
