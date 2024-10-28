# def RecoAllScope(laserMode=False, LGADChannel=2, LGADThreshold=50):
import time
from datetime import datetime
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

raw_path       = "/home/etl/Test_Stand/daq/LecroyMount" # ADD THE LECROY SCOPE RAW DATA FOLDER
converted_path = "/home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/ScopeData/LecroyConverted"
reco_path      = "/home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/ScopeData/LecroyTimingDAQ"
bkp_path       = "/media/etl/Storage/SPS_October_2024"

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
            EntriesWithLGADHits = f.pulse.GetEntries(f"amp[{chan}]>{LGADThreshold}")
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
acquisition_ready         = open("/home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/Lecroy/Acquisition/merging.txt", "r").read() # This flag says if the acquisition data is ready to be merged.
running_acquisition_SCOPE = open("/home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/Lecroy/Acquisition/running_acquisition.txt", "r").read() # This flag says if the scope acquisition is still running.
running_acquisition_ETROC = open("/home/etl/Test_Stand/module_test_sw/running_ETROC_acquisition.txt", "r").read() # This flag says if the KCU acquisition is still running.
print("acquisition_ready: ", acquisition_ready)
print("running_acquisition_SCOPE: ", running_acquisition_SCOPE)
print("running_acquisition_ETROC: ", running_acquisition_ETROC)

while True:
    # This flag says if the acquisition data is ready to be merged.
    acquisition_ready         = open("/home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/Lecroy/Acquisition/merging.txt", "r").read() 
    # This flag says if the scope acquisition is still running.
    running_acquisition_SCOPE = open("/home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/Lecroy/Acquisition/running_acquisition.txt", "r").read()
    # This flag says if the KCU acquisition is still running.
    running_acquisition_ETROC = open("/home/etl/Test_Stand/module_test_sw/running_ETROC_acquisition.txt", "r").read() 

    if (not (running_acquisition_SCOPE == "False" and acquisition_ready == "True")): 
        continue

    ListRawFiles = [(x.split('C2--Trace')[1].split('.trc')[0]) for x in glob.glob(f'{raw_path}/C2--Trace*')]
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
    # print(glob.glob(f'{raw_path}/C1--Trace*'))

    for run in SetRawFiles:
        RecoPath = f'{converted_path}/converted_run{run}.root'
        RawPath  = f'C2--Trace{run}.trc'

        print(f'lsof -f --/home/etl/Test_Stand/daq/LecroyMount/{RawPath} | grep -Eoi {RawPath}')
        if os.path.exists(RecoPath):
            print(f'Run {run} already converted. Doing reco stage two')

        elif not os.popen(f'lsof -f --/home/etl/Test_Stand/daq/LecroyMount/{RawPath} | grep -Eoi {RawPath}').read().strip() == RawPath:
            print('Converting run ', run)
            if not useSingleEvent: 
                print("using conversion")
                ConversionCmd = f"python3 /home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/Lecroy/Conversion/conversion.py --runNumber {run}"
            else:
                print("using one event conversion")
                ConversionCmd = f"python3 /home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/Lecroy/Conversion/conversion_one_event.py --runNumber {run}"
            os.system(ConversionCmd)
        
        if useSingleEvent: continue
        print(f'Doing dattoroot for run {run}')
        
        OutputFile = f'{reco_path}/run_scope{run}.root'
        DattorootCmd = f'/home/etl/Test_Stand/ETL_TestingDAQ/TimingDAQ/NetScopeStandaloneDat2Root --correctForTimeOffsets --input_file={converted_path}/converted_run{run}.root --output_file={OutputFile} --config=/home/etl/Test_Stand/ETL_TestingDAQ/TimingDAQ/config/LecroyScope_v12.config --save_meas'
        
        # need the correct executable script to make the reco files
        print(DattorootCmd)
        os.system(DattorootCmd)
        can_be_later_merged = False
        try:
            CoincRate, EntriesWithLGADHits, TotalEntries = RunEntriesScope(OutputFile, LGADChannels, Threshold) # lgad channel starting from zero 
            can_be_later_merged = True
        except Exception as error:
            print(repr(error))
        print(f"Run {run}: Total entries are {TotalEntries}")
        for i,chan in enumerate(LGADChannels):
            print(f'\t Channel {chan+1} coincidence: {100.*CoincRate[i]} ({EntriesWithLGADHits[i])} hits)')
        print("\n")

        print('Now moving the converted, scope and raw data to backup')
        # # #Here moving the converted and raw data to backup
        os.system(f'mv /home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/ScopeData/LecroyRaw/C*--Trace{run}.trc /media/etl/Storage/SPS_October_2024/LecroyRaw/') # ADD THE BACKUP FOLDER
        os.system(f'mv {converted_path}/converted_run{run}.root /media/etl/Storage/SPS_October_2024/LecroyConverted/') # ADD THE BACKUP FOLDER
        os.system(f'mv {OutputFile}/media/etl/Storage/SPS_October_2024/LecroyTimingDAQ/run_scope{run}.root')
        
        print(run)

        # #Here making a link from the ScopeData directory to the backup
        for i in range(1,5): #
            os.system(f'ln -s /media/etl/Storage/SPS_October_2024/LecroyRaw/C{i}--Trace{run}.trc /home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/ScopeData/LecroyRaw/') # ADD THE BACKUP FOLDER
        os.system(f'ln -s /media/etl/Storage/SPS_October_2024/LecroyConverted/converted_run{run}.root {converted_path}/converted_run{run}.root') 
        os.system(f'ln -s /media/etl/Storage/SPS_October_2024/LecroyTimingDAQ/run_scope{run}.root {OutputFile}')
        print('Done Moving and creating the link')
        if can_be_later_merged:
            f = open("./merging.txt", "w")
            f.write("True")
            f.truncate()
            f.close()

    time.sleep(2)
