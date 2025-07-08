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
lecroy = rm.open_resource('TCPIP0::192.168.0.12::INSTR')
lecroy.timeout = 3000000
lecroy.encoding = 'latin_1'
lecroy.clear()


print "\n \nPreparing 8-channel scope. \n"
lecroy.write('STOP')
lecroy.write("*CLS")
lecroy.write("COMM_HEADER OFF")
lecroy.write("DISPLAY ON")

lecroy.close()
rm.close()
