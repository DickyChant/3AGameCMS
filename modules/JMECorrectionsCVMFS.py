#!/usr/bin/env python3
"""
CVMFS-based JME corrections for Run2 UL
Uses correctionlib JSON files from CVMFS instead of tar.gz files

Advantages over tar.gz approach:
- No local file storage needed
- Always up-to-date corrections from CVMFS
- Faster loading with correctionlib
- Modern JSON format (standard for Run3)
"""

from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
import ROOT
import correctionlib
import numpy as np

ROOT.PyConfig.IgnoreCommandLineOptions = True


class JMECorrectionsCVMFS(Module):
    """
    Apply JEC and JER corrections using CVMFS correctionlib files

    This is a simplified module that applies:
    - Jet Energy Corrections (JEC): L1FastJet, L2Relative, L3Absolute, L2L3Residual (data only)
    - Jet Energy Resolution (JER): smearing for MC

    For triphoton analysis, we primarily need jets for cleaning/overlap removal,
    so we apply nominal corrections without full systematic variations.
    """

    def __init__(self, year, is_mc=True, jet_type="AK4PFchs"):
        """
        Args:
            year: "UL2016_preVFP", "UL2016", "UL2017", or "UL2018"
            is_mc: True for MC, False for Data
            jet_type: "AK4PFchs" (only AK4PFchs supported for now)
        """
        self.year = year
        self.is_mc = is_mc
        self.jet_type = jet_type

        # Map year to CVMFS path
        year_to_cvmfs = {
            "UL2016_preVFP": "/cvmfs/cms-griddata.cern.ch/cat/metadata/JME/Run2-2016preVFP-UL-NanoAODv9/latest/jet_jerc.json.gz",
            "UL2016": "/cvmfs/cms-griddata.cern.ch/cat/metadata/JME/Run2-2016postVFP-UL-NanoAODv9/latest/jet_jerc.json.gz",
            "UL2017": "/cvmfs/cms-griddata.cern.ch/cat/metadata/JME/Run2-2017-UL-NanoAODv9/latest/jet_jerc.json.gz",
            "UL2018": "/cvmfs/cms-griddata.cern.ch/cat/metadata/JME/Run2-2018-UL-NanoAODv9/latest/jet_jerc.json.gz",
        }

        if year not in year_to_cvmfs:
            raise ValueError(f"Unsupported year: {year}")

        cvmfs_path = year_to_cvmfs[year]
        print(f"[JMECorrectionsCVMFS] Loading corrections from: {cvmfs_path}")

        # Load correction set
        self.cset = correctionlib.CorrectionSet.from_file(cvmfs_path)

        # Map year to correction tag prefixes
        self.tag_map = {
            "UL2016_preVFP": "Summer19UL16APV_V7",
            "UL2016": "Summer19UL16_V7",
            "UL2017": "Summer19UL17_V5",
            "UL2018": "Summer19UL18_V5",
        }

        self.jer_tag_map = {
            "UL2016_preVFP": "Summer20UL16APV_JRV3",
            "UL2016": "Summer20UL16_JRV3",
            "UL2017": "Summer19UL17_JRV2",
            "UL2018": "Summer19UL18_JRV2",
        }

        self.tag = self.tag_map[year]
        self.jer_tag = self.jer_tag_map[year]

        # Build correction names
        mc_or_data = "MC" if is_mc else "DATA"
        self.jec_names = {
            "L1FastJet": f"{self.tag}_{mc_or_data}_L1FastJet_{jet_type}",
            "L2Relative": f"{self.tag}_{mc_or_data}_L2Relative_{jet_type}",
            "L3Absolute": f"{self.tag}_{mc_or_data}_L3Absolute_{jet_type}",
        }

        if not is_mc:
            self.jec_names["L2L3Residual"] = f"{self.tag}_{mc_or_data}_L2L3Residual_{jet_type}"

        # JER corrections (MC only)
        if is_mc:
            self.jer_pt_res = f"{self.jer_tag}_MC_PtResolution_{jet_type}"
            self.jer_sf = f"{self.jer_tag}_MC_ScaleFactor_{jet_type}"

        print(f"[JMECorrectionsCVMFS] Year: {year}, MC: {is_mc}, JetType: {jet_type}")
        print(f"[JMECorrectionsCVMFS] JEC corrections: {list(self.jec_names.keys())}")
        if is_mc:
            print(f"[JMECorrectionsCVMFS] JER corrections: {self.jer_pt_res}, {self.jer_sf}")

    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree

        # Add output branches for corrected jet pt and mass
        self.out.branch("Jet_pt_nom", "F", lenVar="nJet")
        self.out.branch("Jet_mass_nom", "F", lenVar="nJet")

        if self.is_mc:
            self.out.branch("Jet_pt_jer_up", "F", lenVar="nJet")
            self.out.branch("Jet_pt_jer_down", "F", lenVar="nJet")

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        """
        Apply JEC and JER corrections to jets
        """
        # Get jets
        jets = Collection(event, "Jet")

        # Get rho (try different possible names)
        rho = None
        for rho_name in ["fixedGridRhoFastjetAll", "Rho_fixedGridRhoFastjetAll", "fixedGridRhoAll", "Rho"]:
            try:
                rho = getattr(event._tree, rho_name)
                break
            except:
                continue

        if rho is None:
            raise RuntimeError(
                "[JMECorrectionsCVMFS] Could not find rho branch! "
                "Tried: fixedGridRhoFastjetAll, Rho_fixedGridRhoFastjetAll, fixedGridRhoAll, Rho. "
                "JME corrections require rho for pileup offset corrections."
            )

        # Output arrays
        jet_pt_nom = np.zeros(len(jets), dtype=np.float32)
        jet_mass_nom = np.zeros(len(jets), dtype=np.float32)

        if self.is_mc:
            jet_pt_jer_up = np.zeros(len(jets), dtype=np.float32)
            jet_pt_jer_down = np.zeros(len(jets), dtype=np.float32)

            # Get GenJets for matching
            genjets = Collection(event, "GenJet")

        # Process each jet
        for i, jet in enumerate(jets):
            pt_raw = jet.pt * (1 - jet.rawFactor)  # Remove existing corrections
            mass_raw = jet.mass * (1 - jet.rawFactor)  # Remove existing corrections
            eta = jet.eta
            phi = jet.phi
            area = jet.area

            # Apply JEC corrections in order (track total correction factor)
            pt_corr = pt_raw
            jec_total = 1.0

            # L1FastJet (pileup offset)
            jec_l1 = self.cset[self.jec_names["L1FastJet"]].evaluate(area, eta, pt_raw, rho)
            pt_corr *= jec_l1
            jec_total *= jec_l1

            # L2Relative
            jec_l2 = self.cset[self.jec_names["L2Relative"]].evaluate(eta, pt_corr)
            pt_corr *= jec_l2
            jec_total *= jec_l2

            # L3Absolute
            jec_l3 = self.cset[self.jec_names["L3Absolute"]].evaluate(eta, pt_corr)
            pt_corr *= jec_l3
            jec_total *= jec_l3

            # L2L3Residual (data only)
            if not self.is_mc:
                jec_res = self.cset[self.jec_names["L2L3Residual"]].evaluate(eta, pt_corr)
                pt_corr *= jec_res
                jec_total *= jec_res

            # Apply total JEC to mass as well
            mass_corr = mass_raw * jec_total

            jet_pt_nom[i] = pt_corr
            jet_mass_nom[i] = mass_corr

            # Apply JER smearing for MC
            if self.is_mc:
                # Get JER parameters
                jer_res = self.cset[self.jer_pt_res].evaluate(eta, pt_corr, rho)
                jer_sf_nom = self.cset[self.jer_sf].evaluate(eta, "nom")
                jer_sf_up = self.cset[self.jer_sf].evaluate(eta, "up")
                jer_sf_down = self.cset[self.jer_sf].evaluate(eta, "down")

                # Match to GenJet
                matched_genjet = None
                min_dr = 0.2
                for genjet in genjets:
                    dr = np.sqrt((eta - genjet.eta)**2 + (phi - genjet.phi)**2)
                    if dr < min_dr and abs(pt_corr - genjet.pt) < 3 * jer_res * pt_corr:
                        matched_genjet = genjet
                        min_dr = dr

                if matched_genjet is not None:
                    # Hybrid method (matched to GenJet)
                    jer_smear_nom = 1 + (jer_sf_nom - 1) * (pt_corr - matched_genjet.pt) / pt_corr
                    jer_smear_up = 1 + (jer_sf_up - 1) * (pt_corr - matched_genjet.pt) / pt_corr
                    jer_smear_down = 1 + (jer_sf_down - 1) * (pt_corr - matched_genjet.pt) / pt_corr
                else:
                    # Stochastic smearing (no GenJet match)
                    # Use random Gaussian smearing
                    sigma_nom = jer_res * np.sqrt(max(jer_sf_nom**2 - 1, 0))
                    sigma_up = jer_res * np.sqrt(max(jer_sf_up**2 - 1, 0))
                    sigma_down = jer_res * np.sqrt(max(jer_sf_down**2 - 1, 0))

                    # Use jet phi as seed for reproducibility
                    np.random.seed(int(abs(phi * 1e6)) % (2**31))
                    jer_smear_nom = max(1 + np.random.normal(0, sigma_nom), 0)
                    jer_smear_up = max(1 + np.random.normal(0, sigma_up), 0)
                    jer_smear_down = max(1 + np.random.normal(0, sigma_down), 0)

                # Apply nominal JER to jet_pt_nom
                jet_pt_nom[i] *= jer_smear_nom
                jet_pt_jer_up[i] = pt_corr * jer_smear_up
                jet_pt_jer_down[i] = pt_corr * jer_smear_down

        # Fill output branches
        self.out.fillBranch("Jet_pt_nom", jet_pt_nom)
        self.out.fillBranch("Jet_mass_nom", jet_mass_nom)

        if self.is_mc:
            self.out.fillBranch("Jet_pt_jer_up", jet_pt_jer_up)
            self.out.fillBranch("Jet_pt_jer_down", jet_pt_jer_down)

        return True


# Convenience functions for common use cases
def JMECorrections2017(is_mc=True):
    """2017 UL JME corrections"""
    return JMECorrectionsCVMFS("UL2017", is_mc=is_mc)


def JMECorrections2018(is_mc=True):
    """2018 UL JME corrections"""
    return JMECorrectionsCVMFS("UL2018", is_mc=is_mc)


def JMECorrections2016apv(is_mc=True):
    """2016 preVFP UL JME corrections"""
    return JMECorrectionsCVMFS("UL2016_preVFP", is_mc=is_mc)


def JMECorrections2016(is_mc=True):
    """2016 postVFP UL JME corrections"""
    return JMECorrectionsCVMFS("UL2016", is_mc=is_mc)
