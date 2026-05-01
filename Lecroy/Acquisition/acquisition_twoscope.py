import numpy as np
import re
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

# Based on your original single-scope script, refactored for:
# - 2 scopes
# - sequential master/slave acquisition
# - independent trigger settings for master and slave
# - optional master AUX TriggerOut
#
# Original structure and commands adapted from your pasted script. :contentReference[oaicite:0]{index=0}

"""################# SEARCH / CONNECT #################"""

initial = time.time()
rm = visa.ResourceManager("@py")

BASE_PATH = "/home/snspd/2026_05_SNSPD/ScopeHandler/"
run_log_path = BASE_PATH + "/Lecroy/Acquisition/RunLog.txt"



def open_scope(ip):
    scope = rm.open_resource(f"TCPIP0::{ip}::INSTR")
    scope.timeout = 3000000
    scope.encoding = "latin_1"
    scope.clear()
    return scope


def GetNextNumber():
    run_num_file = BASE_PATH + "/Lecroy/Acquisition/next_run_number.txt"
    with open(run_num_file, "r") as fh:
        nextNumber = int(fh.read().strip())
    with open(run_num_file, "w") as fh:
        fh.write(str(nextNumber + 1) + "\n")
    return nextNumber


def normalize_trigger_channel(trig_ch):
    trig_ch = str(trig_ch).strip()
    upper = trig_ch.upper()

    if upper in ("EX", "AUX", "LINE"):
        return upper

    # Accept 1..8 as channel numbers
    if trig_ch.isdigit():
        return "C" + trig_ch

    # Also allow already expanded form
    if upper.startswith("C"):
        return trig_ch

    raise ValueError(f"Unsupported trigger channel: {trig_ch}")

def get_counts(scope, channel="C1"):
    def parse(cmd):
        resp = scope.query(cmd)
        m = re.search(r':\s*(\d+)', resp)
        if not m:
            raise ValueError(f"Could not parse integer from: {resp!r}")
        return int(m.group(1))

    nominal = parse(f'{channel}:INSPECT? "NOM_SUBARRAY_COUNT"')
    saved   = parse(f'{channel}:INSPECT? "SUBARRAY_COUNT"')

    return nominal, saved



def write_run_log(status):
    with open(run_log_path, "w") as fh:
        fh.write(status)
        fh.write("\n")

def build_vertical_lists(args):
    # Validate input lengths
    if len(args.vScale) != len(args.vPos):
        raise ValueError(
            f"vScale ({len(args.vScale)}) and vPos ({len(args.vPos)}) must have same length"
        )
    if len(args.vScale) != 16:
        raise ValueError(
            f"vScale ({len(args.vScale)}) needs to have 16 values"
        )


    # Convert to mV for VOLT_DIV
    vScales_in_mV = [int(1000 * scale) for scale in args.vScale]

    # Offset should be in VOLTS (not mV)
    vOffsets_in_mV = [1000 * scale * pos for scale, pos in zip(args.vScale, args.vPos)]

    return vScales_in_mV, vOffsets_in_mV

#def build_vertical_lists(args):
#    vScales_in_mV = [
#        int(1000 * args.vScale1),
#        int(1000 * args.vScale2),
#        int(1000 * args.vScale3),
#        int(1000 * args.vScale4),
#        int(1000 * args.vScale5),
#        int(1000 * args.vScale6),
#        int(1000 * args.vScale7),
#        int(1000 * args.vScale8),
#    ]
#
#    vOffsets_in_mV = [
#        int(1000 * args.vScale1 * args.vPos1),
#        int(1000 * args.vScale2 * args.vPos2),
#        int(1000 * args.vScale3 * args.vPos3),
#        int(1000 * args.vScale4 * args.vPos4),
#        int(1000 * args.vScale5 * args.vPos5),
#        int(1000 * args.vScale6 * args.vPos6),
#        int(1000 * args.vScale7 * args.vPos7),
#        int(1000 * args.vScale8 * args.vPos8),
#    ]
#
#    return vScales_in_mV, vOffsets_in_mV
#

def common_setup(scope, args, label):
    print(f"\nPreparing {label} scope.\n")

    scope.write("STOP")
    scope.write("*CLS")
    scope.write("COMM_HEADER OFF")

    if args.display == 0:
        scope.write("DISPLAY OFF")
    else:
        scope.write("DISPLAY ON")

    ####### Vertical setup ######
    vScales_in_mV, vOffsets_in_mV = build_vertical_lists(args)
    if label == "MASTER": start_ch, end_ch = 1, 8
    else: start_ch, end_ch = 9, 16
    print(label, f"channels: {start_ch} -- {end_ch}")
    for global_ch in range(start_ch, end_ch + 1):
        local_ch = global_ch if global_ch <= 8 else global_ch - 8
        idx = global_ch - 1

        print(
            "\t%s Channel %i (scope C%i): %i mV/div, %.2f mV offset."
            % (label, global_ch, local_ch, vScales_in_mV[idx], vOffsets_in_mV[idx])
        )

        scope.write("C%i:TRA ON" % local_ch)
        scope.write("C%i:COUPLING D50" % local_ch)
        scope.write("C%i:VOLT_DIV %iMV" % (local_ch, vScales_in_mV[idx]))
        scope.write("C%i:OFFSET %iMV" % (local_ch, vOffsets_in_mV[idx]))




    ### Disable bandwidth limit
    scope.write("BANDWIDTH_LIMIT OFF")

    ####### Horizontal setup ######
    time_div_in_ns = int(args.horizontalWindow) / 10.0
    print("\n%s timebase: %s ns/div." % (label, str(time_div_in_ns)))

    if time_div_in_ns not in (2, 5, 500000, 1000000):
        print("Warning: time base must fit predefined set of possible values.")

    sample_rate_in_GS = args.sampleRate
    _ = sample_rate_in_GS  # kept for compatibility with original script

    # Use integer formatting when possible to match original command style
    if float(time_div_in_ns).is_integer():
        scope.write("TIME_DIV %iNS" % int(time_div_in_ns))
    else:
        scope.write("TIME_DIV %fNS" % time_div_in_ns)

    print("\tMake sure sampling rate is set to 10 GS/s manually.")

    print("Setting horizontal offset %f ns" % args.timeoffset)
    scope.write("TRIG_DELAY %f ns" % args.timeoffset)

    ####### Save setup ######
    scope.write("STORE_SETUP ALL_DISPLAYED,HDD,AUTO,OFF,FORMAT,BINARY")

    ####### Sequence configuration ######
    nevents = int(args.numEvents)
    print("\n%s taking %i events in sequence mode." % (label, nevents))
    scope.write("SEQ ON,%i" % nevents)


def setup_trigger(scope, trig_ch, trig_level, trig_slope, holdoff, label):
    trig_src = normalize_trigger_channel(trig_ch)
    print(scope, trig_src, label)
    if holdoff > 0:
        scope.write("TRIG_SELECT Edge,SR,%s,HT,TI,HV,%0.3f NS" % (trig_src, holdoff))
    else:
        scope.write("TRIG_SELECT Edge,SR,%s, HT, OFF" % trig_src)

    print("%s trigger holdoff time is %0.3f ns" % (label, holdoff))

    if trig_src != "LINE":
        scope.write("%s:TRLV %0.3fV" % (trig_src, trig_level))
        scope.write("TRIG_SLOPE %s" % trig_slope)

    print(
        "%s triggering on %s with %0.3fV threshold, %s polarity."
        % (label, trig_src, trig_level, trig_slope)
    )



def setup_master(scope, args):
    common_setup(scope, args, "MASTER")
    setup_trigger(
        scope,
        args.master_trigCh,
        args.master_trig,
        args.master_trigSlope,
        args.master_holdoff,
        "MASTER",
    )

    if args.master_aux_mode.lower() == "triggerout":
        scope.write(r"""vbs 'app.Acquisition.AuxOutput.AuxMode = "TriggerOut"' """)
        if args.master_aux_out_pulse_width > 0:
            scope.write(
                r"""vbs 'app.Acquisition.AuxOutput.TrigOutPulseWidth = "%d ns"' """
                % int(args.master_aux_out_pulse_width)
            )
            print(
                "MASTER Aux Output = TriggerOut, pulse width %d ns"
                % int(args.master_aux_out_pulse_width)
            )
        else:
            print("MASTER Aux Output = TriggerOut, default pulse width")
    else:
        scope.write(r"""vbs 'app.Acquisition.AuxOutput.AuxMode = "Off"' """)
        print("MASTER Aux Output disabled.")


def setup_slave(scope, args):
    common_setup(scope, args, "SLAVE")
    setup_trigger(
        scope,
        args.slave_trigCh,
        args.slave_trig,
        args.slave_trigSlope,
        args.slave_holdoff,
        "SLAVE",
    )

    if args.slave_aux_mode.lower() == "triggerout":
        scope.write(r"""vbs 'app.Acquisition.AuxOutput.AuxMode = "TriggerOut"' """)
        if args.slave_aux_out_pulse_width > 0:
            scope.write(
                r"""vbs 'app.Acquisition.AuxOutput.TrigOutPulseWidth = "%d ns"' """
                % int(args.slave_aux_out_pulse_width)
            )
            print(
                "SLAVE Aux Output = TriggerOut, pulse width %d ns"
                % int(args.slave_aux_out_pulse_width)
            )
        else:
            print("SLAVE Aux Output = TriggerOut, default pulse width")
    else:
        scope.write(r"""vbs 'app.Acquisition.AuxOutput.AuxMode = "Off"' """)
        print("SLAVE Aux Output disabled.")


def save_scope(scope, runNumber, suffix):
    start = time.time()
    print("Saving waveforms for %s..." % suffix)
    scope.write(
        r"""vbs 'app.SaveRecall.Waveform.TraceTitle="Trace%i" ' """
        % (runNumber)
    )
    scope.write(r"""vbs 'app.SaveRecall.Waveform.SaveFile' """)
    scope.query("ALST?")
    end = time.time()
    print("Waveform storage complete for %s." % suffix)
    print("\tStoring waveforms took %0.4f s" % (end - start))


parser = argparse.ArgumentParser(description="Run info.")

parser.add_argument(
    "--master-scope-ip",
    metavar="IP",
    type=str,
    required=True,
    help="IP address of the master oscilloscope",
)
parser.add_argument(
    "--slave-scope-ip",
    metavar="IP",
    type=str,
    required=True,
    help="IP address of the slave oscilloscope",
)

parser.add_argument(
    "--numEvents",
    metavar="Events",
    type=str,
    default=500,
    help="numEvents (default 500)",
    required=False,
)
parser.add_argument(
    "--runNumber",
    metavar="runNumber",
    type=str,
    default=-1,
    help="runNumber (default -1)",
    required=False,
)
parser.add_argument(
    "--sampleRate",
    metavar="sampleRate",
    type=str,
    default=10,
    help="Sampling rate (default 10)",
    required=False,
)
parser.add_argument(
    "--horizontalWindow",
    metavar="horizontalWindow",
    type=str,
    default=50,
    help="horizontal Window (default 50)",
    required=False,
)

# Independent trigger settings
parser.add_argument(
    "--master-trigCh",
    metavar="trigCh",
    type=str,
    default="EX",
    help="master trigger channel (EX, AUX, LINE, 1..8)",
    required=False,
)
parser.add_argument(
    "--master-trig",
    metavar="trig",
    type=float,
    default=0.150,
    help="master trigger value in V",
    required=False,
)
parser.add_argument(
    "--master-trigSlope",
    metavar="trigSlope",
    type=str,
    default="NEGative",
    help="master trigger slope",
    required=False,
)
parser.add_argument(
    "--master-holdoff",
    metavar="holdoff",
    type=float,
    default=0,
    help="master trigger holdoff in ns",
    required=False,
)

parser.add_argument(
    "--slave-trigCh",
    metavar="trigCh",
    type=str,
    default="EX",
    help="slave trigger channel (EX, AUX, LINE, 1..8)",
    required=False,
)
parser.add_argument(
    "--slave-trig",
    metavar="trig",
    type=float,
    default=0.150,
    help="slave trigger value in V",
    required=False,
)
parser.add_argument(
    "--slave-trigSlope",
    metavar="trigSlope",
    type=str,
    default="NEGative",
    help="slave trigger slope",
    required=False,
)
parser.add_argument(
    "--slave-holdoff",
    metavar="holdoff",
    type=float,
    default=0,
    help="slave trigger holdoff in ns",
    required=False,
)

# AUX mode controls
parser.add_argument(
    "--master-aux-mode",
    metavar="mode",
    type=str,
    default="off",
    choices=["off", "triggerout", "Off", "TriggerOut", "TRIGGEROUT", "OFF"],
    help='master AUX output mode: "off" or "triggerout"',
    required=False,
)
parser.add_argument(
    "--master-aux-out-pulse-width",
    metavar="ns",
    type=float,
    default=0,
    help="master AUX TriggerOut pulse width in ns",
    required=False,
)

parser.add_argument(
    "--slave-aux-mode",
    metavar="mode",
    type=str,
    default="off",
    choices=["off", "triggerout", "Off", "TriggerOut", "TRIGGEROUT", "OFF"],
    help='slave AUX output mode: "off" or "triggerout"',
    required=False,
)
parser.add_argument(
    "--slave-aux-out-pulse-width",
    metavar="ns",
    type=float,
    default=0,
    help="slave AUX TriggerOut pulse width in ns",
    required=False,
)

## Vertical settings
#parser.add_argument("--vScale1", metavar="vScale1", type=float, default=0.05, help="Vertical scale, volts/div", required=False)
#parser.add_argument("--vScale2", metavar="vScale2", type=float, default=0.05, help="Vertical scale, volts/div", required=False)
#parser.add_argument("--vScale3", metavar="vScale3", type=float, default=0.05, help="Vertical scale, volts/div", required=False)
#parser.add_argument("--vScale4", metavar="vScale4", type=float, default=0.05, help="Vertical scale, volts/div", required=False)
#parser.add_argument("--vScale5", metavar="vScale5", type=float, default=0.05, help="Vertical scale, volts/div", required=False)
#parser.add_argument("--vScale6", metavar="vScale6", type=float, default=0.05, help="Vertical scale, volts/div", required=False)
#parser.add_argument("--vScale7", metavar="vScale7", type=float, default=0.05, help="Vertical scale, volts/div", required=False)
#parser.add_argument("--vScale8", metavar="vScale8", type=float, default=0.05, help="Vertical scale, volts/div", required=False)
#
#parser.add_argument("--vPos1", metavar="vPos1", type=float, default=0, help="Vertical Pos, div", required=False)
#parser.add_argument("--vPos2", metavar="vPos2", type=float, default=0, help="Vertical Pos, div", required=False)
#parser.add_argument("--vPos3", metavar="vPos3", type=float, default=0, help="Vertical Pos, div", required=False)
#parser.add_argument("--vPos4", metavar="vPos4", type=float, default=0, help="Vertical Pos, div", required=False)
#parser.add_argument("--vPos5", metavar="vPos5", type=float, default=0, help="Vertical Pos, div", required=False)
#parser.add_argument("--vPos6", metavar="vPos6", type=float, default=0, help="Vertical Pos, div", required=False)
#parser.add_argument("--vPos7", metavar="vPos7", type=float, default=0, help="Vertical Pos, div", required=False)
#parser.add_argument("--vPos8", metavar="vPos8", type=float, default=0, help="Vertical Pos, div", required=False)
#

parser.add_argument(
    "--vScale",
    metavar="V",
    nargs="+",
    type=float,
    default=[0.05]*8,
    help="Vertical scales in V/div (one per channel)",
    required=False,
)

parser.add_argument(
    "--vPos",
    metavar="DIV",
    nargs="+",
    type=float,
    default=[0]*8,
    help="Vertical positions in divisions (one per channel)",
    required=False,
)



parser.add_argument(
    "--display",
    metavar="display",
    type=int,
    default=0,
    help="enable display",
    required=False,
)

parser.add_argument(
    "--timeoffset",
    metavar="timeoffset",
    type=float,
    default=0,
    help="Offset to compensate for trigger delay in ns",
    required=False,
)

# Sequential startup behavior
parser.add_argument(
    "--slave-arm-delay",
    metavar="seconds",
    type=float,
    default=0.2,
    help="delay after arming slave before starting master (seconds)",
    required=False,
)

args = parser.parse_args()

runNumber = int(args.runNumber)
if runNumber == -1:
    runNumber = GetNextNumber()

print("Next run number: %i" % runNumber)

master = open_scope(args.master_scope_ip)
slave = open_scope(args.slave_scope_ip)

try:
    setup_master(master, args)
    setup_slave(slave, args)
    write_run_log("busy")

    start = time.time()
    now = datetime.datetime.now()
    current_time = now.strftime("%H:%M:%S")

    print(
        "\n\n\n------------- Starting acquisition for run %i at %s. -------------"
        % (runNumber, current_time)
    )

    # Sequential acquisition:
    # 1. Arm slave first
    # 2. Delay briefly
    # 3. Start master
    # 4. Wait for both
    print("Arming SLAVE first...")
    slave.write("*CLS")      # clear status first
    slave.write("ARM")
    time.sleep(2)
    if args.slave_arm_delay > 0:
        time.sleep(args.slave_arm_delay)


    timeout_s = 5
    t0 = time.time()
    
    while True:
        trig_mode = slave.query("TRIG_MODE?").strip()
    
        if "SINGLE" in trig_mode:
            print("Scope is armed/running in single mode")
            break
        if time.time() - t0 > timeout_s:
            print("Timed out waiting for scope to arm")
            sys.exit(1)
        time.sleep(0.05)

    print("Starting MASTER...")
    master.write("*TRG")

    print("Waiting for MASTER to finish...")
    master.write("WAIT")
    master.query("ALST?")

    print("Waiting for SLAVE to finish...")
    slave.write("WAIT")
    slave.query("ALST?")

    end = time.time()
    duration = end - start
    nevents = int(args.numEvents)

    print("\n\n\n------------- Acquisition complete. ------------------------")
    print("\tAcquisition duration: %0.4f s" % duration)
    if duration > 0:
        print("\tTrigger rate: %0.1f Hz" % (nevents / duration))


    slave_nom, slave_saved = get_counts(slave)
    master_nom, master_saved = get_counts(master)
    print("---------------Number of events acquired:------------------- \n")
    print(f"\t Slave:  requested={slave_nom}, actual={slave_saved}")
    print(f"\t Master: requested={master_nom}, actual={master_saved}")
    if not (slave_nom == master_nom == slave_saved == master_saved == nevents):
        print("SOMETHING IS WRONG!!!!!!!!!")
        print("NUMBER OF EVENTS ACQUIRED NOT CORRECT!!!!!")


    print("\n\n------------- Beginning save waveforms. ----------------------")
    write_run_log("writing")

    save_scope(master, runNumber, "master")
    save_scope(slave, runNumber, "slave")

finally:
    try:
        master.close()
    except Exception:
        pass

    try:
        slave.close()
    except Exception:
        pass

    try:
        rm.close()
    except Exception:
        pass

final = time.time()
print("\nFinished run %i." % runNumber)
print("Full script duration: %0.f s" % (final - initial))
write_run_log("ready")
