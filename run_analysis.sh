#!/bin/bash
# Wrapper script to run analysis with proper CMSSW environment

set -e

# Setup CMSSW
cd /home/sqian/Codes/3a_analysis/CMSSW_14_0_7/src
source /cvmfs/cms.cern.ch/cmsset_default.sh
eval `scramv1 runtime -sh`
cd PhysicsTools/NanoAODTools/python/postprocessing/analysis

# Run the analysis
python3 test/localrun.py "$@"
