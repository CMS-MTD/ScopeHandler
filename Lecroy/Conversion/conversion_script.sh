source /cvmfs/cms.cern.ch/cmsset_default.sh
cd /cvmfs/cms.cern.ch/el9_amd64_gcc12/cms/cmssw/CMSSW_13_3_2/src/
eval `scramv1 runtime -sh`
cd -
BASE=2025_07_FCFD
xrdcp -s root://cmseos.fnal.gov//store/group/cmstestbeam/${BASE}/LecroyScope/RawData/C1--Trace$1.trc .
xrdcp -s root://cmseos.fnal.gov//store/group/cmstestbeam/${BASE}/LecroyScope/RawData/C2--Trace$1.trc .
xrdcp -s root://cmseos.fnal.gov//store/group/cmstestbeam/${BASE}/LecroyScope/RawData/C3--Trace$1.trc .
xrdcp -s root://cmseos.fnal.gov//store/group/cmstestbeam/${BASE}/LecroyScope/RawData/C4--Trace$1.trc .
xrdcp -s root://cmseos.fnal.gov//store/group/cmstestbeam/${BASE}/LecroyScope/RawData/C5--Trace$1.trc .
xrdcp -s root://cmseos.fnal.gov//store/group/cmstestbeam/${BASE}/LecroyScope/RawData/C6--Trace$1.trc .
xrdcp -s root://cmseos.fnal.gov//store/group/cmstestbeam/${BASE}/LecroyScope/RawData/C7--Trace$1.trc .
xrdcp -s root://cmseos.fnal.gov//store/group/cmstestbeam/${BASE}/LecroyScope/RawData/C8--Trace$1.trc .
ls
cp /uscms_data/d3/christiw/testbeam/${BASE}/ScopeHandler/Lecroy/Conversion/conversion.py .
python3 conversion.py --runNumber $1 
rm C*--Trace$1.trc
