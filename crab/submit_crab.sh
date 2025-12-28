#!/bin/bash
# ============================================
# Unified CRAB Submission Script
# ============================================
# Usage:
#   ./submit_crab.sh 2017           # Generate configs only
#   ./submit_crab.sh 2017 submit    # Generate and submit all jobs
#   ./submit_crab.sh 2017 status    # Check status of all jobs
# ============================================

set -e  # Exit on error

YEAR=$1
ACTION=${2:-"config"}  # Default: only create configs

if [ -z "$YEAR" ]; then
    echo "Usage: $0 <year> [action]"
    echo ""
    echo "Arguments:"
    echo "  year     : 2016apv, 2016, 2017, 2018, 2022, 2022EE"
    echo "  action   : config (default), submit, status, resubmit"
    echo ""
    echo "Examples:"
    echo "  $0 2017                  # Create configs only"
    echo "  $0 2017 submit           # Create configs and submit all"
    echo "  $0 2017 status           # Check status of all jobs"
    echo "  $0 2017 resubmit         # Resubmit failed jobs"
    exit 1
fi

# Validate year
case $YEAR in
    2016apv|2016|2017|2018|2022|2022EE)
        echo "✓ Processing year: $YEAR"
        ;;
    *)
        echo "ERROR: Invalid year '$YEAR'"
        echo "Valid options: 2016apv, 2016, 2017, 2018, 2022, 2022EE"
        exit 1
        ;;
esac

# Navigate to crab directory (works from anywhere)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
echo "Working directory: $PWD"

# ============================================
# Step 1: Create CRAB Configurations
# ============================================
if [ "$ACTION" = "config" ] || [ "$ACTION" = "submit" ]; then
    echo ""
    echo "=========================================="
    echo "Creating CRAB configs for $YEAR..."
    echo "=========================================="
    python create_crab.py $YEAR

    CONFIG_DIR="config_crab_${YEAR}"
    NUM_CONFIGS=$(ls -1 ${CONFIG_DIR}/*_cfg.py 2>/dev/null | wc -l)
    echo "✓ Created $NUM_CONFIGS CRAB config files in ${CONFIG_DIR}/"
    ls ${CONFIG_DIR}/*_cfg.py | head -5
    if [ $NUM_CONFIGS -gt 5 ]; then
        echo "  ... ($(($NUM_CONFIGS - 5)) more)"
    fi
fi

# ============================================
# Step 2: Submit CRAB Jobs (if requested)
# ============================================
if [ "$ACTION" = "submit" ]; then
    echo ""
    echo "=========================================="
    echo "Submitting CRAB jobs for $YEAR..."
    echo "=========================================="

    CONFIG_DIR="config_crab_${YEAR}"
    if [ ! -d "$CONFIG_DIR" ]; then
        echo "ERROR: Config directory $CONFIG_DIR not found!"
        exit 1
    fi

    # Submit each config
    for cfg in ${CONFIG_DIR}/*_cfg.py; do
        echo ""
        echo "Submitting: $cfg"
        crab submit -c $cfg || echo "WARNING: Failed to submit $cfg"

        # Clean up tarball after submission
        SAMPLE=$(basename $cfg _cfg.py)
        if [ -d "crab_${SAMPLE}/inputs/" ]; then
            rm -f crab_${SAMPLE}/inputs/*.tgz
            echo "  ✓ Cleaned tarball for crab_${SAMPLE}"
        fi
    done

    echo ""
    echo "=========================================="
    echo "✓ Submission complete!"
    echo "=========================================="
fi

# ============================================
# Step 3: Check Status (if requested)
# ============================================
if [ "$ACTION" = "status" ]; then
    echo ""
    echo "=========================================="
    echo "Checking status of $YEAR jobs..."
    echo "=========================================="

    # Find all crab directories
    for crabdir in crab_*/; do
        if [ -d "$crabdir" ]; then
            echo ""
            echo "Status of $crabdir:"
            crab status -d $crabdir || echo "  WARNING: Could not get status"
        fi
    done
fi

# ============================================
# Step 4: Resubmit Failed (if requested)
# ============================================
if [ "$ACTION" = "resubmit" ]; then
    echo ""
    echo "=========================================="
    echo "Resubmitting failed jobs for $YEAR..."
    echo "=========================================="

    for crabdir in crab_*/; do
        if [ -d "$crabdir" ]; then
            echo ""
            echo "Resubmitting: $crabdir"
            crab resubmit -d $crabdir || echo "  WARNING: Could not resubmit"
        fi
    done
fi

echo ""
echo "=========================================="
echo "Done!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  - Check status:  $0 $YEAR status"
echo "  - Resubmit:      $0 $YEAR resubmit"
echo "  - Get reports:   crab report -d crab_<sample>/"
