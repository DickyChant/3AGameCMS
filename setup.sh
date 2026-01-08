#!/bin/bash
# ============================================
# Triphoton Analysis Setup Script
# ============================================
# Sets up environment for CVMFS-based analysis
# No file copying needed - everything on CVMFS!
# ============================================

# Don't exit on error - continue and report warnings instead
set +e

echo "========================================"
echo "Triphoton Analysis Setup (CVMFS-based)"
echo "========================================"
echo ""

cmsenv

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
        echo "  ✗ WARNING: Compilation had issues"
        echo "    You may need to compile manually: scram b"
    fi
else
    echo "  ✓ Already compiled"
fi

echo ""

# ============================================
# Step 5: Setup Python Virtual Environment and Install cmsstyle
# ============================================
echo "Setting up Python virtual environment for plotting tools..."
cd "$CMSSW_BASE"

# Check if scram-venv is available
if command -v scram-venv &> /dev/null; then
    echo "  Setting up scram-venv..."
    
    # Check if venv already exists (either .venv or venv directory)
    VENV_EXISTS=0
    if [ -d "$CMSSW_BASE/.venv" ] || [ -d "$CMSSW_BASE/venv" ]; then
        VENV_EXISTS=1
        echo "  ✓ Virtual environment already exists"
    fi
    
    # Initialize scram-venv if not already done
    if [ $VENV_EXISTS -eq 0 ]; then
        echo "  Creating virtual environment..."
        scram-venv 2>&1 | grep -v "failed to create symbolic link" || true
        if [ -d "$CMSSW_BASE/.venv" ] || [ -d "$CMSSW_BASE/venv" ]; then
            echo "  ✓ Virtual environment created"
        else
            echo "  ⚠ WARNING: Virtual environment creation had issues, but continuing..."
        fi
    fi
    
    # Re-initialize CMSSW environment to activate venv (ignore errors)
    eval `scram runtime -sh` 2>/dev/null || true
    
    # Check if cmsstyle is installed
    if python3 -c "import cmsstyle" 2>/dev/null; then
        echo "  ✓ cmsstyle already installed"
    else
        echo "  Installing cmsstyle..."
        pip install --quiet cmsstyle 2>&1 | grep -v "WARNING" || true
        if python3 -c "import cmsstyle" 2>/dev/null; then
            echo "  ✓ cmsstyle installed successfully"
        else
            echo "  ⚠ WARNING: Failed to install cmsstyle"
            echo "    You can install it manually with: pip install cmsstyle"
        fi
    fi
else
    echo "  ⚠ WARNING: scram-venv not available"
    echo "    Install cmsstyle manually: pip install --user cmsstyle"
fi

echo ""

# ============================================
# Step 6: Summary
# ============================================
echo "========================================"
echo "✓ Setup Complete!"
echo "========================================"
echo ""
echo "What's configured:"
echo "  • CVMFS corrections (Photon ID, PU weights, JME)"
echo "  • Analysis modules (PUWeightRun2/3, PhoIDSF, TriPhoton)"
echo "  • CRAB submission tools"
echo "  • Python virtual environment with cmsstyle"
echo ""
echo "Quick start:"
echo "  • Test locally:     cd test && python localrun.py"
echo "  • Submit to CRAB:   ./crab/submit_crab.sh 2017 submit"
echo "  • Check status:     ./crab/submit_crab.sh 2017 status"
echo "  • Create plots:      python scripts/plot_triphoton.py input.root"
echo ""
echo "All corrections loaded from CVMFS - no local files needed!"
echo "========================================"
