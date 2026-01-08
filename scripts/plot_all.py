#!/usr/bin/env python3
"""
All-in-one plotting script for triphoton analysis
Combines functionality from:
- plot_triphoton.py: Main distributions with trigger overlays
- plot_triphoton_3gamma.py: Triphoton-specific kinematics
- plot_triphoton_rdf.py: Advanced RDataFrame-based plots

Usage:
    python plot_all.py input_files --year 2017 --lumi 27.1 [options]
"""
import ROOT
import os
import sys
import glob
import argparse
import subprocess
from datetime import datetime

# Prevent ROOT from stealing command-line arguments
ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch(True)

# Try to import and use cmsstyle for CMS-compliant plots
USE_CMSSTYLE = False
cmsstyle_module = None

try:
    import cmsstyle
    cmsstyle_module = cmsstyle
    try:
        if hasattr(cmsstyle, 'setCMSStyle'):
            cmsstyle.setCMSStyle()
        elif hasattr(cmsstyle, 'cms') and hasattr(cmsstyle.cms, 'setCMSStyle'):
            cmsstyle.cms.setCMSStyle()
        elif hasattr(cmsstyle, 'cms') and hasattr(cmsstyle.cms, 'init'):
            cmsstyle.cms.init()
        
        if hasattr(cmsstyle, 'cms'):
            if hasattr(cmsstyle.cms, 'setLumi'):
                cmsstyle.cms.setLumi(0)
            if hasattr(cmsstyle.cms, 'setEnergy'):
                cmsstyle.cms.setEnergy("13.6")
            if hasattr(cmsstyle.cms, 'setExtraText'):
                cmsstyle.cms.setExtraText("Preliminary")
        
        ROOT.gStyle.SetOptStat(0)
        if hasattr(ROOT.gStyle, 'SetPalette'):
            ROOT.gStyle.SetPalette(ROOT.kViridis)
        print("✓ Using cmsstyle for CMS-compliant plots")
        USE_CMSSTYLE = True
    except Exception as e:
        print(f"⚠ WARNING: cmsstyle initialization failed: {e}")
        ROOT.gStyle.SetOptStat(0)
        ROOT.gStyle.SetPalette(ROOT.kViridis)
        USE_CMSSTYLE = False
except ImportError:
    print("⚠ WARNING: cmsstyle not available. Using basic ROOT styling.")
    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetPalette(ROOT.kViridis)
    USE_CMSSTYLE = False

def run_plotting_script(script_name, args_list):
    """Run a plotting script as a subprocess"""
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    if not os.path.exists(script_path):
        print(f"⚠ Warning: Script {script_name} not found, skipping...")
        return False
    
    cmd = [sys.executable, script_path] + args_list
    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}:")
        print(e.stdout)
        print(e.stderr)
        return False
    except Exception as e:
        print(f"❌ Failed to run {script_name}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="All-in-one plotting script for triphoton analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all plots for 2017 MC
  python plot_all.py test_2017_mc/*.root --year 2017 --lumi 27.1 \\
      --triple-trigger1 HLT_TriplePhoton_30_30_10_CaloIdLV2_v \\
      --triple-trigger2 HLT_TriplePhoton_35_35_5_CaloIdLV2_R9IdVL_v

  # Run only main distributions
  python plot_all.py test_2017_mc/*.root --year 2017 --lumi 27.1 \\
      --plots main

  # Run only triphoton-specific plots
  python plot_all.py test_2017_mc/*.root --year 2017 --lumi 27.1 \\
      --plots triphoton
        """
    )
    
    # Input/output arguments
    parser.add_argument("input", help="Input file pattern (e.g., 'test_2017_mc/*.root' or single file)")
    parser.add_argument("-o", "--output", default=None, 
                       help="Output directory for plots (default: /eos/user/s/sqian/www/triphoton/TIMESTAMP)")
    parser.add_argument("--year", default="2022", help="Year label for plots")
    parser.add_argument("--lumi", type=float, default=0.0, 
                       help="Integrated luminosity in fb^-1 (for label)")
    parser.add_argument("--data", action="store_true", 
                       help="Input is data (not MC)")
    
    # Trigger arguments
    parser.add_argument("--triple-trigger1", default="HLT_TriplePhoton_30_30_10_CaloIdLV2",
                       help="First triple photon trigger name", dest="triple_trigger1")
    parser.add_argument("--triple-trigger2", default="HLT_TriplePhoton_30_30_10_CaloIdLV2_R9IdVL",
                       help="Second triple photon trigger name", dest="triple_trigger2")
    parser.add_argument("--no-trigger", action="store_true",
                       help="Don't apply triggers (for debugging only)")
    
    # Plot selection
    parser.add_argument("--plots", choices=["all", "main", "triphoton", "rdf"], 
                       default="all",
                       help="Which plots to generate: 'all' (default), 'main', 'triphoton', or 'rdf'")
    
    # Other options
    parser.add_argument("--max-files", type=int, default=None, 
                       help="Maximum number of files to process")
    parser.add_argument("--no-html", action="store_true", 
                       help="Don't create HTML index files")
    
    args = parser.parse_args()
    
    # Create output directory with timestamp if not specified
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"/eos/user/s/sqian/www/triphoton/{timestamp}"
        print(f"Using timestamped output directory: {args.output}")
    
    os.makedirs(args.output, exist_ok=True)
    
    # Build base arguments that are common to all scripts
    base_args = [
        args.input,
        "--output", args.output,
        "--year", args.year,
        "--lumi", str(args.lumi),
    ]
    
    if args.data:
        base_args.append("--data")
    
    if args.max_files:
        base_args.extend(["--max-files", str(args.max_files)])
    
    if args.no_html:
        base_args.append("--no-html")
    
    # Build trigger arguments
    trigger_args = []
    if not args.no_trigger:
        trigger_args.extend([
            "--triple-trigger1", args.triple_trigger1,
            "--triple-trigger2", args.triple_trigger2,
        ])
    else:
        trigger_args.append("--no-trigger")
    
    success_count = 0
    total_count = 0
    
    # Run main plotting script (plot_triphoton.py)
    if args.plots in ["all", "main"]:
        total_count += 1
        main_args = base_args + trigger_args
        if run_plotting_script("plot_triphoton.py", main_args):
            success_count += 1
    
    # Run triphoton-specific plotting script (plot_triphoton_3gamma.py)
    if args.plots in ["all", "triphoton"]:
        total_count += 1
        triphoton_args = base_args.copy()
        # plot_triphoton_3gamma.py doesn't use triggers, so don't pass trigger args
        if run_plotting_script("plot_triphoton_3gamma.py", triphoton_args):
            success_count += 1
    
    # Run RDataFrame plotting script (plot_triphoton_rdf.py)
    if args.plots in ["all", "rdf"]:
        total_count += 1
        rdf_args = base_args.copy()
        # plot_triphoton_rdf.py doesn't use triggers, so don't pass trigger args
        if run_plotting_script("plot_triphoton_rdf.py", rdf_args):
            success_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY: {success_count}/{total_count} plotting scripts completed successfully")
    print(f"{'='*60}")
    
    if success_count == total_count:
        print(f"\n✓ All plots saved to: {args.output}/")
        if not args.no_html:
            print(f"View plots at: https://sqian.web.cern.ch/triphoton/{os.path.basename(args.output)}/")
        return 0
    else:
        print(f"\n⚠ Some plotting scripts failed. Check output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
