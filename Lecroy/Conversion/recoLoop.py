# def RecoAllScope(laserMode=False, LGADChannel=2, LGADThreshold=50):
import time
from datetime import datetime
# import numpy as np
# from numpy import loadtxt
import getpass
import os
import subprocess
import socket
import sys
import glob
import shutil
import ROOT
import argparse

####Use setup script in home area (setup.sh)

# LECROY_MOUNT_DIRECTORY = "/home/etl/Test_Stand/daq/LecroyMount" # ADD THE LECROY SCOPE RAW DATA FOLDER
# LECROY_CONVERTED_DATA_DIRECTORY = "/home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/ScopeData/LecroyConverted"
# LECROY_TIMINGDAQ_DATA_DIRECTORY ="/home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/ScopeData/LecroyTimingDAQ"
# BACKUP_DIRECTORY="/media/etl/ETL_DESY_Backup/SPS_May24"
# LECROY_RAW_DATA_DIRECTORY = "/home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/ScopeData/LecroyRaw"
# CONVERSION_DIRECTORY = "/home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/Lecroy/Conversion"

# ==================  !!! RUN FROM MODULE TEST SW  !!! ======================== #
# ------------------- SCOPE HANDLER MAIN DIRECTORIES ---------------------- #
TIMINGDAQ_DIRECTORY               = "../TimingDAQ"
ACQUISITION_DIRECTORY             = "../ScopeHandler/Lecroy/Acquisition" # IF RUNNING FROM MODULE_TEST_SW - WHICH IS WHAT HAPPENS WHEN RUNNING AUTOPILOT!!!
CONVERSION_DIRECTORY              = "../ScopeHandler/Lecroy/Conversion"

# ---------------- LECROY OSCILLISCOPE DATA DIRECTORIES ------------------- #
LECROY_MOUNT_DIRECTORY            = "/home/etl/Test_Stand/daq/LecroyMount" # ADD THE LECROY SCOPE RAW DATA FOLDER
LECROY_CONVERTED_DATA_DIRECTORY   = "../ScopeHandler/ScopeData/LecroyConverted"
LECROY_TIMINGDAQ_DATA_DIRECTORY   = "../ScopeHandler/ScopeData/LecroyTimingDAQ"
LECROY_RAW_DATA_DIRECTORY         = "../ScopeHandler/ScopeData/LecroyRaw"

#------------------------BACKUP DIRECTORIES---------------------------------#
BACKUP_DIRECTORY                  = "/media/etl/ETL_DESY_Backup/SPS_May24"
LECROY_RAW_BACKUP_DIRECTROY       = "/media/etl/ETL_DESY_Backup/SPS_May24/LecroyRaw/"
LECROY_CONVERTED_BACKUP_DIRECTORY = "/media/etl/ETL_DESY_Backup/SPS_May24/LecroyConverted/"
LECROY_TIMINGDAQ_BACKUP_DIRECTORY = "/media/etl/ETL_DESY_Backup/SPS_May24/LecroyTimingDAQ"


parser = argparse.ArgumentParser(description='Run info.')
parser.add_argument('--singleMode',metavar='Single event mode', type=str,default = 0, help='Single event acquisition (default 0, 1 for yes)',required=False)
args = parser.parse_args()

useSingleEvent =False
if int(args.singleMode) > 0:
    useSingleEvent=True
    print("Using single event mode.")

def RunEntriesScope(FileLocation, LGADChannels, LGADThreshold):
    list_hits=[]
    list_coinc=[]
    f = ROOT.TFile.Open(FileLocation)
    if hasattr(f, 'pulse'):
        ##### Number of Entries with Tracks
        TotalEntries = f.pulse.GetEntries()
        for chan in LGADChannels:
            EntriesWithLGADHits = f.pulse.GetEntries("amp[%i]>%i"%(chan,LGADThreshold))
            CoincRate = float(EntriesWithLGADHits)/TotalEntries
            list_hits.append(EntriesWithLGADHits)
            list_coinc.append(CoincRate)
        return list_coinc, list_hits, TotalEntries
    else:
        print("Root file did not have pulse tree!")
        return -1

# LGADChannels=[0,1,2,3]
LGADChannels=[1,2] #20GS/s
Threshold=15
acquisition_ready         = open(f"{ACQUISITION_DIRECTORY}/merging.txt",             "r").read() # This flag says if the acquisition data is ready to be merged.
running_acquisition_SCOPE = open(f"{ACQUISITION_DIRECTORY}/running_acquisition.txt", "r").read() # This flag says if the scope acquisition is still running.
running_acquisition_ETROC = open("running_ETROC_acquisition.txt",                    "r").read() # This flag says if the KCU acquisition is still running.
print("acquisition_ready: ", acquisition_ready)
print("running_acquisition_SCOPE: ", running_acquisition_SCOPE)
print("running_acquisition_ETROC: ", running_acquisition_ETROC)

while True:
    # This flag says if the acquisition data is ready to be merged.
    acquisition_ready         = open(f"{ACQUISITION_DIRECTORY}/merging.txt",             "r").read() 
    # This flag says if the scope acquisition is still running.
    running_acquisition_SCOPE = open(f"{ACQUISITION_DIRECTORY}/running_acquisition.txt", "r").read()
    # This flag says if the KCU acquisition is still running.
    running_acquisition_ETROC = open("running_ETROC_acquisition.txt",                    "r").read() 

    if (not (running_acquisition_SCOPE == "False" and acquisition_ready == "True")): 
        continue

    ListRawFiles = [(x.split('C2--Trace')[1].split('.trc')[0]) for x in glob.glob('%s/C2--Trace*'%LECROY_MOUNT_DIRECTORY)]
    print(ListRawFiles)
    SetRawFiles = set([int(x) for x in ListRawFiles])
    #### reprocess hack
    #  SetRawFiles = set( range(153629,154321))#range(9500,11099) )
        #+range(153629,154321))

    print ("Found files: ")
    print (SetRawFiles)

    if len(SetRawFiles) != 0:
        print(f"Number of files to be converted: {len(SetRawFiles)}")
    # print(ListRawFiles)
    # print(glob.glob('%s/C1--Trace*'%LECROY_MOUNT_DIRECTORY))

    for run in SetRawFiles:
        RecoPath = '%s/converted_run%i.root' % (LECROY_CONVERTED_DATA_DIRECTORY, run)
        RawPath = 'C2--Trace%i.trc' % run

        print('lsof -f --/home/etl/Test_Stand/daq/LecroyMount/%s |grep -Eoi %s' % (RawPath, RawPath))
        if os.path.exists(RecoPath):
            print('Run %i already converted. Doing reco stage two' % run)
        elif not os.popen(f'lsof -f -- {LECROY_MOUNT_DIRECTORY}/{RawPath} |grep -Eoi {RawPath}').read().strip() == RawPath:
            print('Converting run ', run)
            if not useSingleEvent: 
                print("using conversion")
                ConversionCmd = f"python3 {CONVERSION_DIRECTORY}/conversion.py --runNumber {run}"
            else:
                print("using one event conversion")
                ConversionCmd = f"python3 {CONVERSION_DIRECTORY}/conversion_one_event.py --runNumber {run}"
            os.system(ConversionCmd)
        if useSingleEvent: continue
        print('Doing dattoroot for run %i' % run)
        
        OutputFile = '%s/run_scope%i.root' % (LECROY_TIMINGDAQ_DATA_DIRECTORY, run)
        # OutputFile = '%s/run_scope%i.root' % (LECROY_CONVERTED_DATA_DIRECTORY, run)

        # HAYDEN TURNING THIS INTO F STRING...
        # DattorootCmd = '/home/etl/Test_Stand/ETL_TestingDAQ/TimingDAQ/NetScopeStandaloneDat2Root --correctForTimeOffsets --input_file=%s/converted_run%i.root \
        # --output_file=%s --config=/home/etl/Test_Stand/ETL_TestingDAQ/TimingDAQ/config/LecroyScope_v12.config --save_meas'  % (LECROY_CONVERTED_DATA_DIRECTORY, run, OutputFile)
        DattorootCmd = f'{TIMINGDAQ_DIRECTORY}/NetScopeStandaloneDat2Root --correctForTimeOffsets --input_file={LECROY_CONVERTED_DATA_DIRECTORY}/converted_run{run}.root \
        --output_file={OutputFile} --config={TIMINGDAQ_DIRECTORY}/config/LecroyScope_v12.config --save_meas'

        # need the correct executable script to make the reco files
        print(DattorootCmd)
        os.system(DattorootCmd)
        can_be_later_merged = False
        try:
            CoincRate, EntriesWithLGADHits, TotalEntries = RunEntriesScope(OutputFile, LGADChannels, Threshold) # lgad channel starting from zero 
            can_be_later_merged = True
        except Exception as error:
            print(repr(error))
        print("Run %i: Total entries are %i"%(run,TotalEntries))
        for i,chan in enumerate(LGADChannels):
            print('\t Channel %i coincidence:  %.1f%% (%i hits)'  % (chan+1, 100.*CoincRate[i], EntriesWithLGADHits[i]))
        print("\n")

        print('Now moving the converted, scope and raw data to backup')
        # # #Here moving the converted and raw data to backup
        os.system(f'mv {LECROY_RAW_DATA_DIRECTORY}/C*--Trace{run}.trc {LECROY_RAW_BACKUP_DIRECTROY}')  # ADD THE BACKUP FOLDER
        os.system(f'mv {LECROY_CONVERTED_DATA_DIRECTORY}/converted_run{run}.root {LECROY_CONVERTED_BACKUP_DIRECTORY}')  # ADD THE BACKUP FOLDER
        os.system(f'mv {OutputFile} {LECROY_TIMINGDAQ_BACKUP_DIRECTORY}/run_scope{run}.root')
        print(run)

        # #Here making a link from the ScopeData directory to the backup
        for i in range(1, 5):
            os.system(f'ln -s {LECROY_RAW_BACKUP_DIRECTROY}/C{i}--Trace{run}.trc {LECROY_RAW_DATA_DIRECTORY}')  # ADD THE BACKUP FOLDER
        os.system(f'ln -s {LECROY_CONVERTED_BACKUP_DIRECTORY}/converted_run{run}.root {LECROY_CONVERTED_DATA_DIRECTORY}/converted_run{run}.root')
        os.system(f'ln -s {LECROY_TIMINGDAQ_BACKUP_DIRECTORY}/run_scope{run}.root {OutputFile}')
        
        if can_be_later_merged:
            f = open("./merging.txt", "w")
            f.write("True")
            f.truncate()
            f.close()

    time.sleep(2)
