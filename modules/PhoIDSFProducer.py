import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection 
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

import math
import os
import correctionlib._core



class PhoIDSFProducer(Module):
  def __init__( self , year ):
    self.year = year
    # Map year to era string for correctionlib
    year_to_era = {
      "2016apv": "2016preVFP",
      "2016": "2016postVFP",
      "2017": "2017",
      "2018": "2018"
    }
    self.era = year_to_era.get(year, year)
    # Map year to CVMFS path structure
    year_to_cvmfs_path = {
      "2016apv": "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run2-2016preVFP-UL-NanoAODv9/latest/photon.json.gz",
      "2016": "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run2-2016postVFP-UL-NanoAODv9/latest/photon.json.gz",
      "2017": "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run2-2017-UL-NanoAODv9/latest/photon.json.gz",
      "2018": "/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/Run2-2018-UL-NanoAODv9/latest/photon.json.gz"
    }
    self.photon_sf_path = year_to_cvmfs_path.get(year, None)
    if self.photon_sf_path is None:
      # Fallback to local path if year not in mapping
      self.photon_sf_path = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/analysis/data/year%s/photon.json.gz" %(os.environ['CMSSW_BASE'], self.year)
    print('Photon SF path:', self.photon_sf_path)
    print('Era:', self.era)

  def beginJob(self):
    print('begin to set Photon ID SF --->>>')
    print('start to open SF correctionlib file --->>>')
    # Load correctionlib JSON file from CVMFS (single file contains all corrections)
    if not os.path.exists(self.photon_sf_path):
      # Try .json if .json.gz doesn't exist
      photon_sf_path_alt = self.photon_sf_path.replace('.json.gz', '.json')
      if os.path.exists(photon_sf_path_alt):
        self.photon_sf_path = photon_sf_path_alt
      else:
        raise FileNotFoundError(f"Photon SF file not found: {self.photon_sf_path}")
    
    self.evaluator = correctionlib._core.CorrectionSet.from_file(self.photon_sf_path)
    print('open SF file successfully:', self.photon_sf_path)

  def endJob(self):
    print('finish setting Photon ID SF --->>>')
    
  def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
    self.out = wrappedOutputTree
    self.out.branch('Photon_CutBased_MediumID_SF','F', lenVar='nPhoton')
    self.out.branch('Photon_CutBased_MediumID_SFerr','F', lenVar='nPhoton')
    self.out.branch('Photon_CutBased_TightID_SF','F', lenVar='nPhoton')
    self.out.branch('Photon_CutBased_TightID_SFerr','F', lenVar='nPhoton')
    self.out.branch('Photon_PixelVeto_MediumID_Inc_SF','F', lenVar='nPhoton')
    self.out.branch('Photon_PixelVeto_MediumID_high_SF','F', lenVar='nPhoton')
    self.out.branch('Photon_PixelVeto_MediumID_low_SF','F', lenVar='nPhoton')
    self.out.branch('Photon_PixelVeto_MediumID_Inc_SFerr','F', lenVar='nPhoton')
    self.out.branch('Photon_PixelVeto_MediumID_high_SFerr','F', lenVar='nPhoton')
    self.out.branch('Photon_PixelVeto_MediumID_low_SFerr','F', lenVar='nPhoton')
    self.out.branch('Photon_PixelVeto_TightID_Inc_SF','F', lenVar='nPhoton')
    self.out.branch('Photon_PixelVeto_TightID_high_SF','F', lenVar='nPhoton')
    self.out.branch('Photon_PixelVeto_TightID_low_SF','F', lenVar='nPhoton')
    self.out.branch('Photon_PixelVeto_TightID_Inc_SFerr','F', lenVar='nPhoton')
    self.out.branch('Photon_PixelVeto_TightID_high_SFerr','F', lenVar='nPhoton')
    self.out.branch('Photon_PixelVeto_TightID_low_SFerr','F', lenVar='nPhoton')
  def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
    pass

  def analyze(self, event):
    
    photons = Collection(event, "Photon")
    if not (len(photons)>0): pass
    Photon_CutBased_MediumID_SF = []
    Photon_CutBased_MediumID_SFerr = []
    Photon_CutBased_TightID_SF = []
    Photon_CutBased_TightID_SFerr = []
    Photon_PixelVeto_MediumID_Inc_SF = []
    Photon_PixelVeto_MediumID_Inc_SFerr = []
    Photon_PixelVeto_MediumID_high_SF = []
    Photon_PixelVeto_MediumID_high_SFerr = []
    Photon_PixelVeto_MediumID_low_SF = []
    Photon_PixelVeto_MediumID_low_SFerr = []
    Photon_PixelVeto_TightID_Inc_SF = []
    Photon_PixelVeto_TightID_high_SF = []
    Photon_PixelVeto_TightID_low_SF = []
    Photon_PixelVeto_TightID_Inc_SFerr = []
    Photon_PixelVeto_TightID_high_SFerr = []
    Photon_PixelVeto_TightID_low_SFerr = []
    
    for ipho in range(0, len(photons)):
      # Get photon properties
      eta = photons[ipho].eta
      pt = photons[ipho].pt
      abs_eta = abs(eta)
      r9 = photons[ipho].r9
      
      # Evaluate CutBased ID scale factors
      # Format: evaluator["UL-Photon-ID-SF"].evaluate(era, systematic, ID_level, eta, pt)
      sf_medium = 1.0
      sf_medium_err = 0.0
      try:
        corr_id = self.evaluator["UL-Photon-ID-SF"]
        sf_medium = corr_id.evaluate(self.era, "sf", "Medium", eta, pt)
        # Calculate error from systematic variations
        try:
          sf_medium_up = corr_id.evaluate(self.era, "sfup", "Medium", eta, pt)
          sf_medium_down = corr_id.evaluate(self.era, "sfdown", "Medium", eta, pt)
          sf_medium_err = max(abs(sf_medium_up - sf_medium), abs(sf_medium_down - sf_medium))
        except:
          sf_medium_err = 0.0
      except (KeyError, AttributeError) as e:
        print(f"Warning: Could not evaluate Medium ID SF: {e}")
      except Exception as e:
        print(f"Warning: Error evaluating Medium ID SF: {e}")
      
      Photon_CutBased_MediumID_SF.append(sf_medium)
      Photon_CutBased_MediumID_SFerr.append(sf_medium_err)
      
      sf_tight = 1.0
      sf_tight_err = 0.0
      try:
        corr_id = self.evaluator["UL-Photon-ID-SF"]
        sf_tight = corr_id.evaluate(self.era, "sf", "Tight", eta, pt)
        try:
          sf_tight_up = corr_id.evaluate(self.era, "sfup", "Tight", eta, pt)
          sf_tight_down = corr_id.evaluate(self.era, "sfdown", "Tight", eta, pt)
          sf_tight_err = max(abs(sf_tight_up - sf_tight), abs(sf_tight_down - sf_tight))
        except:
          sf_tight_err = 0.0
      except (KeyError, AttributeError) as e:
        print(f"Warning: Could not evaluate Tight ID SF: {e}")
      except Exception as e:
        print(f"Warning: Error evaluating Tight ID SF: {e}")
      
      Photon_CutBased_TightID_SF.append(sf_tight)
      Photon_CutBased_TightID_SFerr.append(sf_tight_err)
      
      # Evaluate PixelVeto scale factors
      # Format: evaluator["UL-Photon-PixVeto-SF"].evaluate(era, systematic, ID_level, region)
      # Region format: "EBInc", "EBHighR9", "EBLowR9", "EEInc", "EEHighR9", "EELowR9"
      if abs_eta < 1.566:
        # Barrel
        region_inc = "EBInc"
        region_high = "EBHighR9"
        region_low = "EBLowR9"
      else:
        # Endcap
        region_inc = "EEInc"
        region_high = "EEHighR9"
        region_low = "EELowR9"
      
      r9_category = "high" if r9 > 0.96 else "low"
      region_cat = region_high if r9_category == "high" else region_low
      
      # PixelVeto Medium ID
      sf_pv_med_inc = 1.0
      sf_pv_med_high = 0.0
      sf_pv_med_low = 0.0
      sf_pv_med_inc_err = 0.0
      sf_pv_med_high_err = 0.0
      sf_pv_med_low_err = 0.0
      
      try:
        corr_pv = self.evaluator["UL-Photon-PixVeto-SF"]
        # Inclusive SF
        sf_pv_med_inc = corr_pv.evaluate(self.era, "sf", "Medium", region_inc)
        try:
          sf_pv_med_inc_up = corr_pv.evaluate(self.era, "sfup", "Medium", region_inc)
          sf_pv_med_inc_down = corr_pv.evaluate(self.era, "sfdown", "Medium", region_inc)
          sf_pv_med_inc_err = max(abs(sf_pv_med_inc_up - sf_pv_med_inc), abs(sf_pv_med_inc_down - sf_pv_med_inc))
        except:
          sf_pv_med_inc_err = 0.0
        
        # Category-specific SF (high or low R9)
        sf_pv_med_cat = corr_pv.evaluate(self.era, "sf", "Medium", region_cat)
        try:
          sf_pv_med_cat_up = corr_pv.evaluate(self.era, "sfup", "Medium", region_cat)
          sf_pv_med_cat_down = corr_pv.evaluate(self.era, "sfdown", "Medium", region_cat)
          sf_pv_med_cat_err = max(abs(sf_pv_med_cat_up - sf_pv_med_cat), abs(sf_pv_med_cat_down - sf_pv_med_cat))
        except:
          sf_pv_med_cat_err = 0.0
        
        if r9_category == "high":
          sf_pv_med_high = sf_pv_med_cat
          sf_pv_med_high_err = sf_pv_med_cat_err
        else:
          sf_pv_med_low = sf_pv_med_cat
          sf_pv_med_low_err = sf_pv_med_cat_err
      except (KeyError, AttributeError) as e:
        print(f"Warning: Could not evaluate PixelVeto Medium ID SF: {e}")
      except Exception as e:
        print(f"Warning: Error evaluating PixelVeto Medium ID SF: {e}")
      
      Photon_PixelVeto_MediumID_Inc_SF.append(sf_pv_med_inc)
      Photon_PixelVeto_MediumID_high_SF.append(sf_pv_med_high)
      Photon_PixelVeto_MediumID_low_SF.append(sf_pv_med_low)
      Photon_PixelVeto_MediumID_Inc_SFerr.append(sf_pv_med_inc_err)
      Photon_PixelVeto_MediumID_high_SFerr.append(sf_pv_med_high_err)
      Photon_PixelVeto_MediumID_low_SFerr.append(sf_pv_med_low_err)
      
      # PixelVeto Tight ID
      sf_pv_tig_inc = 1.0
      sf_pv_tig_high = 0.0
      sf_pv_tig_low = 0.0
      sf_pv_tig_inc_err = 0.0
      sf_pv_tig_high_err = 0.0
      sf_pv_tig_low_err = 0.0
      
      try:
        corr_pv = self.evaluator["UL-Photon-PixVeto-SF"]
        # Inclusive SF
        sf_pv_tig_inc = corr_pv.evaluate(self.era, "sf", "Tight", region_inc)
        try:
          sf_pv_tig_inc_up = corr_pv.evaluate(self.era, "sfup", "Tight", region_inc)
          sf_pv_tig_inc_down = corr_pv.evaluate(self.era, "sfdown", "Tight", region_inc)
          sf_pv_tig_inc_err = max(abs(sf_pv_tig_inc_up - sf_pv_tig_inc), abs(sf_pv_tig_inc_down - sf_pv_tig_inc))
        except:
          sf_pv_tig_inc_err = 0.0
        
        # Category-specific SF (high or low R9)
        sf_pv_tig_cat = corr_pv.evaluate(self.era, "sf", "Tight", region_cat)
        try:
          sf_pv_tig_cat_up = corr_pv.evaluate(self.era, "sfup", "Tight", region_cat)
          sf_pv_tig_cat_down = corr_pv.evaluate(self.era, "sfdown", "Tight", region_cat)
          sf_pv_tig_cat_err = max(abs(sf_pv_tig_cat_up - sf_pv_tig_cat), abs(sf_pv_tig_cat_down - sf_pv_tig_cat))
        except:
          sf_pv_tig_cat_err = 0.0
        
        if r9_category == "high":
          sf_pv_tig_high = sf_pv_tig_cat
          sf_pv_tig_high_err = sf_pv_tig_cat_err
        else:
          sf_pv_tig_low = sf_pv_tig_cat
          sf_pv_tig_low_err = sf_pv_tig_cat_err
      except (KeyError, AttributeError) as e:
        print(f"Warning: Could not evaluate PixelVeto Tight ID SF: {e}")
      except Exception as e:
        print(f"Warning: Error evaluating PixelVeto Tight ID SF: {e}")
      
      Photon_PixelVeto_TightID_Inc_SF.append(sf_pv_tig_inc)
      Photon_PixelVeto_TightID_high_SF.append(sf_pv_tig_high)
      Photon_PixelVeto_TightID_low_SF.append(sf_pv_tig_low)
      Photon_PixelVeto_TightID_Inc_SFerr.append(sf_pv_tig_inc_err)
      Photon_PixelVeto_TightID_high_SFerr.append(sf_pv_tig_high_err)
      Photon_PixelVeto_TightID_low_SFerr.append(sf_pv_tig_low_err)

    self.out.fillBranch('Photon_CutBased_MediumID_SF', Photon_CutBased_MediumID_SF)
    self.out.fillBranch('Photon_CutBased_MediumID_SFerr', Photon_CutBased_MediumID_SFerr)
    self.out.fillBranch('Photon_CutBased_TightID_SF', Photon_CutBased_TightID_SF)
    self.out.fillBranch('Photon_CutBased_TightID_SFerr', Photon_CutBased_TightID_SFerr)
    self.out.fillBranch('Photon_PixelVeto_MediumID_Inc_SF', Photon_PixelVeto_MediumID_Inc_SF)
    self.out.fillBranch('Photon_PixelVeto_MediumID_Inc_SFerr', Photon_PixelVeto_MediumID_Inc_SFerr)
    self.out.fillBranch('Photon_PixelVeto_MediumID_high_SF', Photon_PixelVeto_MediumID_high_SF)
    self.out.fillBranch('Photon_PixelVeto_MediumID_high_SFerr', Photon_PixelVeto_MediumID_high_SFerr)
    self.out.fillBranch('Photon_PixelVeto_MediumID_low_SF', Photon_PixelVeto_MediumID_low_SF)
    self.out.fillBranch('Photon_PixelVeto_MediumID_low_SFerr', Photon_PixelVeto_MediumID_low_SFerr)
    self.out.fillBranch('Photon_PixelVeto_TightID_Inc_SF', Photon_PixelVeto_TightID_Inc_SF)
    self.out.fillBranch('Photon_PixelVeto_TightID_Inc_SFerr', Photon_PixelVeto_TightID_Inc_SFerr)
    self.out.fillBranch('Photon_PixelVeto_TightID_high_SF', Photon_PixelVeto_TightID_high_SF)
    self.out.fillBranch('Photon_PixelVeto_TightID_high_SFerr', Photon_PixelVeto_TightID_high_SFerr)
    self.out.fillBranch('Photon_PixelVeto_TightID_low_SF', Photon_PixelVeto_TightID_low_SF)
    self.out.fillBranch('Photon_PixelVeto_TightID_low_SFerr', Photon_PixelVeto_TightID_low_SFerr)

    return True

PhoIDSF2016apv = lambda: PhoIDSFProducer("2016apv")
PhoIDSF2016 = lambda: PhoIDSFProducer("2016")
PhoIDSF2017 = lambda: PhoIDSFProducer("2017")
PhoIDSF2018 = lambda: PhoIDSFProducer("2018")
