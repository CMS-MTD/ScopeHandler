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

"""#################SEARCH/CONNECT#################"""
# establish communication with scope
initial = time.time()
rm = visa.ResourceManager("@py")
lecroy = rm.open_resource('TCPIP0::192.168.133.169::INSTR')
lecroy.timeout = 3000000
lecroy.encoding = 'latin_1'
lecroy.clear()


print "\n \nPreparing 8-channel scope. \n"
lecroy.write('STOP')
lecroy.write("*CLS")
lecroy.write("COMM_HEADER OFF")
lecroy.write("DISPLAY ON")

####### Vertical setup ######

vScales_in_mV = []
vScales_in_mV.append(int(1000* 0.01))
vScales_in_mV.append(int(1000* 0.01))
vScales_in_mV.append(int(1000* 0.01))
vScales_in_mV.append(int(1000* 0.01))
vScales_in_mV.append(int(1000* 0.01))
vScales_in_mV.append(int(1000* 0.01))
vScales_in_mV.append(int(1000* 0.01))
vScales_in_mV.append(int(1000* 0.01))

vOffsets_in_mV = []
vOffsets_in_mV.append(int(1000* 0.01 * 3.25))
vOffsets_in_mV.append(int(1000* 0.01 * 2.5))
vOffsets_in_mV.append(int(1000* 0.01 * 1.75 ))
vOffsets_in_mV.append(int(1000* 0.01 * 1.))
vOffsets_in_mV.append(int(1000* 0.01 * 0. ))
vOffsets_in_mV.append(int(1000* 0.01 * -1))
vOffsets_in_mV.append(int(1000* 0.01 * -2))
vOffsets_in_mV.append(int(1000* 0.01 * -3 ))
print "Vertical setup."
for chan in range(1,8+1):
	print "\tChannel %i: %i mV/div, %i mV offset. "% (chan, vScales_in_mV[chan-1],vOffsets_in_mV[chan-1])
	lecroy.write("C%i:COUPLING D50"%(chan))
	lecroy.write("C%i:VOLT_DIV %iMV"%(chan, vScales_in_mV[chan-1]))
	lecroy.write("C%i:OFFSET %iMV"%(chan, vOffsets_in_mV[chan-1]))

lecroy.write("TRIG_SELECT Edge,SR,%s"%"C!")
lecroy.write("%s:TRLV %0.3fV"%("C1",0.001))

lecroy.write("SEQ OFF")
lecroy.write("*TRG")






lecroy.close()
rm.close()
