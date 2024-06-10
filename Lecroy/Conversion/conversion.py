import struct  #struct unpack result - tuple
import numpy as np
from ROOT import *
import time
import optparse
import argparse
import os
import sys

nchan=8

parser = argparse.ArgumentParser(description='Run info.')
parser.add_argument('--runNumber',metavar='runNumber', type=str,default = -1, help='runNumber (default -1)',required=False)
args = parser.parse_args()

initial = time.time()

RawDataPath = ""
RawDataLocalCopyPath = ""
BasePath = "2024_05_SNSPD_FCFD_ETL"
OutputFilePath = "/home/daq/%s/LecroyScope/RecoData/ConversionRECO/" % BasePath
eosPath = "root://cmseos.fnal.gov//store/group/cmstestbeam/%s/LecroyScope/RecoData/ConversionRECO/"  % BasePath

LocalMode=True
CopyToEOS=True
isLPC = False

if os.path.exists("_condor_stdout"):
	print("Detected condor")
	LocalMode=False
else:
    try:
        user = os.environ['USER']
        isLPC = 'cmslpc' in os.environ['HOSTNAME']
    except:
        print("Failed to find environment")
    if isLPC:
        print("Found user: {} Running on LPC: {}".format(user, isLPC))
        LocalMode = False
if LocalMode:
	RawDataPath = "/home/daq/LecroyMount/"
	RawDataLocalCopyPath = "/home/daq/%s/LecroyScope/RawData/" % BasePath
if not LocalMode:
        OutputFilePath = ""



#### Memory addresses #####
WAVEDESC=11
aTEMPLATE_NAME		= WAVEDESC+ 16;
aCOMM_TYPE			= WAVEDESC+ 32;
aCOMM_ORDER			= WAVEDESC+ 34;
aWAVE_DESCRIPTOR	= WAVEDESC+ 36;	# length of the descriptor block
aUSER_TEXT			= WAVEDESC+ 40;	# length of the usertext block
aTRIGTIME_ARRAY     = WAVEDESC+ 48;
aWAVE_ARRAY_1		= WAVEDESC+ 60;	# length (in Byte) of the sample array
aINSTRUMENT_NAME	= WAVEDESC+ 76;
aINSTRUMENT_NUMBER  = WAVEDESC+ 92;
aTRACE_LABEL		= WAVEDESC+ 96;
aWAVE_ARRAY_COUNT	= WAVEDESC+ 116;
aPNTS_PER_SECREEN = WAVEDESC+120
aFIRST_VALID_PNT = WAVEDESC+124
aLAST_VALID_PNT = WAVEDESC+128
aSEGMENT_INDEX = WAVEDESC+140;
aSUBARRAY_COUNT = WAVEDESC+144
aNOM_SUBARRAY_COUNT = WAVEDESC+174
aVERTICAL_GAIN		= WAVEDESC+ 156;
aVERTICAL_OFFSET	= WAVEDESC+ 160;
aNOMINAL_BITS		= WAVEDESC+ 172;
aHORIZ_INTERVAL     = WAVEDESC+ 176;
aHORIZ_OFFSET		= WAVEDESC+ 180;
aVERTUNIT			= WAVEDESC+ 196;
aHORUNIT			= WAVEDESC+ 244;
aTRIGGER_TIME		= WAVEDESC+ 296;
aACQ_DURATION = WAVEDESC+312;
aRECORD_TYPE		= WAVEDESC+ 316;
aPROCESSING_DONE	= WAVEDESC+ 318;
aTIMEBASE			= WAVEDESC+ 324;
aVERT_COUPLING		= WAVEDESC+ 326;
aPROBE_ATT			= WAVEDESC+ 328;
aFIXED_VERT_GAIN	= WAVEDESC+ 332;
aBANDWIDTH_LIMIT	= WAVEDESC+ 334;
aVERTICAL_VERNIER	= WAVEDESC+ 336;
aACQ_VERT_OFFSET	= WAVEDESC+ 340;
aWAVE_SOURCE		= WAVEDESC+ 344;



def dump_info(filepath_in, index_in,n_points):
	x_axis = []
	y_axis = []

	# read from file
	my_index = index_in
	# start = time.time()
	my_file = open(filepath_in, 'rb')
	#WAVEDESC = my_file.read(50).find("WAVEDESC")
	#WAVEDESC = 11
	#print WAVEDESC
	my_file.seek(aCOMM_ORDER)
	comm_order = struct.unpack('h',my_file.read(2))
	print("Comm order",comm_order)
	my_file.seek(aCOMM_TYPE)
	comm_type = struct.unpack('h',my_file.read(2))
	print("Comm type",comm_type)

	my_file.seek(WAVEDESC+16)
	template_name= my_file.read(16)
	print(template_name)
	my_file.seek(WAVEDESC+76)
	# instrument_name = struct.unpack('s',my_file.read(16))
	instrument_name = my_file.read(16)
	print(instrument_name)

	my_file.seek(aWAVE_SOURCE)
	print("Wave source index is ",struct.unpack('h',my_file.read(2)))
	my_file.seek(aVERT_COUPLING)
	print("Vert coupling index is ",struct.unpack('h',my_file.read(2)))
	my_file.seek(aBANDWIDTH_LIMIT)
	print("Bandwith limiting index is ",struct.unpack('h',my_file.read(2)))
	my_file.seek(aRECORD_TYPE)
	print("Record type index is ",struct.unpack('h',my_file.read(2)))
	my_file.seek(aVERTICAL_GAIN)
	vertical_gain = struct.unpack('f',my_file.read(4))[0]
	print("Vertical gain is ",vertical_gain)
	my_file.seek(aVERTICAL_OFFSET)
	print("Vertical offset is ",struct.unpack('f',my_file.read(4)))
	my_file.seek(aFIXED_VERT_GAIN)
	print("Fixed vertical gain index is",struct.unpack('h',my_file.read(2)))
	my_file.seek(aNOMINAL_BITS)
	print("Nominal bits is ",struct.unpack('h',my_file.read(2)))
	my_file.seek(aHORIZ_INTERVAL)
	print("Horizontal interval is ",struct.unpack('f',my_file.read(4)))	
	my_file.seek(aHORIZ_OFFSET)
	print("Horizontal offset is ",struct.unpack('d',my_file.read(8)))	

	my_file.seek(aWAVE_DESCRIPTOR)
	wave_descriptor = struct.unpack('i',my_file.read(4))
	print("descriptor is ",wave_descriptor)

	my_file.seek(aUSER_TEXT)
	USER_TEXT			= struct.unpack('i',my_file.read(4))#ReadLong(fid, aUSER_TEXT);
	my_file.seek(aWAVE_ARRAY_1)
	WAVE_ARRAY_1		= struct.unpack('i',my_file.read(4))
	my_file.seek(aWAVE_ARRAY_COUNT)
	WAVE_ARRAY_COUNT    = struct.unpack('i',my_file.read(4))
	my_file.seek(aPNTS_PER_SECREEN)
	PNTS_PER_SCREEN    = struct.unpack('i',my_file.read(4))
	my_file.seek(aTRIGTIME_ARRAY)
	TRIGTIME_ARRAY      = struct.unpack('i',my_file.read(4))

	my_file.seek(aSEGMENT_INDEX)
	SEGMENT_INDEX      = struct.unpack('i',my_file.read(4))
	my_file.seek(aSUBARRAY_COUNT)
	SUBARRAY_COUNT      = struct.unpack('i',my_file.read(4))
	print("Actual segment count: ",SUBARRAY_COUNT)
	my_file.seek(aNOM_SUBARRAY_COUNT)
	NOM_SUBARRAY_COUNT      = struct.unpack('h',my_file.read(2))
	print("Target segment count: ",NOM_SUBARRAY_COUNT)

	my_file.seek(aTRIGGER_TIME)
	TRIGGER_TIME      = struct.unpack('d',my_file.read(8))

	my_file.seek(aACQ_DURATION)
	ACQ_DURATION      = struct.unpack('f',my_file.read(4))

	print("User text ",USER_TEXT)
	print("Wave array",WAVE_ARRAY_1)
	print("Wave array count",WAVE_ARRAY_COUNT)
	print("PNTS_PER_SCREEN",PNTS_PER_SCREEN)
	print("Trig time array",TRIGTIME_ARRAY)
	print("Segment index",SEGMENT_INDEX)
	print("Trigger time,",TRIGGER_TIME)
	print("Acquisition duration",ACQ_DURATION)

	my_file.seek(aFIRST_VALID_PNT)
	FIRST_VALID_PNT = struct.unpack("i",my_file.read(4))

	my_file.seek(aLAST_VALID_PNT)
	LAST_VALID_PNT = struct.unpack("i",my_file.read(4))
	print("First point ",FIRST_VALID_PNT)
	print("LAST point ",LAST_VALID_PNT)
	# b_y_data = my_file.read(WAVE_ARRAY_1[0])
	# exit
	offset = WAVEDESC + wave_descriptor[0] + USER_TEXT[0] #+ TRIGTIME_ARRAY[0]
	my_file.seek(offset)
	print(offset)
	time_event1      = struct.unpack('d',my_file.read(8))
	offset_event1      = struct.unpack('d',my_file.read(8))

	#my_file.seek(offset + 1000+ TRIGTIME_ARRAY[0])
	time_event2      = struct.unpack('d',my_file.read(8))
	offset_event2      = struct.unpack('d',my_file.read(8))

	time_event3      = struct.unpack('d',my_file.read(8))
	offset_event3      = struct.unpack('d',my_file.read(8))

	print("time event 1 ",time_event1)
	print("offset event 1 ",offset_event1)
	print("time event 2 ",time_event2)
	print("offset event 2 ",offset_event2)
	print("time event 3 ",time_event3)
	print("offset event 3 ",offset_event3)


	my_file.seek(offset + TRIGTIME_ARRAY[0])
	b_y_data = my_file.read(1004)
	y_axis = struct.unpack("<"+str(502)+"h", b_y_data)
	data = [1000*vertical_gain*y for y in y_axis]
	#for y in data:
	#	print "%.2f" %y


def get_waveform_block_offset(filepath_in):
	my_file = open(filepath_in, 'rb')

	my_file.seek(aUSER_TEXT)
	USER_TEXT = struct.unpack('i',my_file.read(4))#ReadLong(fid, aUSER_TEXT);
	my_file.seek(aTRIGTIME_ARRAY)
	TRIGTIME_ARRAY = struct.unpack('i',my_file.read(4))
	my_file.seek(aWAVE_DESCRIPTOR)
	WAVE_DESCRIPTOR = struct.unpack('i',my_file.read(4))

	offset = WAVEDESC + WAVE_DESCRIPTOR[0] + USER_TEXT[0] #+ TRIGTIME_ARRAY[0]
	full_offset = WAVEDESC + WAVE_DESCRIPTOR[0] + USER_TEXT[0] + TRIGTIME_ARRAY[0]
	my_file.close()
	return offset,full_offset


def get_configuration(filepath_in):
	my_file = open(filepath_in, 'rb')
	my_file.seek(aVERTICAL_GAIN)
	vertical_gain = struct.unpack('f',my_file.read(4))[0]
	my_file.seek(aVERTICAL_OFFSET)
	vertical_offset = struct.unpack('f',my_file.read(4))[0]
	my_file.seek(aHORIZ_INTERVAL)
	horizontal_interval = struct.unpack('f',my_file.read(4))[0]
	my_file.seek(aSUBARRAY_COUNT)
	nsegments      = struct.unpack('i',my_file.read(4))[0]
	my_file.seek(aWAVE_ARRAY_COUNT)
	WAVE_ARRAY_COUNT    = struct.unpack('i',my_file.read(4))[0]
	points_per_frame = int(WAVE_ARRAY_COUNT / nsegments)
	my_file.close()
	return [nsegments,points_per_frame,horizontal_interval,vertical_gain,vertical_offset]


def get_segment_times(filepath_in,offset,nsegments):
	my_file = open(filepath_in, 'rb')
	trigger_times = []
	horizontal_offsets = []

	my_file.seek(offset)
	for i_event in range(nsegments):
		trigger_times.append(struct.unpack('d',my_file.read(8))[0])
		horizontal_offsets.append(struct.unpack('d',my_file.read(8))[0])
	
	my_file.close()
	return trigger_times,horizontal_offsets


def get_vertical_array(filepath_in,full_offset,points_per_frame,vertical_gain,vertical_offset,event_number):
	my_file = open(filepath_in, 'rb')

	starting_position = full_offset + 2*points_per_frame*event_number
	my_file.seek(starting_position)
	binary_y_data = my_file.read(2*points_per_frame)
	y_axis_raw = struct.unpack("<"+str(points_per_frame)+"h", binary_y_data)
	y_axis = [vertical_gain*y - vertical_offset for y in y_axis_raw]

	my_file.close()
	return y_axis


def calc_horizontal_array(points_per_frame,horizontal_interval,horizontal_offset):
	x_axis = horizontal_offset + horizontal_interval * np.linspace(0, points_per_frame-1, points_per_frame)
	return x_axis






runNumber = int(args.runNumber)
print("\nProcessing run %i." % runNumber)

sourceFiles=[]
inputFiles=[]
start = time.time()
for ic in range(nchan):
	this_file = "%s/C%i--Trace%i.trc" % (RawDataPath, ic+1,runNumber)
	if LocalMode: 
		print("Copying files locally and moving originals to deletion folder.")
		inputFiles.append("%s/C%i--Trace%i.trc" % (RawDataLocalCopyPath, ic+1,runNumber))
		#print 'rsync -z -v %s %s && mv %s %s' % (this_file,RawDataLocalCopyPath,this_file,RawDataPath+"/to_delete/")
		os.system('rsync -z -v %s %s && mv %s %s' % (this_file,RawDataLocalCopyPath,this_file,RawDataPath+"/to_delete/"))

	else: inputFiles.append("C%i--Trace%i.trc" % (ic+1,runNumber)) ### condor copies files to current directory

end = time.time()
print("\nCopying files locally took %i seconds." % (end-start))

outputFile = "%sconverted_run%i.root"%(OutputFilePath, runNumber)
#outputFile = "%srun_scope%i.root"%(OutputFilePath, runNumber)

#inputFile = "%s/C1--Trace%i.trc" %(RawDataPath,runNumber)  ### use ch1 to get information
##### Get necessary information about format

vertical_gains =[]
vertical_offsets =[]
nsegments=0
points_per_frame=0
horizontal_interval=0
for ichan in range(nchan):
	nsegments,points_per_frame,horizontal_interval,vertical_gain,vertical_offset = get_configuration(inputFiles[ichan])
	vertical_gains.append(vertical_gain)
	vertical_offsets.append(vertical_offset)

print("Number of segments: %i" %nsegments)
print("Points per segment %i" % points_per_frame)
print("Horizontal interval %s" % str(horizontal_interval))

for ichan in range(nchan):
	print("Channel %i"%ichan)
	print("\t vertical_gain %0.3f" % vertical_gains[ichan])
	print("\t vertical offset %0.3f" % vertical_offsets[ichan])

### find beginning of trigger time block and y-axis block
offset,full_offset = get_waveform_block_offset(inputFiles[0])
#print "offset is ",offset

## get event times and offsets
trigger_times,horizontal_offsets = get_segment_times(inputFiles[0],offset,nsegments)
trigger_times2,horizontal_offsets2 = get_segment_times(inputFiles[1],offset,nsegments)
trigger_times3,horizontal_offsets3 = get_segment_times(inputFiles[2],offset,nsegments)
trigger_times3,horizontal_offsets4 = get_segment_times(inputFiles[3],offset,nsegments)
trigger_times3,horizontal_offsets5 = get_segment_times(inputFiles[4],offset,nsegments)
trigger_times3,horizontal_offsets6 = get_segment_times(inputFiles[5],offset,nsegments)
trigger_times3,horizontal_offsets7 = get_segment_times(inputFiles[6],offset,nsegments)
trigger_times3,horizontal_offsets8 = get_segment_times(inputFiles[7],offset,nsegments)

# for i in range(20):
# 	print "delta offsets 1st group %i %0.4f" % (i,1e12*(horizontal_offsets[i]-horizontal_offsets2[i]))
# 	print "delta offsets 2 groups %i %0.4f" % (i,1e12*(horizontal_offsets[i]-horizontal_offsets3[i]))
# for i in range(20):
# 	print "Offsets %i %0.1f %0.1f %0.1f %0.1f %0.1f %0.1f %0.1f %0.1f" % (i,1e12*horizontal_offsets[i] +25000,1e12*horizontal_offsets2[i] +25000,1e12*horizontal_offsets3[i] +25000,1e12*horizontal_offsets4[i] +25000,1e12*horizontal_offsets5[i] +25000,1e12*horizontal_offsets6[i] +25000,1e12*horizontal_offsets7[i] +25000,1e12*horizontal_offsets8[i]+25000)
#print "Trigger times: ",trigger_times
#print "Horizontal offsets: ",horizontal_offsets

## prepare the output files
# outputFile = '%srun_scope%s.root' % (output, run)
start = time.time()
outRoot = TFile(outputFile, "RECREATE")
outTree = TTree("pulse","pulse")

i_evt = np.zeros(1,dtype=np.dtype("u4"))
segment_time = np.zeros(1,dtype=np.dtype("f"))
channel = np.zeros([8,points_per_frame],dtype=np.float32)
time_array = np.zeros([1,points_per_frame],dtype=np.float32)
time_offsets = np.zeros(8,dtype=np.dtype("f"))

outTree.Branch('i_evt',i_evt,'i_evt/i')
outTree.Branch('segment_time',segment_time,'segment_time/F')
outTree.Branch('channel', channel, 'channel[%i][%i]/F' %(nchan,points_per_frame) )
outTree.Branch('time', time_array, 'time[1]['+str(points_per_frame)+']/F' )
outTree.Branch('timeoffsets',time_offsets,'timeoffsets[8]/F')

for i in range(nsegments):
    if i%1000==0:
        print("Processing event %i" % i)
    channel[0] = get_vertical_array(inputFiles[0],full_offset,points_per_frame,vertical_gains[0],vertical_offsets[0],i)
    channel[1] = get_vertical_array(inputFiles[1],full_offset,points_per_frame,vertical_gains[1],vertical_offsets[1],i)
    channel[2] = get_vertical_array(inputFiles[2],full_offset,points_per_frame,vertical_gains[2],vertical_offsets[2],i)
    channel[3] = get_vertical_array(inputFiles[3],full_offset,points_per_frame,vertical_gains[3],vertical_offsets[3],i)
    channel[4] = get_vertical_array(inputFiles[4],full_offset,points_per_frame,vertical_gains[4],vertical_offsets[4],i)
    channel[5] = get_vertical_array(inputFiles[5],full_offset,points_per_frame,vertical_gains[5],vertical_offsets[5],i)
    channel[6] = get_vertical_array(inputFiles[6],full_offset,points_per_frame,vertical_gains[6],vertical_offsets[6],i)
    channel[7] = get_vertical_array(inputFiles[7],full_offset,points_per_frame,vertical_gains[7],vertical_offsets[7],i)
    time_array[0]    = calc_horizontal_array(points_per_frame,horizontal_interval,horizontal_offsets[i])
    i_evt[0]   = i
    segment_time[0] = trigger_times[i]
    time_offsets[0] = horizontal_offsets[i] -horizontal_offsets[i]
    time_offsets[1] = horizontal_offsets2[i]-horizontal_offsets[i]
    time_offsets[2] = horizontal_offsets3[i]-horizontal_offsets[i]
    time_offsets[3] = horizontal_offsets4[i]-horizontal_offsets[i]
    time_offsets[4] = horizontal_offsets5[i]-horizontal_offsets[i]
    time_offsets[5] = horizontal_offsets6[i]-horizontal_offsets[i]
    time_offsets[6] = horizontal_offsets7[i]-horizontal_offsets[i]
    time_offsets[7] = horizontal_offsets8[i]-horizontal_offsets[i]

    outTree.Fill()

print("done filling the tree")
outRoot.cd()
outTree.Write()
outRoot.Close()
final = time.time()
print("\nFilling tree took %i seconds." %(final-start))
print("\nFull script duration: %0.f s"%(final-initial))

if CopyToEOS: os.system("xrdcp -fs %s %s" %(outputFile,eosPath))
