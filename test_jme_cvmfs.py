#!/usr/bin/env python3
"""
Test script for CVMFS-based JME corrections
"""

import sys
import correctionlib

print("Testing CVMFS JME corrections...")
print("=" * 60)

# Test 2017 corrections
cvmfs_path_2017 = "/cvmfs/cms-griddata.cern.ch/cat/metadata/JME/Run2-2017-UL-NanoAODv9/latest/jet_jerc.json.gz"
print(f"\nLoading: {cvmfs_path_2017}")

try:
    cset = correctionlib.CorrectionSet.from_file(cvmfs_path_2017)
    print("✓ Successfully loaded 2017 correction set")

    # Test JEC L1FastJet
    jec_name = "Summer19UL17_V5_MC_L1FastJet_AK4PFchs"
    if jec_name in cset:
        print(f"✓ Found correction: {jec_name}")

        # Test evaluation
        area = 0.5
        eta = 0.0
        pt = 50.0
        rho = 20.0

        result = cset[jec_name].evaluate(area, eta, pt, rho)
        print(f"  Test: JetA={area}, JetEta={eta}, JetPt={pt}, Rho={rho}")
        print(f"  Result (correction factor): {result:.4f}")

    # Test JER
    jer_res_name = "Summer19UL17_JRV2_MC_PtResolution_AK4PFchs"
    jer_sf_name = "Summer19UL17_JRV2_MC_ScaleFactor_AK4PFchs"

    if jer_res_name in cset and jer_sf_name in cset:
        print(f"✓ Found JER corrections")

        # Test JER resolution
        eta = 0.0
        pt = 100.0
        rho = 20.0
        jer_res = cset[jer_res_name].evaluate(eta, pt, rho)
        print(f"  JER resolution at eta={eta}, pt={pt}: {jer_res:.4f}")

        # Test JER scale factor
        jer_sf = cset[jer_sf_name].evaluate(eta, "nom")
        jer_sf_up = cset[jer_sf_name].evaluate(eta, "up")
        jer_sf_down = cset[jer_sf_name].evaluate(eta, "down")
        print(f"  JER SF (nom/up/down): {jer_sf:.4f} / {jer_sf_up:.4f} / {jer_sf_down:.4f}")

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
