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
import visa
import glob
import subprocess

"""#################SEARCH/CONNECT#################"""
# establish communication with scope
initial = time.time()
rm = visa.ResourceManager("@py")
lecroy = rm.open_resource('TCPIP0::192.168.0.12::INSTR')
lecroy.timeout = 3000000
lecroy.encoding = 'latin_1'
lecroy.clear()
BASE_PATH = "/home/daq/2025_07_FCFD/ScopeHandler/"
run_log_path = BASE_PATH + "/Lecroy/Acquisition/RunLog.txt"


def GetNextNumber():
    run_num_file = BASE_PATH + "/Lecroy/Acquisition/next_run_number.txt"
    FileHandle = open(run_num_file)
    nextNumber = int(FileHandle.read().strip())
    FileHandle.close()
    FileHandle = open(run_num_file,"w")
    FileHandle.write(str(nextNumber+1)+"\n") 
    FileHandle.close()
    return nextNumber

nchan=8

parser = argparse.ArgumentParser(description='Run info.')

parser.add_argument('--numEvents',metavar='Events', type=str,default = 500, help='numEvents (default 500)',required=False)
parser.add_argument('--runNumber',metavar='runNumber', type=str,default = -1, help='runNumber (default -1)',required=False)
parser.add_argument('--sampleRate',metavar='sampleRate', type=str,default = 10, help='Sampling rate (default 20)',required=False)
parser.add_argument('--horizontalWindow',metavar='horizontalWindow', type=str,default = 50, help='horizontal Window (default 125)',required=False)
# parser.add_argument('--numPoints',metavar='Points', type=str,default = 500, help='numPoints (default 500)',required=True)
parser.add_argument('--trigCh',metavar='trigCh', type=str, default='EX',help='trigger Channel (EX, or CN',required=False)
parser.add_argument('--trig',metavar='trig', type=float, default= 0.150, help='trigger value in V',required=False)
parser.add_argument('--trigSlope',metavar='trigSlope', type=str, default= 'NEGative', help='trigger slope; positive(rise) or negative(fall)',required=False)

parser.add_argument('--vScale1',metavar='vScale1', type=float, default= 0.05, help='Vertical scale, volts/div',required=False)
parser.add_argument('--vScale2',metavar='vScale2', type=float, default= 0.05, help='Vertical scale, volts/div',required=False)
parser.add_argument('--vScale3',metavar='vScale3', type=float, default= 0.05, help='Vertical scale, volts/div',required=False)
parser.add_argument('--vScale4',metavar='vScale4', type=float, default= 0.05, help='Vertical scale, volts/div',required=False)
parser.add_argument('--vScale5',metavar='vScale5', type=float, default= 0.05, help='Vertical scale, volts/div',required=False)
parser.add_argument('--vScale6',metavar='vScale6', type=float, default= 0.05, help='Vertical scale, volts/div',required=False)
parser.add_argument('--vScale7',metavar='vScale7', type=float, default= 0.05, help='Vertical scale, volts/div',required=False)
parser.add_argument('--vScale8',metavar='vScale8', type=float, default= 0.05, help='Vertical scale, volts/div',required=False)

parser.add_argument('--vPos1',metavar='vPos1', type=float, default= 3, help='Vertical Pos, div',required=False)
parser.add_argument('--vPos2',metavar='vPos2', type=float, default= 3, help='Vertical Pos, div',required=False)
parser.add_argument('--vPos3',metavar='vPos3', type=float, default= 3, help='Vertical Pos, div',required=False)
parser.add_argument('--vPos4',metavar='vPos4', type=float, default= 3, help='Vertical Pos, div',required=False)
parser.add_argument('--vPos5',metavar='vPos5', type=float, default= 3, help='Vertical Pos, div',required=False)
parser.add_argument('--vPos6',metavar='vPos6', type=float, default= 3, help='Vertical Pos, div',required=False)
parser.add_argument('--vPos7',metavar='vPos7', type=float, default= 3, help='Vertical Pos, div',required=False)
parser.add_argument('--vPos8',metavar='vPos8', type=float, default= 3, help='Vertical Pos, div',required=False)

parser.add_argument('--display',metavar='display', type=int, default= 0, help='enable display',required=False)


parser.add_argument('--timeoffset',metavar='timeoffset', type=float, default=0, help='Offset to compensate for trigger delay. This is the delta T between the center of the acquisition window and the trigger. (default for NimPlusX: -160 ns)',required=False)
parser.add_argument('--holdoff',metavar='holdoff', type=float, default=0, help='trigger hold off time in units of ns, default is 0',required=False)
parser.add_argument('--auxOutPulseWidth',metavar='args.auxOutPulseWidth', type=float, default=0, help='Aux Output Pulse Width',required=False)

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
print "Next run number: %i"%runNumber

print "\n \nPreparing 8-channel scope. \n"
lecroy.write('STOP')
lecroy.write("*CLS")
lecroy.write("COMM_HEADER OFF")
if args.display == 0: lecroy.write("DISPLAY OFF")
else: lecroy.write("DISPLAY ON")

####### Vertical setup ######

vScales_in_mV = []
vScales_in_mV.append(int(1000* args.vScale1))
vScales_in_mV.append(int(1000* args.vScale2))
vScales_in_mV.append(int(1000* args.vScale3))
vScales_in_mV.append(int(1000* args.vScale4))
vScales_in_mV.append(int(1000* args.vScale5))
vScales_in_mV.append(int(1000* args.vScale6))
vScales_in_mV.append(int(1000* args.vScale7))
vScales_in_mV.append(int(1000* args.vScale8))

vOffsets_in_mV = []
vOffsets_in_mV.append(int(1000* args.vScale1 * args.vPos1))
vOffsets_in_mV.append(int(1000* args.vScale2 * args.vPos2))
vOffsets_in_mV.append(int(1000* args.vScale3 * args.vPos3))
vOffsets_in_mV.append(int(1000* args.vScale4 * args.vPos4))
vOffsets_in_mV.append(int(1000* args.vScale5 * args.vPos5))
vOffsets_in_mV.append(int(1000* args.vScale6 * args.vPos6))
vOffsets_in_mV.append(int(1000* args.vScale7 * args.vPos7))
vOffsets_in_mV.append(int(1000* args.vScale8 * args.vPos8))
print "Vertical setup."
for chan in range(1,nchan+1):
	print "\tChannel %i: %i mV/div, %i mV offset. "% (chan, vScales_in_mV[chan-1],vOffsets_in_mV[chan-1])
	lecroy.write("C%i:TRA ON"%(chan))
	lecroy.write("C%i:COUPLING D50"%(chan))
	lecroy.write("C%i:VOLT_DIV %iMV"%(chan, vScales_in_mV[chan-1]))
	lecroy.write("C%i:OFFSET %iMV"%(chan, vOffsets_in_mV[chan-1]))

### Disable bandwidth limit
lecroy.write("BANDWIDTH_LIMIT OFF")


####### Horizontal setup ########

time_div_in_ns = int(args.horizontalWindow)/10 ## specify full window as argument
print "\nTimebase: %i ns/div." % time_div_in_ns
if time_div_in_ns != 2 and time_div_in_ns != 5 and time_div_in_ns!=500000 and time_div_in_ns!=1000000:
	print "Warning: time base must fit predefined set of possible values."
sample_rate_in_GS = args.sampleRate

lecroy.write("TIME_DIV %iNS"%time_div_in_ns)
print "\tMake sure sampling rate is set to 10 GS/s manually."
# lecroy.write("TIME_DIV e-9")

print "Setting horizontal offset 50 %i ns" %args.timeoffset
lecroy.write("TRIG_DELAY %i ns"%args.timeoffset)


####### Trigger setup #####
if args.holdoff > 0: lecroy.write("TRIG_SELECT Edge,SR,%s,HT,TI,HV,%0.3f NS"% (args.trigCh, args.holdoff))
else:lecroy.write("TRIG_SELECT Edge,SR,%s, HT, OFF" % args.trigCh) 
print("\nTrigger holdoff time is %0.3f ns" % args.holdoff)
if args.trigCh != "LINE":
	lecroy.write("%s:TRLV %0.3fV"%(args.trigCh,args.trig))
	lecroy.write("TRIG_SLOPE %s" %args.trigSlope)

print "Triggering on %s with %0.3fV threshold, %s polarity." %(args.trigCh,args.trig,args.trigSlope)

####### Trigger Aux Out Setup ######
if args.auxOutPulseWidth > 0:
	lecroy.write(r"""vbs 'app.Acquisition.AuxOutput.AuxMode = "TriggerOut"' """)
	lecroy.write(r"""vbs 'app.Acquisition.AuxOutput.TrigOutPulseWidth = "%d ns"' """ % args.auxOutPulseWidth)
	print("Trigger Aux Output Pulse Width: %d ns" % args.auxOutPulseWidth)
else:
	lecroy.write(r"""vbs 'app.Acquisition.AuxOutput.AuxMode = "Off"' """)
	print("No Trigger Aux Output Set")


#lecroy.write("TRIG_SELECT Edge,SR,LINE")
#lecroy.write("TRIG_SELECT Edge,SR,EX")
# lecroy.write("EX:TRSL POS")
# lecroy.write("EX:TRLV 0.15V")
# lecroy.write("EX:TRSL POS")

lecroy.write("STORE_SETUP ALL_DISPLAYED,HDD,AUTO,OFF,FORMAT,BINARY")
# lecroy.write("STORE_SETUP C1,HDD,AUTO,OFF,FORMAT,BINARY")

nevents = int(args.numEvents)
##Sequence configuration
print "\nTaking %i events in sequence mode."%nevents
lecroy.write("SEQ ON,%i"%nevents)
status = ""
status = "busy"

run_logf = open(run_log_path,"w")
run_logf.write(status)
#run_logf.write("\n")
run_logf.close()
start = time.time()
now = datetime.datetime.now()
current_time = now.strftime("%H:%M:%S")
print "\n \n \n  -------------  Starting acquisition for run %i at %s. ---------------"%(runNumber,current_time)
lecroy.write("*TRG")
#prewait = time.time()
#lecroy.query(r"""vbs? 'app.waituntilidle(7)' """)
#time.sleep(7)
#postwait=time.time()
#print "wait until idle took %i seconds."%(postwait-prewait)


#lecroy.write("ARM")
lecroy.write("WAIT")
#ime.sleep(10)
#print "Finished waiting, attempting stop."
#lecroy.write("STOP;*OPC?")
#lecroy.write("STOP")
#time.sleep(10)
# lecroy.write("WAIT")



lecroy.query("ALST?")

end = time.time()
duration = end-start
print "\n \n \n  -------------  Acquisition complete.   ------------------------"
print "\tAcquisition duration: %0.4f s"%duration
print "\tTrigger rate: %0.1f Hz" %(nevents/duration)

# print("Storage configuration:")
# print(lecroy.query("STORE_SETUP?"))
print("\n\n  -------------  Beginning save waveforms.  ----------------------")
tmp_file = open(run_log_path,"w")
status = "writing"
tmp_file.write(status)
tmp_file.write("\n")
tmp_file.close()


start = time.time()
### save all active channels with single command, using ALL_DISPLAYED ###
lecroy.write(r"""vbs 'app.SaveRecall.Waveform.TraceTitle="Trace%i" ' """%(runNumber))
lecroy.write(r"""vbs 'app.SaveRecall.Waveform.SaveFile' """)
#lecroy.write("STORE")
#for ichan in range(1,9):
#	lecroy.write("STORE_SETUP C%i,HDD,AUTO,OFF,FORMAT,BINARY"%ichan)
	#lecroy.write(r"""vbs 'app.SaveRecall.Waveform.SaveFilename="C%i--Trace%i.trc" ' """%(ichan,int(runNumber)))
	#lecroy.write(r"""vbs 'app.SaveRecall.Waveform.SaveFile' """)

# for ichan in range(1,9):
#        print "Saving channel %i"%ichan
#        lecroy.write("STORE_SETUP C%i,HDD,AUTO,OFF,FORMAT,BINARY"%ichan)
#        lecroy.write(r"""vbs 'app.SaveRecall.Waveform.SaveFilename="C%i--Trace%i.trc" ' """%(ichan,int(runNumber)))
#        lecroy.write(r"""vbs 'app.SaveRecall.Waveform.SaveFile' """)
#        lecroy.query("ALST?")

lecroy.query("ALST?")
end = time.time()


print("Waveform storage complete. \n\tStoring waveforms took %0.4f s" % (end - start))
#time.sleep(0.5)

## renaming files with automatic numbering scheme.. no lnoger needed.
#list_of_files = glob.glob('/home/daq/LecroyMount/*.trc') 
#latest_file = max(list_of_files, key=os.path.getctime)

#autoRunNum = latest_file.split("Trace")[1].split(".trc")[0]
#print "Lecroy run number: %s. Renaming to run %s."%(autoRunNum,runNumber)
#for chan in range(1,nchan+1):
#	os.rename("/home/daq/LecroyMount/C%iTrace%s.trc" % (chan,autoRunNum), "/home/daq/LecroyMount/C%iTrace%s.trc" % (chan,runNumber))

#lecroy.write("WAIT")

# for x in xrange(1,10):
# 	time.sleep(0.5)
# 	lecroy.write("OPC?")

lecroy.close()
rm.close()
final = time.time()
print "\nFinished run %i."%runNumber
print "Full script duration: %0.f s"%(final-initial)
tmp_file2 = open(run_log_path,"w")
status = "ready"
tmp_file2.write(status)
tmp_file2.write("\n")
tmp_file2.close()
 







