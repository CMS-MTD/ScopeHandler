source /cvmfs/cms.cern.ch/cmsset_default.sh
cd /cvmfs/cms.cern.ch/el9_amd64_gcc12/cms/cmssw/CMSSW_13_3_2/src/
eval `scramv1 runtime -sh`
cd -
xrdcp -s root://cmseos.fnal.gov//store/group/cmstestbeam/2024_05_SNSPD_FCFD_ETL/LecroyScope/RawData/C1--Trace$1.trc .
xrdcp -s root://cmseos.fnal.gov//store/group/cmstestbeam/2024_05_SNSPD_FCFD_ETL/LecroyScope/RawData/C2--Trace$1.trc .
xrdcp -s root://cmseos.fnal.gov//store/group/cmstestbeam/2024_05_SNSPD_FCFD_ETL/LecroyScope/RawData/C3--Trace$1.trc .
xrdcp -s root://cmseos.fnal.gov//store/group/cmstestbeam/2024_05_SNSPD_FCFD_ETL/LecroyScope/RawData/C4--Trace$1.trc .
xrdcp -s root://cmseos.fnal.gov//store/group/cmstestbeam/2024_05_SNSPD_FCFD_ETL/LecroyScope/RawData/C5--Trace$1.trc .
xrdcp -s root://cmseos.fnal.gov//store/group/cmstestbeam/2024_05_SNSPD_FCFD_ETL/LecroyScope/RawData/C6--Trace$1.trc .
xrdcp -s root://cmseos.fnal.gov//store/group/cmstestbeam/2024_05_SNSPD_FCFD_ETL/LecroyScope/RawData/C7--Trace$1.trc .
xrdcp -s root://cmseos.fnal.gov//store/group/cmstestbeam/2024_05_SNSPD_FCFD_ETL/LecroyScope/RawData/C8--Trace$1.trc .
ls
python3 conversion.py --runNumber $1 
rm C*--Trace$1.trc
