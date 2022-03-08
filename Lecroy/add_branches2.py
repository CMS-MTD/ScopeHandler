#! /usr/bin/env python
import os, sys, shutil
import csv
import yaml
from ROOT import *
from array import array
from collections import namedtuple

hitTreeInputDir ="/home/daq/SurvivalBeam2021/LecroyScope/RecoData/HitCounterRECO/RecoWithoutTracks/";
infoInputDir = "/home/daq/SurvivalBeam2021/ConfigInfo/Runs/"

condorMode=True
if condorMode: 
    hitTreeInputDir=""
    infoInputDir=""


def processRun(runNumber,outfileName,infoDict):
    # globConf,scopeConf,caenConf = getConfs(runNumber)
    # sensors,pads = getChannelMap(scopeConf)
    # sensorsHV,HVs = getHVMap(caenConf)
    # print "Processing run %i, global configuration %i, scopeConf %i, caenConf %i" % (runNumber,globConf,scopeConf,caenConf)

    rootfile = TFile(outfileName, "UPDATE")
    if (rootfile.IsZombie() or not rootfile.IsOpen()):
        return 'ERROR: Could not recover TTree, please check file:', outfileName
    hits = rootfile.Get('hits')

    arr_run = array('i',[infoDict['Run number']])
    arr_gconf = array('i',[infoDict['Configuration']])
    v_sensors = vector('string')()
    v_mux = vector('string')()
    v_padnum = vector('int')()
    v_row = vector('int')()
    v_col = vector('int')()
    v_slot = vector('int')()

    for ichan in range(8):
        key = 'Sensor Ch%i' % ichan
        if key in infoDict: 
            v_sensors.push_back(infoDict[key])
            if len(infoDict[key].split("Slot"))>1:
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
        key = 'Ch %i' % ichan
        if key in infoDict: 
            v_padnum.push_back(infoDict[key])
            v_row.push_back(infoDict[key]/10)
            v_col.push_back(infoDict[key]%10)
        
        else: 
            v_padnum.push_back(-1)
            v_row.push_back(-1)
            v_col.push_back(-1)


    print "sensors"
    for sensor in v_sensors: print sensor
    print "pads"
    for pad in v_padnum: print pad
    print "mux"
    for mux in v_mux: print mux
    print "col"
    for col in v_col: print col

    # for x in sensors: v_sensors.push_back(x)
    # v_pads = vector('int')()
    # for x in pads: v_pads.push_back(x)
    #arr_pads = array('i',pads)
    # v_sensorsHV = vector('string')()
    # for x in sensorsHV: v_sensorsHV.push_back(x)
    # v_HVs = vector('int')()
    # for x in HVs: v_HVs.push_back(x)
    # #arr_HVs = array('i',HVs)

    v_sensor_this_hit = vector('string')()
    v_sensor_this_hit.push_back(v_sensors[0])
    
    arr_pad_this_hit = array('i',[v_padnum[0]])
    arr_col_this_hit = array('i',[v_col[0]])
    arr_row_this_hit = array('i',[v_row[0]])
    arr_slot_this_hit = array('i',[v_slot[0]])
    # arr_mux_this_hit = array('i',[v_mux[4]])

    b_run = hits.Branch("run",arr_run,"run/I")
    b_gconf = hits.Branch("gconf",arr_gconf,"gconf/I")
    b_sensor = hits.Branch('sensor',v_sensor_this_hit)
    b_col = hits.Branch("col",arr_col_this_hit,"col/I")
    b_row = hits.Branch("row",arr_row_this_hit,"row/I")
    b_pad = hits.Branch("pad",arr_pad_this_hit,"pad/I")
    b_slot = hits.Branch("slot",arr_slot_this_hit,"slot/I")
    # b_slot = hits.Branch("slot",arr_slot,"slot/I")





    # b_sensors = hits.Branch('sensors',v_sensors)
    # b_pads = hits.Branch("pads",v_pads)
    # b_sensorsHV = hits.Branch('sensorsHV',v_sensorsHV)
    # b_HVs = hits.Branch("HVs",v_HVs)
    #b_HVs = hits.Branch("HVs",arr_HVs,'HVs[{0}]/I'.format(len(HVs)))

    for i in range(hits.GetEntries()):
        hits.GetEntry(i)
        scopeChannel = hits.scopechan
        v_sensor_this_hit[0]=v_sensors[scopeChannel]
        
        arr_pad_this_hit[0] = v_padnum[scopeChannel]
        arr_col_this_hit[0] = v_col[scopeChannel]
        arr_row_this_hit[0] = v_row[scopeChannel]
        arr_slot_this_hit[0] = v_slot[scopeChannel]

        b_run.Fill()
        b_gconf.Fill()
        
        b_sensor.Fill()
        b_pad.Fill()
        b_col.Fill()
        b_row.Fill()
        b_slot.Fill()

    hits.Write()
    rootfile.Close()


if __name__ == '__main__':
    
    runNumber = int(sys.argv[1])
    versionNumber = int(sys.argv[2])

    infileName = "%s/v%i/hitTree_run%i.root" % (hitTreeInputDir,versionNumber,runNumber)
    outfileName = "%s/v%i/hitTree_run%i_info.root" % (hitTreeInputDir,versionNumber,runNumber)
    if condorMode:
        infileName="hitTree_run%i.root"%runNumber
        outfileName="hitTree_run%i_info.root"%runNumber


    cmd = "xrdcp -f %s %s" % (infileName,outfileName)
    print cmd
    os.system(cmd)

    infoDictFileName = "%sinfo_%i.json" % (infoInputDir,runNumber)
    infoDictFile = open(infoDictFileName,"r")
    txtbuffer = infoDictFile.read()

    infoDict = yaml.safe_load(txtbuffer)

    print 'Processing file:', infileName
    processRun(runNumber,outfileName,infoDict)

    # if condorMode:
    #     cmd = "xrdcp -f %s %s" % (outfileName,outDir)
    #     print cmd
    #     os.system(cmd)
