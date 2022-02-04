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

raw_path = "/home/daq/LecroyMount/"
converted_path = "/home/daq/ScopeData/LecroyConverted/"
reco_path ="/home/daq/ScopeData/LecroyTimingDAQ/"

parser = argparse.ArgumentParser(description='Run info.')

parser.add_argument('--singleMode',metavar='Single event mode', type=str,default = 0, help='Single event acquisition (default 0, 1 for yes)',required=False)
args = parser.parse_args()

useSingleEvent =False
if int(args.singleMode) >0: 
    useSingleEvent=True
    print "Using single event mode."

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
        return -1

LGADChannels=[0,1,2]
Threshold=15
while True:
    ListRawFiles = [(x.split('C8--Trace')[1].split('.trc')[0]) for x in glob.glob('%s/C8--Trace*'%raw_path)]
    SetRawFiles = set([int(x) for x in ListRawFiles])
  #  print "Found files: "
  #  print SetRawFiles
    for run in SetRawFiles:
        RecoPath = '%s/converted_run_scope%i.root' % (converted_path,run)
        RawPath = 'C8--Trace%i.trc' % run

        print 'lsof -f --/home/daq/LecroyMount/%s |grep -Eoi %s' % (RawPath, RawPath)
        if os.path.exists(RecoPath):
            print 'Run %i already converted. Doing reco stage two' % run

        elif not os.popen('lsof -f -- /home/daq/LecroyMount/%s |grep -Eoi %s' % (RawPath, RawPath)).read().strip() == RawPath:
            print 'Converting run ', run
            if not useSingleEvent: 
                print "using conversion"
                ConversionCmd = "python /home/daq/LecroyControl/Reconstruction/conversion.py --runNumber %i" % (run)
            else:
                print "using one event conversion" 
                ConversionCmd = "python /home/daq/LecroyControl/Reconstruction/conversion_one_event.py --runNumber %i" % (run)
            #print ConversionCmd
            os.system(ConversionCmd)
       
        if useSingleEvent: continue
        print 'Doing dattoroot for run %i' % run       
        # DattorootCmd = '/home/daq/ScopeTimingDAQ/TimingDAQ/NetScopeStandaloneDat2Root --config_file=/home/daq/ScopeTimingDAQ/TimingDAQ/config/Scope_BetaSource.config --input_file=/home/daq/ScopeData/Converted/run_scope%i.root --output_file=/home/daq/ScopeData/Reco/run_scope%i.root --save_meas' % (run,run)
        
        OutputFile = '%s/run_scope%i.root' % (reco_path, run)
        #DattorootCmd = '/home/daq/ScopeTimingDAQ/TimingDAQ/NetScopeStandaloneDat2Root502 --input_file=%s/converted_run%i.root --output_file=%s --config=/home/daq/ScopeTimingDAQ/TimingDAQ/config/Lecroy_BetaSource.config --save_meas'  % (converted_path,run,OutputFile)
        DattorootCmd = '/home/daq/ScopeTimingDAQ/TimingDAQ/NetScopeStandaloneDat2Root2002 --input_file=%s/converted_run%i.root --output_file=%s --config=/home/daq/ScopeTimingDAQ/TimingDAQ/config/Lecroy_BetaSource_v2.config --save_meas'  % (converted_path,run,OutputFile)

        print DattorootCmd
        os.system(DattorootCmd)
        
        CoincRate, EntriesWithLGADHits, TotalEntries = RunEntriesScope(OutputFile, LGADChannels, Threshold) # lgad channel starting from zero 
        print "Run %i: Total entries are %i"%(run,TotalEntries)
        for i,chan in enumerate(LGADChannels):
            print '\t Channel %i coincidence:  %.1f%% (%i hits)'  % (chan+1, 100.*CoincRate[i], EntriesWithLGADHits[i])
        print "\n"

        print 'Now moving the converted and raw data to backup'
        # #Here moving the converted and raw data to backup
        os.system('mv %s/converted_run%i.root /run/media/daq/ScanBackup/LecroyBackup/Converted/' % (converted_path,run))
        os.system('mv /home/daq/ScopeData/LecroyRaw/C*--Trace%i.trc /run/media/daq/ScanBackup/LecroyBackup/Raw/' % (run))


        # #Here making a link from the ScopeData directory to the backup
        for i in range(1,9):
            os.system('ln -s /run/media/daq/ScanBackup/LecroyBackup/Raw/C%i--Trace%i.trc /home/daq/ScopeData/LecroyRaw/' % (i,run))
        os.system('ln -s /run/media/daq/ScanBackup/LecroyBackup/Converted/converted_run%i.root %s/converted_run%i.root' % (run,converted_path,run)) 
        print 'Done Moving and creating the link'

    time.sleep(2)