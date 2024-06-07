#! /usr/bin/env python
import os, sys, shutil
import csv
import yaml
from ROOT import *
from array import array
from collections import namedtuple

hitTreeInputDir ="/home/daq/SurvivalBeam2021/LecroyScope/RecoData/HitCounterRECO/RecoWithoutTracks/";
infoInputDir = "/home/daq/SurvivalBeam2021/ConfigInfo/Runs/"


condorMode=False
if os.path.exists("_condor_stdout"):
    print("Detected condor")
    condorMode=True
    hitTreeInputDir=""
    infoInputDir=""

def processRun(runNumber,outfileName,infoDict):
    rootfile = TFile(outfileName, "UPDATE")
    if (rootfile.IsZombie() or not rootfile.IsOpen()):
        return 'ERROR: Could not recover TTree, please check file:', outfileName
    pulse = rootfile.Get('pulse')


    ### Declare vectors to hold branches
    arr_run = array('i',[infoDict['Run number']])
    arr_gconf = array('i',[infoDict['Configuration']])

    v_sensors = vector('string')()
    v_pads = vector('int')()
    v_mux = vector('string')()
    v_row = vector('int')()
    v_col = vector('int')()
    v_slot = vector('int')()
    v_sensorsHV = vector('string')()
    v_HVs = vector('int')()

    #### Fill vectors from Lecroy config
    for ichan in range(8): 
        key = 'Sensor Ch%i' % ichan  ### Loop over sensor names in airtable Lecroy config
        if key in infoDict: 
            v_sensors.push_back(infoDict[key])
            if len(infoDict[key].split("Slot"))>1: ###if slot is specified in sensor name
                v_slot.push_back(int(infoDict[key].split("Slot")[1].split("_")[0]))
            else: v_slot.push_back(-1)
        else: 
            v_sensors.push_back("Empty")
            v_slot.push_back(-1)

    for ichan in range(8):
        key = 'CH%i MUX' % ichan
        if key in infoDict: v_mux.push_back(infoDict[key])
        else: v_mux.push_back("Not set")

    for ichan in range(8):
        key = 'Ch %i' % ichan ### ### Loop over sensor pad number in airtable Lecroy config
        if key in infoDict: 
            v_pads.push_back(infoDict[key])
            v_row.push_back(int(infoDict[key]/10))
            v_col.push_back(infoDict[key]%10)
        
        else: 
            v_pads.push_back(-1)
            v_row.push_back(-1)
            v_col.push_back(-1)

    #### Fill vectors from CAEN config
    for iHV in range(8):
        key = 'Sensor HV%i' % iHV  ### Loop over sensor names in airtable CAEN config
        if key in infoDict: v_sensorsHV.push_back(infoDict[key])

        key = 'HV%i' % iHV
        if key in infoDict: v_HVs.push_back(infoDict[key])



    print("sensors")
    for sensor in v_sensors: print(sensor)
    print("pads")
    for pad in v_pads: print(pad)
    print("mux")
    for mux in v_mux: print(mux)
    print("col")
    for col in v_col: print(col)

    ### define new branches from vectors
    b_run = pulse.Branch("run",arr_run,"run/I")
    b_gconf = pulse.Branch("gconf",arr_gconf,"gconf/I")
    b_sensors = pulse.Branch('sensors',v_sensors)
    b_pads = pulse.Branch("pads",v_pads)
    b_sensorsHV = pulse.Branch('sensorsHV',v_sensorsHV)
    b_HVs = pulse.Branch("HVs",v_HVs)


    #### Not currently keeping row, col, slot, or mux, these were specific to survival beam.

    for i in range(pulse.GetEntries()):
        pulse.GetEntry(i)
        b_run.Fill()
        b_gconf.Fill()
        b_sensors.Fill()
        b_pads.Fill()
        b_HVs.Fill()
        b_sensorsHV.Fill()

    pulse.Write()
    rootfile.Close()


if __name__ == '__main__':
    
    runNumber = int(sys.argv[1])
    versionNumber = int(sys.argv[2])
    inputFileName = str(sys.argv[3])

    infileName = "%s/v%i/hitTree_run%i.root" % (hitTreeInputDir,versionNumber,runNumber)
    outfileName = "%s/v%i/hitTree_run%i_info.root" % (hitTreeInputDir,versionNumber,runNumber)
    if condorMode:
        infileName=inputFileName
        outfileName=infileName.replace(".root","_info.root")

    cmd = "xrdcp -f %s %s" % (infileName,outfileName)
    print(cmd)
    os.system(cmd)

    infoDictFileName = "%sinfo_%i.json" % (infoInputDir,runNumber)
    infoDictFile = open(infoDictFileName,"r")
    txtbuffer = infoDictFile.read()

    infoDict = yaml.safe_load(txtbuffer)

    print('Processing file:', infileName)
    processRun(runNumber,outfileName,infoDict)
