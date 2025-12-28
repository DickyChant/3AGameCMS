#!/bin/bash
# ============================================
# Triphoton Analysis Setup Script
# ============================================
# Sets up environment for CVMFS-based analysis
# No file copying needed - everything on CVMFS!
# ============================================

set -e  # Exit on error

echo "========================================"
echo "Triphoton Analysis Setup (CVMFS-based)"
echo "========================================"
echo ""

# ============================================
# Step 1: Check CMSSW Environment
# ============================================
if [ -z "$CMSSW_BASE" ]; then
    echo "ERROR: CMSSW environment not set!"
    echo "Please run: cmsenv"
    echo ""
    echo "Example:"
    echo "  cd \$CMSSW_BASE/src"
    echo "  cmsenv"
    exit 1
fi

echo "✓ CMSSW environment: $CMSSW_BASE"
echo ""

# ============================================
# Step 2: Verify CVMFS Access
# ============================================
echo "Checking CVMFS access..."

# Check EGM (Photon ID SF)
if [ -d "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM" ]; then
    echo "  ✓ EGM metadata (Photon ID SF) accessible"
else
    echo "  ✗ WARNING: EGM metadata not accessible"
    echo "    Path: /cvmfs/cms-griddata.cern.ch/cat/metadata/EGM"
fi

# Check LUM (PU weights)
if [ -d "/cvmfs/cms-griddata.cern.ch/cat/metadata/LUM" ]; then
    echo "  ✓ LUM metadata (PU weights) accessible"
else
    echo "  ✗ WARNING: LUM metadata not accessible"
    echo "    Path: /cvmfs/cms-griddata.cern.ch/cat/metadata/LUM"
fi

# Check JME (Jet corrections)
if [ -d "/cvmfs/cms-griddata.cern.ch/cat/metadata/JME" ]; then
    echo "  ✓ JME metadata (Jet/MET corrections) accessible"
else
    echo "  ✗ WARNING: JME metadata not accessible"
    echo "    Path: /cvmfs/cms-griddata.cern.ch/cat/metadata/JME"
fi

echo ""

# ============================================
# Step 3: Set Analysis Paths
# ============================================
export ANALYSIS_BASE="$CMSSW_BASE/src/PhysicsTools/NanoAODTools/python/postprocessing/analysis"
export PYTHONPATH="$ANALYSIS_BASE:$PYTHONPATH"

echo "Analysis paths set:"
echo "  ANALYSIS_BASE: $ANALYSIS_BASE"
echo ""

# ============================================
# Step 4: Compile (if needed)
# ============================================
echo "Checking compilation..."
cd "$CMSSW_BASE/src"

# Check if WeightCalculatorFromHistogram is compiled
if [ ! -f "$CMSSW_BASE/lib/$SCRAM_ARCH/libPhysicsToolsNanoAODTools.so" ]; then
    echo "  Compiling NanoAODTools..."
    scram b -j 4
    if [ $? -eq 0 ]; then
        echo "  ✓ Compilation successful"
    else
        echo "  ✗ Compilation failed!"
        exit 1
    fi
else
    echo "  ✓ Already compiled"
fi

echo ""

# ============================================
# Step 5: Summary
# ============================================
echo "========================================"
echo "✓ Setup Complete!"
echo "========================================"
echo ""
echo "What's configured:"
echo "  • CVMFS corrections (Photon ID, PU weights, JME)"
echo "  • Analysis modules (PUWeightRun2/3, PhoIDSF, TriPhoton)"
echo "  • CRAB submission tools"
echo ""
echo "Quick start:"
echo "  • Test locally:     cd test && python localrun.py"
echo "  • Submit to CRAB:   ./crab/submit_crab.sh 2017 submit"
echo "  • Check status:     ./crab/submit_crab.sh 2017 status"
echo ""
echo "All corrections loaded from CVMFS - no local files needed!"
echo "========================================"
