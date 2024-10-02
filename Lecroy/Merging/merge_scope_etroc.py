import uproot
import numpy as np
import awkward as ak
from awkward.highlevel import Array as akArray
import time
import os
import argparse
from clock import calc_clock
import file_status as file

BASE_DATA_DIR   = "/home/etl/Test_Stand/ETROC2_Test_Stand/ScopeHandler"

# INPUT DATA PATHS
RECO_DATA_PATH  = lambda run_num: f"{BASE_DATA_DIR}/ScopeData/LecroyConverted/converted_run{run_num}.root"
SCOPE_DATA_PATH = lambda run_num: f"{BASE_DATA_DIR}/ScopeData/LecroyTimingDAQ/run_scope{run_num}.root"
ETROC_DATA_PATH = lambda run_num: f"{BASE_DATA_DIR}/ScopeData/ETROCData/output_run_{run_num}_rb0.root"
RECO_TREE, SCOPE_TREE, ETROC_TREE = 'pulse', 'pulse', 'pulse'

# CLOCK CONFIGURABLES
CLOCK_THRESH_LOW, CLOCK_THRESH_HIGH = 0.25, 0.8 #used to pick out the edges (between 0 and 1, percentage of the absolute amplitude)
CLOCK_MEAUREMENT_POINT = 0.5 #between 0 and 1, after the fit, where along the fitted y axis do we take the clock value
CHANNEL_NUM = 2 #channel with square wave voltage (by index!! so subtract 1 to whatever it is on oscilloscope)

# OUTPUT DATA PATHS
OUTPUT_FILENAME = lambda run_num: f"run_{run_num}_rb0.root"
BACKUP_FOLDER   = "/media/etl/Storage/LecroyMerged/"
OUTPUT_FILE_DIR = f"{BASE_DATA_DIR}/ScopeData/LecroyMerged/"
#OUTPUT_FILE_DIR = f"/home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/Lecroy/Merging/unit_test/run_{f_index}_rb0.root"

# STATUS FILEPATHS 
NEXT_RUN_NUM_PATH               = f"{BASE_DATA_DIR}/Lecroy/Acquisition/next_run_number.txt"
LECROY_CONVERSION_MERGING_PATH  = f"{BASE_DATA_DIR}/Lecroy/Conversion/merging.txt"
LECROY_ACQUISITION_MERGING_PATH = f"{BASE_DATA_DIR}/Lecroy/Acquisition/merging.txt"
MODULE_TEST_SW_MERGING          = f"/home/etl/Test_Stand/module_test_sw/merging.txt" #root dumper?

#RAW_PATH = "/home/etl/Test_Stand/daq/LecroyMount/"  # PATH TO THE SCOPE RAW DATA FOLDER

def merge_trees(reco_data:akArray, scope_data:akArray, etroc_data:akArray, output_file:str) -> None:
    #---------------MERGE ARRAYS----------------#
    reco_data_map = dict(zip(
        ak.fields(reco_data), ak.unzip(reco_data)
    ))
    scope_data_map = dict(zip(
        ak.fields(scope_data), ak.unzip(scope_data)
    ))
    etroc_data_map = dict(zip(
        ak.fields(etroc_data), ak.unzip(etroc_data)
    ))
    
    #NOTE !!!!!!!ORDER MATTERS!!!!!!!!!!! 
    # THE CHANNEL FIELD FOR SCOPE_DATA IS DIFFERENT THAN RECO DATA!
    # taking reco data channels because of what was done previously...
    merged_data_map = scope_data_map | reco_data_map |  etroc_data_map
    clock = calc_clock(
        merged_data_map['time'], 
        merged_data_map['channel'][:, CHANNEL_NUM],
        CLOCK_THRESH_LOW, CLOCK_THRESH_HIGH, CLOCK_MEAUREMENT_POINT
    )
    merged_data_map['Clock'] = clock

    with uproot.recreate(output_file) as output:
        output["pulse"] = merged_data_map

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run info.')
    parser.add_argument('--runNumber',metavar='runNumber', type=str,default = -1, help='runNumber (default -1)',required=False)
    parser.add_argument('--force', default=False, action='store_true', help='skip reco/merge/scope is running checks',required=False)
    parser.add_argument('--replace', default=False, action='store_true', help='If a merge file already exists, it deletes it and replaces it',required=False)
    parser.add_argument('--no_sym_link', default=False, action='store_true', help='Turns off sym linking to backup')
    args = parser.parse_args()

    if args.runNumber==-1:
        f_index=int(open(NEXT_RUN_NUM_PATH, "r").read())
    else:
        f_index = int(args.runNumber)
    print(f"MERGING FILES FOR RUN: {f_index}")

    main_loop = True
    while main_loop:
        reco_path  = RECO_DATA_PATH(f_index) 
        scope_path = SCOPE_DATA_PATH(f_index)
        etroc_path = ETROC_DATA_PATH(f_index)

        reco  = file.is_data_file_ready(reco_path,  LECROY_CONVERSION_MERGING_PATH,  force=args.force)
        scope = file.is_data_file_ready(scope_path, LECROY_ACQUISITION_MERGING_PATH, force=args.force)
        etroc = file.is_data_file_ready(etroc_path, MODULE_TEST_SW_MERGING,          force=args.force)
        
        merged_file = os.path.join(
            OUTPUT_FILE_DIR(f_index), OUTPUT_FILENAME(f_index)
        )
        print(f"Merged file: {merged_file} | Already Exist? {os.path.isfile(merged_file)}")
        if reco and scope and etroc:
            print("All files are ready! Preparing merging on paths:")
            print(f"Reco data: {reco_path}")
            print(f"Scope data: {scope_path}")
            print(f"ETROC data: {etroc_path}")
            time.sleep(3)
            if args.replace and os.path.exists(merged_file):
                print(f"removing {merged_file}")
                os.remove(merged_file)

            reco_data  = uproot.open(reco_path)[RECO_TREE].arrays()
            scope_data = uproot.open(scope_path)[SCOPE_TREE].arrays()
            etroc_data = uproot.open(etroc_path)[ETROC_TREE].arrays()
            merge_trees(reco_data, scope_data, etroc_data, merged_file)
            if not args.no_sym_link: #so if they give no_sym_link flag this doesnt run...
                os.system(f"mv -f {merged_file} {BACKUP_FOLDER}")
                os.system(f"ln -nsf {os.path.join(BACKUP_FOLDER, OUTPUT_FILENAME(f_index))} {merged_file}")

            if args.runNumber!=-1: break #if I am specifying the run to merge I am only doing that one

            # Set status to False so new data can be taken
            file.write_status(LECROY_CONVERSION_MERGING_PATH,  False)
            file.write_status(LECROY_ACQUISITION_MERGING_PATH, False)
            file.write_status(MODULE_TEST_SW_MERGING,          False)

        main_loop = False