import numpy as np
import sys
import optparse
import argparse
import signal
import os
import time
import shutil
import datetime
from shutil import copy
import pyvisa as visa
import glob
import pdb

"""#################SEARCH/CONNECT#################"""
# establish communication with scope
initial = time.time()
rm = visa.ResourceManager("@py")
lecroy = rm.open_resource('TCPIP0::192.168.0.6::INSTR')
lecroy.timeout = 3000000
lecroy.encoding = 'latin_1'
lecroy.clear()

run_log_path = "/home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/Lecroy/Acquisition/RunLog.txt"

def GetNextNumber():
    run_num_file = "/home/etl/Test_Stand/ETL_TestingDAQ/ScopeHandler/Lecroy/Acquisition/next_run_number.txt"
    with open(run_num_file) as file:
        nextNumber = int(file.read().strip())
    with open(run_num_file, "w") as file:
        file.write(f"{nextNumber + 1}\n")
    return nextNumber

nchan=4

parser = argparse.ArgumentParser(description='Run info.')

parser.add_argument('--numEvents',metavar='Events', type=str,default = 500, help='numEvents (default 500)',required=False)
parser.add_argument('--runNumber',metavar='runNumber', type=str,default = -1, help='runNumber (default -1)',required=False)
parser.add_argument('--sampleRate',metavar='sampleRate', type=str,default = 10, help='Sampling rate (default 10)',required=False)
parser.add_argument('--horizontalWindow',metavar='horizontalWindow', type=str,default = 50, help='horizontal Window (default 125)',required=False)
# parser.add_argument('--numPoints',metavar='Points', type=str,default = 500, help='numPoints (default 500)',required=True)
parser.add_argument('--trigCh',metavar='trigCh', type=str, default='C2',help='trigger Channel (EX, or CN',required=False)
parser.add_argument('--trig',metavar='trig', type=float, default= 0.150, help='trigger value in V',required=False)
parser.add_argument('--trigSlope',metavar='trigSlope', type=str, default= 'NEGative', help='trigger slope; positive(rise) or negative(fall)',required=False)

parser.add_argument('--vScale1',metavar='vScale1', type=float, default= 0.05, help='Vertical scale, volts/div',required=False)
parser.add_argument('--vScale2',metavar='vScale2', type=float, default= 0.05, help='Vertical scale, volts/div',required=False)
parser.add_argument('--vScale3',metavar='vScale3', type=float, default= 0.05, help='Vertical scale, volts/div',required=False)
parser.add_argument('--vScale4',metavar='vScale4', type=float, default= 0.05, help='Vertical scale, volts/div',required=False)
# parser.add_argument('--vScale5',metavar='vScale5', type=float, default= 0.05, help='Vertical scale, volts/div',required=False)
# parser.add_argument('--vScale6',metavar='vScale6', type=float, default= 0.05, help='Vertical scale, volts/div',required=False)
# parser.add_argument('--vScale7',metavar='vScale7', type=float, default= 0.05, help='Vertical scale, volts/div',required=False)
# parser.add_argument('--vScale8',metavar='vScale8', type=float, default= 0.05, help='Vertical scale, volts/div',required=False)

parser.add_argument('--vPos1',metavar='vPos1', type=float, default= 3, help='Vertical Pos, div',required=False)
parser.add_argument('--vPos2',metavar='vPos2', type=float, default= 3, help='Vertical Pos, div',required=False)
parser.add_argument('--vPos3',metavar='vPos3', type=float, default= 3, help='Vertical Pos, div',required=False)
parser.add_argument('--vPos4',metavar='vPos4', type=float, default= 3, help='Vertical Pos, div',required=False)
# parser.add_argument('--vPos5',metavar='vPos5', type=float, default= 3, help='Vertical Pos, div',required=False)
# parser.add_argument('--vPos6',metavar='vPos6', type=float, default= 3, help='Vertical Pos, div',required=False)
# parser.add_argument('--vPos7',metavar='vPos7', type=float, default= 3, help='Vertical Pos, div',required=False)
# parser.add_argument('--vPos8',metavar='vPos8', type=float, default= 3, help='Vertical Pos, div',required=False)

parser.add_argument('--display',metavar='display', type=int, default= 0, help='enable display',required=False)
parser.add_argument('--timeoffset',metavar='timeoffset', type=float, default=0, help='Offset to compensate for trigger delay. This is the delta T between the center of the acquisition window and the trigger. (default for NimPlusX: -160 ns)',required=False)

# parser.add_argument('--save',metavar='save', type=int, default= 1, help='Save waveforms',required=False)
# parser.add_argument('--timeout',metavar='timeout', type=float, default= -1, help='Max run duration [s]',required=False)

args = parser.parse_args()
trigCh = str(args.trigCh)
runNumber = int(args.runNumber)
if trigCh != "AUX": trigCh = 'CHANnel'+trigCh
trigLevel = float(args.trig)
triggerSlope = args.trigSlope
timeoffset = float(args.timeoffset)*1e-9
# print "timeoffset is ",timeoffset
date = datetime.datetime.now()
# savewaves = int(args.save)
# timeout = float(args.timeout)
# print savewaves
# print "timeout is ",timeout

if runNumber==-1:
	runNumber=GetNextNumber()
#### Initial preparation
print(f"Next run number: {runNumber}")
print(f"\n \nPreparing {nchan}-channel scope. \n")
lecroy.write('STOP')
lecroy.write("*CLS")
lecroy.write("COMM_HEADER OFF")
if args.display == 0: lecroy.write("DISPLAY ON")
else: 
    lecroy.write("DISPLAY ON")
    lecroy.write('DISPLAY:ACQUIRE:COUNT ON')

####### Vertical setup ######
vScales_in_mV = []
vScales_in_mV.append(int(1000* args.vScale1))
vScales_in_mV.append(int(1000* args.vScale2))
vScales_in_mV.append(int(1000* args.vScale3))
vScales_in_mV.append(int(1000* args.vScale4))
# vScales_in_mV.append(int(1000* args.vScale5))
# vScales_in_mV.append(int(1000* args.vScale6))
# vScales_in_mV.append(int(1000* args.vScale7))
# vScales_in_mV.append(int(1000* args.vScale8))

vOffsets_in_mV = []
vOffsets_in_mV.append(int(1000* args.vScale1 * args.vPos1))
vOffsets_in_mV.append(int(1000* args.vScale2 * args.vPos2))
vOffsets_in_mV.append(int(1000* args.vScale3 * args.vPos3))
vOffsets_in_mV.append(int(1000* args.vScale4 * args.vPos4))
# vOffsets_in_mV.append(int(1000* args.vScale5 * args.vPos5))
# vOffsets_in_mV.append(int(1000* args.vScale6 * args.vPos6))
# vOffsets_in_mV.append(int(1000* args.vScale7 * args.vPos7))
# vOffsets_in_mV.append(int(1000* args.vScale8 * args.vPos8))
print("Vertical setup.")
# for chan in range(1,nchan+1):
for chan in range(2,nchan): #20GS/s
    print(f"\tChannel {chan}: {vScales_in_mV[chan-1]} mV/div, {vOffsets_in_mV[chan-1]} mV offset.")
    lecroy.write(f"C{chan}:COUPLING D50")
    lecroy.write(f"C{chan}:VOLT_DIV {vScales_in_mV[chan-1]}MV")
    lecroy.write(f"C{chan}:OFFSET {vOffsets_in_mV[chan-1]}MV")

### Disable bandwidth limit
lecroy.write("BANDWIDTH_LIMIT OFF")

####### Horizontal setup ########

time_div_in_ns = int(args.horizontalWindow)/10 ## specify full window as argument
print(f"\nTimebase: {time_div_in_ns} ns/div.")
if time_div_in_ns != 2 and time_div_in_ns != 5 and time_div_in_ns!=500000 and time_div_in_ns!=1000000:
	print("Warning: time base must fit predefined set of possible values.")
sample_rate_in_GS = args.sampleRate

lecroy.write(f"TIME_DIV {time_div_in_ns}NS")
# print("\tMake sure sampling rate is set to 10 GS/s manually.")
print("\tMake sure sampling rate is set to 20 GS/s manually.") #20GS/s
# lecroy.write("TIME_DIV e-9")

print(f"Setting horizontal offset 50 {args.timeoffset} ns")
lecroy.write(f"TRIG_DELAY {args.timeoffset} ns")
print(args.trigCh)

####### Trigger setup ######
lecroy.write("TRIG_SELECT Edge,SR,%s"%args.trigCh)

if args.trigCh != "LINE":
    lecroy.write(f"{args.trigCh}:TRLV {args.trig:.3f}V")
    lecroy.write(f"TRIG_SLOPE {args.trigSlope}")

print(f"\nTriggering on {args.trigCh} with {args.trig:.3f}V threshold, {args.trigSlope} polarity.")
#lecroy.write("TRIG_SELECT Edge,SR,LINE")
#lecroy.write("TRIG_SELECT Edge,SR,EX")
# lecroy.write("EX:TRSL POS")
# lecroy.write("EX:TRLV 0.15V")
# lecroy.write("EX:TRSL POS")

lecroy.write("STORE_SETUP ALL_DISPLAYED,HDD,AUTO,OFF,FORMAT,BINARY")
# lecroy.write("STORE_SETUP C1,HDD,AUTO,OFF,FORMAT,BINARY")

nevents = int(args.numEvents)
##Sequence configuration
print(f"\nTaking {nevents} events in sequence mode.")
lecroy.write(f"SEQ ON,{nevents}")

with open(run_log_path, "w") as run_logf:
    run_logf.write("busy")
    # run_logf.write("\n")
start = time.time()
now = datetime.datetime.now()
current_time = now.strftime("%H:%M:%S")
# pdb.set_trace()
print("\n \n \n  -------------  Starting acquisition for run %i at %s. ---------------"%(runNumber,current_time))
lecroy.write("*TRG")
#prewait = time.time()
#lecroy.query(r"""vbs? 'app.waituntilidle(7)' """)
#time.sleep(7)
#postwait=time.time()
#print "wait until idle took %i seconds."%(postwait-prewait)

# lecroy.write("ARM")
lecroy.write("WAIT")

#time.sleep(10)
#print "Finished waiting, attempting stop."
#lecroy.write("STOP;*OPC?")
#lecroy.write("STOP")
#time.sleep(10)
# lecroy.write("WAIT")

lecroy.query("ALST?")

end = time.time()
duration = end-start
print("\n \n \n  -------------  Acquisition complete.   ------------------------")
print("\tAcquisition duration: %0.4f s"%duration)
print("\tTrigger rate: %0.1f Hz" %(nevents/duration))

# print("Storage configuration:")
# print(lecroy.query("STORE_SETUP?"))
print("\n\n  -------------  Beginning save waveforms.  ----------------------")
with open(run_log_path, "w") as tmp_file:
    tmp_file.write("writing")
    tmp_file.write("\n")

start = time.time()
### save all active channels with single command, using ALL_DISPLAYED ###
lecroy.write(r"""vbs 'app.SaveRecall.Waveform.TraceTitle="Trace%i" ' """%(runNumber))
lecroy.write(r"""vbs 'app.SaveRecall.Waveform.SaveFile' """)
lecroy.write("STORE")
# for ichan in range(1,nchan+1):
#     lecroy.write("STORE_SETUP C%i,HDD,AUTO,OFF,FORMAT,BINARY"%ichan)
#     lecroy.write(r"""vbs 'app.SaveRecall.Waveform.SaveFilename="C%i--Trace%i.trc" ' """%(ichan,int(runNumber)))
#     lecroy.write(r"""vbs 'app.SaveRecall.Waveform.SaveFile' """)

# for ichan in range(1,nchan+1):
for ichan in range(2,nchan):#20GS/s
    print(f"Saving channel {ichan}")
    lecroy.write(f"STORE_SETUP C{ichan},HDD,AUTO,OFF,FORMAT,BINARY")
    lecroy.write(r"""vbs 'app.SaveRecall.Waveform.SaveFilename="C%i--Trace%i.trc" ' """%(ichan,int(runNumber)))
    lecroy.write(r"""vbs 'app.SaveRecall.Waveform.SaveFile' """)
    lecroy.query("ALST?")

lecroy.query("ALST?")
end = time.time()
print(f"Waveform storage complete. \n\tStoring waveforms took {end - start:.4f} s")
#time.sleep(0.5)

## renaming files with automatic numbering scheme.. no lnoger needed.
# list_of_files = glob.glob('/home/etl/Test_Stand/daq/LecroyMount/*.trc') 
# latest_file = max(list_of_files, key=os.path.getctime)

#autoRunNum = latest_file.split("Trace")[1].split(".trc")[0]
#print "Lecroy run number: %s. Renaming to run %s."%(autoRunNum,runNumber)
#for chan in range(1,nchan+1):
#	os.rename("/home/etl/Test_Stand/daq/LecroyMount/C%iTrace%s.trc" % (chan,autoRunNum), "/home/etl/Test_Stand/daq/LecroyMount/C%iTrace%s.trc" % (chan,runNumber))

#lecroy.write("WAIT")

for x in range(1,10):
    time.sleep(0.5)
    lecroy.write("*OPC?")

lecroy.close()
rm.close()

final = time.time()
print(f"\nFinished run {runNumber}.")
print(f"Full script duration: {final - initial:.0f} s")
with open(run_log_path, "w") as tmp_file2:
    tmp_file2.write("ready")
    tmp_file2.write("\n")