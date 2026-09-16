 ## Instructions for Running SNSPD waveform conversion on FNAL Spot 2 Computer

 Need the ROOT package, will use a specific mamba environment \
 Navigate to this directory \
 `ScopeHandler/Lecroy/Conversion' \
 
 Run `mamba activate root_env` \

 Copy the traces to this directory. The code expects them to have a name in the format `C<channel number>--Trace<run number>.trc`. Right now, the main conversion script is set to run 2 channels, expecting channels 1 and 2 to have input files. This can be changed in the code by hand.\
 
 Run `python3 conversion.py --runNumber <run number>` \
 The output should be a single root file in this directory with name `converted_run<run number>.root`

 To inspect the output, run `root -l <output file>`
 A quick command to check that the waveform looks ok is \
 `pulse->Draw("channel[<channel number>]:time[0]","i_evt==<event number>","L")`\
 You can run `.q` in the root terminal to exit root

 To exit the environment run \
 `conda deactivate root_env`
 
