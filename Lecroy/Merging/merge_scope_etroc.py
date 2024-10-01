import uproot
import numpy as np
import os.path as path
import awkward as ak
from awkward.highlevel import Array as akArray
import time
import os
import argparse

#RAW_PATH = "/home/etl/Test_Stand/daq/LecroyMount/"  # PATH TO THE SCOPE RAW DATA FOLDER

def get_rising_edge_after_first_fall(nanoseconds: akArray, volts_scaled: akArray, thresh_low: int, thresh_high: int) -> tuple[akArray, akArray]:
    """
    INPUTS \n
    nanoseconds: array of arrays of times of the square wave in nanoseconds \n
    volts_scaled: array of arrays of the volts of the square waved scaled between 0 and 1 \n
    thresh_low and thresh_high: between 0 and 1, select the values of where the edges are, chops the bottom and top of the square wave respectively \n
    
    RETURNS \n
    Rising edge times and voltage values \n

    Returns the first rising edge of a square wave \n
    Algorithm STEPS: \n
    1. Make a mask of all falling edges from the square wave and get the indices of the square wave \n
        - edges decided by thresh_low and thresh high, and falling decided by taking the difference between neighboring points of V and checking the sign \n
    2. SELECT all points of the square wave AFTER the FALLING EDGE by checking for discontinuity in index (ex: 1,2,3,4,656 then remove 1,2,3,4) \n
    3. Make a mask of all edges and get the indices of the filtered square wave from step 2
    4. SELECT all points BEFORE the end of the first edge \n
        - which is gaurenteed to be a rising edge and is detected by this index discontinuity method \n
    5. Apply edge mask again to get just the first rising edge! \n
    """
    def edge_mask(V: akArray) -> akArray:
        return ((thresh_low <= V) & (V <= thresh_high))

    def get_idx_between_edgs(edg_idxs: akArray) -> akArray:
        #works like np.diff!
        edg_diffs = edg_idxs[:, 1:] - edg_idxs[:, :-1]
        #if there is a diff greater than one in index than we jumped to a new edge!
        return edg_idxs[edg_diffs > 1] + 1
    
    square_wave = ak.zip({
        "t": nanoseconds,
        'V': volts_scaled
    })
    # !!!!!!!!!see docstring for steps!!!!!!!!!
    # -------------[ STEP 1 ]---------------- #
    sw_idxs = ak.local_index(square_wave)
    falling_edg_mask = edge_mask(square_wave.V) & (np.diff(square_wave.V, append=np.inf) < 0)
    # -------------[ STEP 2 ]---------------- #
    #the [...,0] is important, grabs the first index out of each array, 99% of the time there is only one anyway
    falling_transition_idx = get_idx_between_edgs( sw_idxs[falling_edg_mask] )[...,0] 
    past_first_fall = sw_idxs[sw_idxs > falling_transition_idx[:,np.newaxis]]
    sw_pff = square_wave[past_first_fall]    

    # -------------[ STEP 3 ]---------------- #
    sw_pff_idxs = ak.local_index(sw_pff)
    all_edge_mask = edge_mask(sw_pff.V)
    #the [...,0] is important, grabs the first index out of each array, 99% of the time there is only one anyway
    # -------------[ STEP 4 ]---------------- #
    rising_edg_pff = get_idx_between_edgs( sw_pff_idxs[all_edge_mask] )[...,0]
    rising_after_falling = sw_pff_idxs[sw_pff_idxs < rising_edg_pff[:, np.newaxis]]
    sw_rising_pff = sw_pff[rising_after_falling]

    # -------------[ STEP 5 ]---------------- #
    e2mask = edge_mask(sw_rising_pff.V) #need to recut to just get rising edge
    return sw_rising_pff[e2mask].t, sw_rising_pff[e2mask].V

def calc_clock(seconds: akArray, volts: akArray) -> akArray:
    nanoseconds = seconds[:,0]*10**9
    #SCALE the voltage so values are between 0 and 1
    v_mins = ak.min(volts, axis=1, keepdims=True)
    v_maxs = ak.max(volts, axis=1, keepdims=True)
    volts_scaled = (volts - v_mins) / (v_maxs-v_mins)

    thresh_low, thresh_high = 0.25, 0.8
    rising_times, rising_volts = get_rising_edge_after_first_fall(nanoseconds, volts_scaled, thresh_low, thresh_high)
    fits = ak.linear_fit(rising_times, rising_volts, axis=-1)

    #0.5 is take the point halfway of the clock amplitude, since the voltages are scaled!!
    clock_stamp = (0.5 - fits['intercept'])/fits['slope'] # x = (y-b)/m
    return clock_stamp #nanoseconds

def merge_trees(files:list[str], trees:list[str], output_file:str) -> None:
    # Read ROOT files and trees
    ts = [uproot.open(files[t])[tree] for t, tree in enumerate(trees)]
    print(ts)
    datas = [t.arrays() for t in ts]
    lengths = [len(d) for d in datas]
    if np.all(np.array(lengths)==lengths[0]):
        print("All arrays have the same length")
    else:
        raise RuntimeError("Length mismatch of arrays, merging can't be done.")
    print(type(datas[0]))
    print(datas[1]["i_evt"])

    # -----------ADD CLOCK TO DATA-------------#
    scope_data = uproot.open(files[1])["pulse"]
    scope_channels = scope_data['channel'].array()
    CHANNEL_NUM = 2
    clock = calc_clock(
        scope_data['time'].array(), 
        scope_channels[:, CHANNEL_NUM]
    )
    print(len(clock))
    datas.append(ak.Array({"Clock": clock}))
    #------------------------------------------#

    # Merge the two datasets
    merged_data  = {}
    common_keys  = []
    other_keys_1 = []
    other_keys_2 = []

    for data in datas:
        for key in data.fields:
            if key not in merged_data.keys():
                merged_data[key] = data[key]

    print(merged_data.keys(), len(merged_data.keys()))
    # Create a new output file and write the merged tree
    with uproot.recreate(output_file) as output:
        output[trees[0]] = {key: merged_data[key] for key in merged_data.keys()}
        print(output[trees[0]].num_entries)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Run info.')
    parser.add_argument('--runNumber',metavar='runNumber', type=str,default = -1, help='runNumber (default -1)',required=False)
    parser.add_argument('--force', default=False, action='store_true', help='skip reco/merge/scope is running checks',required=False)
    parser.add_argument('--replace', default=False, action='store_true', help='If a merge file already exists, it deletes it and replaces it',required=False)

    args = parser.parse_args()
    # Replace these file names and tree names with your actual file names and tree names 
    # /home/etl/Test_Stand/daq/ETROC2_Test_Stand/ScopeHandler/Lecroy/Conversion/merging.txt
    base = "/home/etl/Test_Stand/ETROC2_Test_Stand/ScopeHandler"
    bkp_folder="/media/etl/Storage/"
    # os.system("./reset_merging.sh")
    if args.runNumber==-1:
        f_index=int(open(f"{base}/Lecroy/Acquisition/next_run_number.txt").read())
    else:
        f_index = int(args.runNumber)
    print(f_index, "\n")
    prev_status = 0

    main_loop = True
    while main_loop:
        reco_tree  = f"{base}/ScopeData/LecroyConverted/converted_run{f_index}.root"
        scope_tree = f"{base}/ScopeData/LecroyTimingDAQ/run_scope{f_index}.root"
        etroc_tree = f"{base}/ScopeData/ETROCData/output_run_{f_index}_rb0.root"

        #etroc_tree1 = f"{base}/ScopeData/ETROCData/{f_index}_rb0.root"
        #etroc_tree2 = f"{base}/ScopeData/ETROCData/{f_index}_rb1.root"
        reco_1 = (open(f"{base}/Lecroy/Conversion/merging.txt",                    "r").read() == "True")
        reco_2 = (path.isfile(reco_tree))
        reco = reco_1 and reco_2
        if args.force: 
            print(reco_2)
            reco = reco_2
            if not reco:
                print (f"Converted scope output ({reco_tree}) does not exist in force mode. Exiting")
                break
        scope_1 = (open(f"{base}/Lecroy/Acquisition/merging.txt",                  "r").read() == "True")
        scope_2 = (path.isfile(scope_tree))
        scope = scope_1 and scope_2
        if args.force: scope = scope_2
        etroc_1 = (open(f"/home/etl/Test_Stand/module_test_sw/merging.txt", "r").read() == "True")
        etroc_2 = (path.isfile(etroc_tree))
        #etroc_2 = (path.isfile(etroc_tree1) or path.isfile(etroc_tree2) )
        etroc = etroc_1 and etroc_2
        if args.force:
            etroc = etroc_2
            if not etroc:
                print("ETROC outputs does not exist in force mode. Exiting.")
                break
        
        #merged_file = f"{base}/ScopeData/LecroyMerged/run_{f_index}_rb0.root"
        merged_file = f"/home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/Lecroy/Merging/unit_test/run_{f_index}_rb0.root"
        #merged_file2 = f"{base}/ScopeData/LecroyMerged/run_{f_index}_rb1.root"
        status = sum([reco_1, reco_2, scope_1, scope_2, etroc_1, etroc_2, not path.isfile(merged_file)])

        if abs(status - prev_status) > 0:
            print( "                                  Flag      File")
            print(f"Acquisition from the scope done:  {scope_1}      {scope_2}")
            print(f"Acquisition from the KCU done:    {etroc_1}      {etroc_2}")
            print(f"Conversion done:                  {reco_1}      {reco_2}")
            print(f"Merged file was created:          {path.isfile(merged_file)}")
            print()

        if reco and scope and etroc: #and (not path.isfile(merged_file)):
            print("Secondary checking")
            print(reco)
            print(scope)
            print(etroc)
            print(not path.isfile(merged_file))
            print("\n")
            print(f"Reco data: {base}/ScopeData/LecroyConverted/converted_run{f_index}.root")
            print(f"Scope data: {base}/ScopeData/LecroyTimingDAQ/run_scope{f_index}.root")
            print(f"ETROC data: {etroc_tree}")
            #if path.isfile(etroc_tree1): 
            #    print(f"ETROC data: {etroc_tree1}")
            #    print(f"Merged data: {merged_file1}")
            #if path.isfile(etroc_tree2): 
            #    print(f"ETROC data: {etroc_tree2}")
            #    print(f"Merged data: {merged_file2}")
            time.sleep(3)
            if path.isfile(etroc_tree):
                try:
                    if args.replace and os.path.exists(merged_file):
                        print(f"removing {merged_file}")
                        os.remove(merged_file)
                    merge_trees([reco_tree, scope_tree, etroc_tree], ["pulse", "pulse", "pulse"], merged_file)
                    # os.system(f"mv -f {merged_file} {bkp_folder}LecroyMerged/")
                    # os.system(f"ln -nsf {bkp_folder}LecroyMerged/run_{f_index}_rb0.root {merged_file}")
                except RuntimeError:
                    print(f"Merging step failed for run { merged_file}")
            '''        
            if path.isfile(etroc_tree1):
                try:
                    merge_trees([reco_tree, scope_tree, etroc_tree1], ["pulse", "pulse", "pulse"], merged_file1)
                    os.system(f"mv {merged_file1} {bkp_folder}LecroyMerged/")
                    os.system(f"ln -s {bkp_folder}LecroyMerged/run_{f_index}_rb0.root {merged_file1}")
                except RuntimeError:
                    print(f"Merging step failed for run { merged_file1}")
            if path.isfile(etroc_tree2):
                try:
                    merge_trees([reco_tree, scope_tree, etroc_tree2], ["pulse", "pulse", "pulse"], merged_file2)
                    os.system(f"mv {merged_file2} {bkp_folder}LecroyMerged/")
                    os.system(f"ln -s {bkp_folder}LecroyMerged/run_{f_index}_rb1.root {merged_file2}")
                except RuntimeError:
                    print(f"Merging step failed for run { merged_file2}")
            '''

            if args.runNumber!=-1: break #if I am specifying the run to merge I am only doing that one

            # print("Merging done!")
            # except Exception as error:
            #     print(repr(error))
            f_index = int(open(f"{base}/Lecroy/Acquisition/next_run_number.txt").read())
            print("\n", f_index, "\n")
            f = open(f"{base}/Lecroy/Conversion/merging.txt", "w")
            f.write("False")
            f.truncate()
            f.close()
            f = open(f"{base}/Lecroy/Acquisition/merging.txt", "w")
            f.write("False")
            f.truncate()
            f.close()
            f = open(f"/home/etl/Test_Stand/ETROC2_Test_Stand/module_test_sw/merging.txt", "w")
            f.write("False")
            f.truncate()
            f.close()
        time.sleep(1)
        prev_status = status

        main_loop = False