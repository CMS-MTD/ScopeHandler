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
trig= -0.3 # -0.04 ## -0.01 V

vScale1 = 0.2
vScale2 = 0.2 
vScale3 = 0.2 
vScale4 = 0.2 
# vScale5 = 0.05 
# vScale6 = 0.10
# vScale7 = 0.50
# vScale8 = 0.50
vPos1 = 0
vPos2 = 3
vPos3 = -3
vPos4 = 0

trigSlope = "NEG"
timeoffset = 0 #ns
# timeoffset = 12.5 #ns
runNumber = -1 ### -1 means use serial number
ScopeControlDir = "/home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/Lecroy"

def ScopeAcquisition(numEvents):
    print("\n ####################### Running the scope acquisition ##################################\n")
    ScopeCommand = (
        f'/usr/bin/python3 {ScopeControlDir}/Acquisition/acquisition.py '
        f'--runNum {runNumber} '
        f'--numEvents {numEvents} '
        f'--sampleRate {sampleRate} '
        f'--horizontalWindow {horizontalWindow} '
        f'--trigCh {trigCh} '
        f'--trig {trig} '
        f'--vScale2 {vScale2} '
        f'--vScale3 {vScale3} '
        f'--vPos2 {vPos2} '
        f'--vPos3 {vPos3} '
        f'--timeoffset {timeoffset} '
        f'--trigSlope {trigSlope} '
        f'--display 1'
    )
    # ScopeCommand += ' --vScale1 %f --vScale2 %f --vScale3 %f --vScale4 %f ' % (vScale1, vScale2, vScale3, vScale4)
    # ScopeCommand += ' --vPos1 %f --vPos2 %f --vPos3 %f --vPos4 %f ' % (vPos1,vPos2, vPos3, vPos4)
    #GS/s
    # ScopeCommand += f' --vScale1 {vScale1} --vScale2 {vScale2} --vScale3 {vScale3} --vScale4 {vScale4} '
    # ScopeCommand += f' --vPos1 {vPos1} --vPos2 {vPos2} --vPos3 {vPos3} --vPos4 {vPos4} '
    # GS/s

    print(ScopeCommand)
    os.system(ScopeCommand)
            
if __name__ == "__main__":
    argParser = argparse.ArgumentParser(description = "Argument parser")
    argParser.add_argument("--force_acquisition",action="store_true")
    argParser.add_argument("--nevents",action="store")
    args = argParser.parse_args()
    with open("/home/etl/Test_Stand/ETL_TestingDAQ/module_test_sw/running_ETROC_acquisition.txt") as file:
        kcu_acquisition_flag = file.read()
    
    print("kcu_acquisition_flag ",kcu_acquisition_flag)
    iteration = 0
    while kcu_acquisition_flag == "False":
        if args.force_acquisition: break
        if iteration == 0:
            print(f"Waiting for the KCU.")
        with open("/home/etl/Test_Stand/ETL_TestingDAQ/module_test_sw/running_ETROC_acquisition.txt") as file:
            kcu_acquisition_flag = file.read()
        iteration+=1

    with open("/home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/Lecroy/Acquisition/running_acquisition.txt", "w") as f:
        f.write("True")
        f.truncate()

    numEvents = int(args.nevents)
    ScopeAcquisition(numEvents)

    with open("/home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/Lecroy/Acquisition/running_acquisition.txt", "w") as f:
        f.write("False")
        f.truncate()

    with open("/home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/Lecroy/Acquisition/merging.txt", "w") as f:
        f.write("True")
        f.truncate()

