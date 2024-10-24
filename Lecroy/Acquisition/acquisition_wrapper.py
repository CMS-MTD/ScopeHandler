### if sample rate or horizontal window is changed, TimingDAQ must be recompiled to account for new npoints.
import sys
import os
import argparse
# sampleRate = 1000 #GSa/s ### not sure if works for Lecroy
# sampleRate = 10 #GSa/s ### not sure if works for Lecroy
sampleRate = 20 #GSa/s ### not sure if works for Lecroy
horizontalWindow = 50 #ns
# horizontalWindow = 40 #ns
# horizontalWindow = 25 # ns
# horizontalWindow = 12.5 #ns

#Hard Code these:
trigCh="C2" #"EX" ## or "C{N}" or "EX"
trig= -0.05 # -0.04 ## -0.01 V

vScale1 = 0.2
vScale2 = 0.15 
vScale3 = 0.2 
vScale4 = 0.2 
# vScale5 = 0.05 
# vScale6 = 0.10
# vScale7 = 0.50
# vScale8 = 0.50
vPos1 = 0
vPos2 = 2
vPos3 = -3
vPos4 = 0

trigSlope = "NEG"
timeoffset = 0 #ns
# timeoffset = 12.5 #ns
runNumber = -1 ### -1 means use serial number
#ScopeControlDir = "../ScopeHandler/Lecroy" # deprecated this line for the below, more general line
ACQUISITION_DIRECTORY = "../ScopeHandler/Lecroy/Acquisition" # IF RUNNING FROM MODULE_TEST_SW - WHICH IS WHAT HAPPENS WHEN RUNNING AUTOPILOT!!!

def ScopeAcquisition(numEvents):
    print("\n ####################### Running the scope acquisition ##################################\n")
    ScopeCommand = 'python3 %s/acquisition.py --runNum %s --numEvents %d --sampleRate %d --horizontalWindow %d --trigCh %s --trig %f' % (ACQUISITION_DIRECTORY,runNumber, numEvents, sampleRate, horizontalWindow, trigCh, trig)
    # ScopeCommand += ' --vScale1 %f --vScale2 %f --vScale3 %f --vScale4 %f ' % (vScale1, vScale2, vScale3, vScale4)
    # ScopeCommand += ' --vPos1 %f --vPos2 %f --vPos3 %f --vPos4 %f ' % (vPos1,vPos2, vPos3, vPos4)
    #GS/s
    ScopeCommand += ' --vScale2 %f --vScale3 %f ' % ( vScale2, vScale3)
    ScopeCommand += ' --vPos2 %f --vPos3 %f  ' % (vPos2, vPos3)

    ScopeCommand += ' --timeoffset %i --trigSlope %s --display 1' % (timeoffset,trigSlope) 
    print(ScopeCommand)
    os.system(ScopeCommand)
            
if __name__ == "__main__":
    argParser = argparse.ArgumentParser(description = "Argument parser")
    argParser.add_argument("--force_acquisition",action="store_true")
    argParser.add_argument("--nevents",action="store")
    args = argParser.parse_args()
    kcu_acquisition_flag = open("running_ETROC_acquisition.txt").read() # This is in module_test_sw so for when running autopilot this path is correct!
    print("kcu_acquisition_flag ",kcu_acquisition_flag)
    iteration = 0
    while kcu_acquisition_flag == "False":
        if args.force_acquisition: break
        if iteration == 0:
            print(f"Waiting for the KCU.")
        kcu_acquisition_flag = open("running_ETROC_acquisition.txt").read()
        iteration+=1
    f = open(f"{ACQUISITION_DIRECTORY}/running_acquisition.txt", "w") 
    f.write("True")
    f.truncate()
    f.close()
    numEvents = int(args.nevents)
    ScopeAcquisition(numEvents)
    f = open(f"{ACQUISITION_DIRECTORY}/running_acquisition.txt", "w")
    f.write("False")
    f.truncate()
    f.close()
    f = open(f"{ACQUISITION_DIRECTORY}/merging.txt", "w")
    f.write("True")
    f.truncate()
    f.close()

