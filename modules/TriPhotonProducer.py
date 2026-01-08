import ROOT
from ROOT import TLorentzVector
ROOT.PyConfig.IgnoreCommandLineOptions = True

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

import math
import os,copy
import numpy as np

MW, MZ = 80.4, 91.2


class TriPhotonProducer(Module):
  def __init__(self , year):
    self.year = year
  def beginJob(self):
    pass
  def endJob(self):
    pass
  
  def checkHLT(self, event, trigger_base_name):
    """
    Check if an HLT trigger fired, handling different version suffixes.
    In NanoAOD, HLT branches may have version suffixes like _v1, _v2, etc.
    This function checks for the base name and common version suffixes.
    """
    # Try base name first (without _v suffix)
    try:
      if getattr(event, trigger_base_name) == 1:
        return True
    except:
      pass

    # Try with _v suffix (as shown in CSV files)
    try:
      if getattr(event, trigger_base_name + "_v") == 1:
        return True
    except:
      pass

    # Try common version suffixes (_v1, _v2, _v3, _v4, _v5)
    for v in range(1, 6):
      try:
        if getattr(event, trigger_base_name + "_v" + str(v)) == 1:
          return True
      except:
        pass

    return False
  def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
    self.out = wrappedOutputTree
    self.out.branch("HLT_passEle32WPTight", "I")
    
    # All photon-related HLT paths for 2017 and 2018 data
    # Double photon triggers
    self.out.branch("HLT_DoublePhoton85", "I")
    self.out.branch("HLT_DoublePhoton70", "I")
    
    # Diphoton triggers
    self.out.branch("HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass90", "I")
    self.out.branch("HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass95", "I")
    self.out.branch("HLT_Diphoton30PV_18PV_R9Id_AND_IsoCaloId_AND_HE_R9Id_PixelVeto_Mass55", "I")
    self.out.branch("HLT_Diphoton30_18_PVrealAND_R9Id_AND_IsoCaloId_AND_HE_R9Id_PixelVeto_Mass55", "I")
    self.out.branch("HLT_Diphoton30_18_PVrealAND_R9Id_AND_IsoCaloId_AND_HE_R9Id_NoPixelVeto_Mass55", "I")
    self.out.branch("HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto_Mass55", "I")
    self.out.branch("HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto", "I")
    
    # Triple photon triggers
    self.out.branch("HLT_TriplePhoton_20_20_20_CaloIdLV2", "I")
    self.out.branch("HLT_TriplePhoton_20_20_20_CaloIdLV2_R9IdVL", "I")
    self.out.branch("HLT_TriplePhoton_30_30_10_CaloIdLV2", "I")
    self.out.branch("HLT_TriplePhoton_30_30_10_CaloIdLV2_R9IdVL", "I")
    self.out.branch("HLT_TriplePhoton_35_35_5_CaloIdLV2_R9IdVL", "I")
    
    # Single photon triggers
    self.out.branch("HLT_Photon200", "I")
    self.out.branch("HLT_Photon300_NoHE", "I")
    self.out.branch("HLT_Photon40_HoverELoose", "I")
    self.out.branch("HLT_Photon50_HoverELoose", "I")
    self.out.branch("HLT_Photon60_HoverELoose", "I")
    self.out.branch("HLT_Photon60_R9Id90_CaloIdL_IsoL_DisplacedIdL_PFHT350MinPFJet15", "I")
    self.out.branch("HLT_Photon50_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3_PFMET50", "I")
    self.out.branch("HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3", "I")
    self.out.branch("HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ600DEta3", "I")
    self.out.branch("HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_CaloMJJ300_PFJetsMJJ400DEta3", "I")
    self.out.branch("HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_CaloMJJ400_PFJetsMJJ600DEta3", "I")
    self.out.branch("HLT_Photon110EB_TightID_TightIso", "I")
    self.out.branch("HLT_Photon120EB_TightID_TightIso", "I")
    self.out.branch("HLT_Photon35_TwoProngs35", "I")
    
    # Combined flags
    self.out.branch("HLT_passAnyTriplePhoton", "I")
    self.out.branch("HLT_passAnyDoublePhoton", "I")
    self.out.branch("HLT_passAnyDiphoton", "I")
    self.out.branch("HLT_passAnyPhoton", "I")
    self.out.branch("met_user","F")
    self.out.branch("met_phi_user","F")
    self.out.branch("GoodPhoton_id","I",lenVar="nGoodPhoton")
    self.out.branch("FakePhoton_id","I",lenVar="nFakePhoton")
    self.out.branch("TightJet_id","I",lenVar="nTightJet")
    self.out.branch("TightJet_pt","F",lenVar="nTightJet")
    self.out.branch("TightJet_eta","F",lenVar="nTightJet")
    self.out.branch("TightJet_phi","F",lenVar="nTightJet")
    self.out.branch("TightJet_mass","F",lenVar="nTightJet")
    self.out.branch("j1_pt","F")
    self.out.branch("j1_eta","F")
    self.out.branch("j1_phi","F")
    self.out.branch("j1_mass","F")
    self.out.branch("j2_pt","F")
    self.out.branch("j2_eta","F")
    self.out.branch("j2_phi","F")
    self.out.branch("j2_mass","F")
    self.out.branch("dRjj","F")
    self.out.branch("dEtajj","F")
    self.out.branch("dPhijj","F")
    self.out.branch("mjj","F")
    self.out.branch("SB_region","I")
    self.out.branch("SR_region","I")
    # fake_flag for 3 photons: 0=all good, 1=p3 fake, 2=p2 fake, 3=p2&p3 fake, 4=p1 fake, 5=p1&p3 fake, 6=p1&p2 fake, 7=all fake
    self.out.branch("fake_flag","I")
    # Sideband region: 1 or 2 photons
    self.out.branch("pho1_pt_SB","F")
    self.out.branch("pho1_eta_SB","F")
    self.out.branch("pho1_phi_SB","F")
    self.out.branch("pho2_pt_SB","F")
    self.out.branch("pho2_eta_SB","F")
    self.out.branch("pho2_phi_SB","F")
    self.out.branch("dR_p1p2_SB","F")
    self.out.branch("Maa_SB","F")
    # Signal region: 3 photons
    self.out.branch("pho1_pt_SR","F")
    self.out.branch("pho1_eta_SR","F")
    self.out.branch("pho1_phi_SR","F")
    self.out.branch("pho2_pt_SR","F")
    self.out.branch("pho2_eta_SR","F")
    self.out.branch("pho2_phi_SR","F")
    self.out.branch("pho3_pt_SR","F")
    self.out.branch("pho3_eta_SR","F")
    self.out.branch("pho3_phi_SR","F")
    self.out.branch("dR_p1p2_SR","F")
    self.out.branch("dR_p1p3_SR","F")
    self.out.branch("dR_p2p3_SR","F")
    self.out.branch("dPhi_p1p2_SR","F")
    self.out.branch("dPhi_p1p3_SR","F")
    self.out.branch("dPhi_p2p3_SR","F")
    self.out.branch("dEta_p1p2_SR","F")
    self.out.branch("dEta_p1p3_SR","F")
    self.out.branch("dEta_p2p3_SR","F")
    self.out.branch("M_p1p2","F")
    self.out.branch("M_p1p3","F")
    self.out.branch("M_p2p3","F")
    self.out.branch("Maaa","F")
    self.out.branch("Ptaaa","F")
    self.out.branch("Etaaaa","F")
    self.out.branch("Phiaaa","F")

    self.is_mc = bool(inputTree.GetBranch("GenJet_pt"))
    self.is_lhe = bool(inputTree.GetBranch("nLHEPart"))

  def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
    pass

  def analyze(self, event):
    if (event.PV_npvsGood<1): return False

    met_user=-99
    met_phi_user=-99
    # Run 3 (2022/2022EE) uses DeepMET
    if self.year in ["2022", "2022EE"]:
      met_user=event.DeepMETResolutionTune_pt
      met_phi_user=event.DeepMETResolutionTune_phi
    else:
      # Run 2 (2017/2018) uses PFMET
      # Note: MET is only stored for reference, not used in event selection
      # JME corrections are applied to jets (used for photon cleaning)
      met_user = event.PFMET_pt
      met_phi_user = event.PFMET_phi

    self.out.fillBranch("met_user",met_user)
    self.out.fillBranch("met_phi_user",met_phi_user)

    # recover HLT
    HLT_passEle32WPTight=0
    if self.year=="2017":
      trgobjs=Collection(event, 'TrigObj')
      if event.HLT_Ele32_WPTight_Gsf_L1DoubleEG==1:
        for iobj in range(0,event.nTrigObj):
          if trgobjs[iobj].id==11 and (trgobjs[iobj].filterBits & (1<<10))== (1<<10):
            HLT_passEle32WPTight=1

    self.out.fillBranch("HLT_passEle32WPTight",HLT_passEle32WPTight)

    # All photon-related HLT paths for 2017 and 2018 data and MC
    # Note: 
    #   - For DATA: HLT flags are stored AND used for filtering (require at least one photon HLT)
    #   - For MC: HLT flags are stored but NOT used for filtering (study pass vs fail)
    # For data, flags are checked with run range checks for proper trigger selection
    # Initialize all to 0
    # Double photon
    HLT_DoublePhoton85 = 0
    HLT_DoublePhoton70 = 0
    # Diphoton
    HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass90 = 0
    HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass95 = 0
    HLT_Diphoton30PV_18PV_R9Id_AND_IsoCaloId_AND_HE_R9Id_PixelVeto_Mass55 = 0
    HLT_Diphoton30_18_PVrealAND_R9Id_AND_IsoCaloId_AND_HE_R9Id_PixelVeto_Mass55 = 0
    HLT_Diphoton30_18_PVrealAND_R9Id_AND_IsoCaloId_AND_HE_R9Id_NoPixelVeto_Mass55 = 0
    HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto_Mass55 = 0
    HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto = 0
    # Triple photon
    HLT_TriplePhoton_20_20_20_CaloIdLV2 = 0
    HLT_TriplePhoton_20_20_20_CaloIdLV2_R9IdVL = 0
    HLT_TriplePhoton_30_30_10_CaloIdLV2 = 0
    HLT_TriplePhoton_30_30_10_CaloIdLV2_R9IdVL = 0
    HLT_TriplePhoton_35_35_5_CaloIdLV2_R9IdVL = 0
    # Single photon
    HLT_Photon200 = 0
    HLT_Photon300_NoHE = 0
    HLT_Photon40_HoverELoose = 0
    HLT_Photon50_HoverELoose = 0
    HLT_Photon60_HoverELoose = 0
    HLT_Photon60_R9Id90_CaloIdL_IsoL_DisplacedIdL_PFHT350MinPFJet15 = 0
    HLT_Photon50_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3_PFMET50 = 0
    HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3 = 0
    HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ600DEta3 = 0
    HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_CaloMJJ300_PFJetsMJJ400DEta3 = 0
    HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_CaloMJJ400_PFJetsMJJ600DEta3 = 0
    HLT_Photon110EB_TightID_TightIso = 0
    HLT_Photon120EB_TightID_TightIso = 0
    HLT_Photon35_TwoProngs35 = 0
    # Combined flags
    HLT_passAnyTriplePhoton = 0
    HLT_passAnyDoublePhoton = 0
    HLT_passAnyDiphoton = 0
    HLT_passAnyPhoton = 0

    # Check triggers for both data and MC
    # For data: check within appropriate run ranges (for proper trigger selection and filtering)
    # For MC: check all triggers regardless of run number (to study pass vs fail, no filtering)
    run_number = event.run if not self.is_mc else None
    
    if self.year == "2017":
      # For MC, check all triggers. For data, check within run ranges
      check_all = self.is_mc
      
      # 2017: Most triggers available from run 296070 to 306460
      if check_all or (run_number >= 296070 and run_number <= 306460):
        # Double photon triggers
        if self.checkHLT(event, 'HLT_DoublePhoton85'):
          HLT_DoublePhoton85 = 1
        if self.checkHLT(event, 'HLT_DoublePhoton70'):
          HLT_DoublePhoton70 = 1
        # Diphoton triggers
        if self.checkHLT(event, 'HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass90'):
          HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass90 = 1
        if self.checkHLT(event, 'HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass95'):
          HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass95 = 1
        if self.checkHLT(event, 'HLT_Diphoton30PV_18PV_R9Id_AND_IsoCaloId_AND_HE_R9Id_PixelVeto_Mass55'):
          HLT_Diphoton30PV_18PV_R9Id_AND_IsoCaloId_AND_HE_R9Id_PixelVeto_Mass55 = 1
        # Single photon triggers
        if self.checkHLT(event, 'HLT_Photon200'):
          HLT_Photon200 = 1
        if self.checkHLT(event, 'HLT_Photon300_NoHE'):
          HLT_Photon300_NoHE = 1
        if self.checkHLT(event, 'HLT_Photon60_R9Id90_CaloIdL_IsoL_DisplacedIdL_PFHT350MinPFJet15'):
          HLT_Photon60_R9Id90_CaloIdL_IsoL_DisplacedIdL_PFHT350MinPFJet15 = 1
        
        # 2017: Triple photon triggers available from run 302026 to 306460
        if check_all or (run_number >= 302026 and run_number <= 306460):
          if self.checkHLT(event, 'HLT_TriplePhoton_20_20_20_CaloIdLV2'):
            HLT_TriplePhoton_20_20_20_CaloIdLV2 = 1
          if self.checkHLT(event, 'HLT_TriplePhoton_20_20_20_CaloIdLV2_R9IdVL'):
            HLT_TriplePhoton_20_20_20_CaloIdLV2_R9IdVL = 1
          if self.checkHLT(event, 'HLT_TriplePhoton_30_30_10_CaloIdLV2'):
            HLT_TriplePhoton_30_30_10_CaloIdLV2 = 1
          if self.checkHLT(event, 'HLT_TriplePhoton_30_30_10_CaloIdLV2_R9IdVL'):
            HLT_TriplePhoton_30_30_10_CaloIdLV2_R9IdVL = 1
          if self.checkHLT(event, 'HLT_TriplePhoton_35_35_5_CaloIdLV2_R9IdVL'):
            HLT_TriplePhoton_35_35_5_CaloIdLV2_R9IdVL = 1
        
        # 2017: Late-run diphoton triggers from run 305405 to 306460
        if check_all or (run_number >= 305405 and run_number <= 306460):
          if self.checkHLT(event, 'HLT_Diphoton30_18_PVrealAND_R9Id_AND_IsoCaloId_AND_HE_R9Id_PixelVeto_Mass55'):
            HLT_Diphoton30_18_PVrealAND_R9Id_AND_IsoCaloId_AND_HE_R9Id_PixelVeto_Mass55 = 1
          if self.checkHLT(event, 'HLT_Diphoton30_18_PVrealAND_R9Id_AND_IsoCaloId_AND_HE_R9Id_NoPixelVeto_Mass55'):
            HLT_Diphoton30_18_PVrealAND_R9Id_AND_IsoCaloId_AND_HE_R9Id_NoPixelVeto_Mass55 = 1
          if self.checkHLT(event, 'HLT_Photon50_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3_PFMET50'):
            HLT_Photon50_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3_PFMET50 = 1
          if self.checkHLT(event, 'HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3'):
            HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3 = 1
          if self.checkHLT(event, 'HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ600DEta3'):
            HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ600DEta3 = 1
        
        # 2017: Very low lumi triggers from run 295965 to 306460
        if check_all or (run_number >= 295965 and run_number <= 306460):
          if self.checkHLT(event, 'HLT_Photon40_HoverELoose'):
            HLT_Photon40_HoverELoose = 1
          if self.checkHLT(event, 'HLT_Photon50_HoverELoose'):
            HLT_Photon50_HoverELoose = 1
          if self.checkHLT(event, 'HLT_Photon60_HoverELoose'):
            HLT_Photon60_HoverELoose = 1
      
    elif self.year == "2018":
      # For MC, check all triggers. For data, check within run ranges
      check_all = self.is_mc
      
      # 2018: Most triggers available from run 315252 to 325175
      if check_all or (run_number >= 315252 and run_number <= 325175):
        # Double photon triggers
        if self.checkHLT(event, 'HLT_DoublePhoton85'):
          HLT_DoublePhoton85 = 1
        if self.checkHLT(event, 'HLT_DoublePhoton70'):
          HLT_DoublePhoton70 = 1
        # Diphoton triggers
        if self.checkHLT(event, 'HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass90'):
          HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass90 = 1
        if self.checkHLT(event, 'HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass95'):
          HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass95 = 1
        if self.checkHLT(event, 'HLT_Diphoton30PV_18PV_R9Id_AND_IsoCaloId_AND_HE_R9Id_PixelVeto_Mass55'):
          HLT_Diphoton30PV_18PV_R9Id_AND_IsoCaloId_AND_HE_R9Id_PixelVeto_Mass55 = 1
        # Triple photon triggers
        if self.checkHLT(event, 'HLT_TriplePhoton_20_20_20_CaloIdLV2'):
          HLT_TriplePhoton_20_20_20_CaloIdLV2 = 1
        if self.checkHLT(event, 'HLT_TriplePhoton_20_20_20_CaloIdLV2_R9IdVL'):
          HLT_TriplePhoton_20_20_20_CaloIdLV2_R9IdVL = 1
        if self.checkHLT(event, 'HLT_TriplePhoton_30_30_10_CaloIdLV2'):
          HLT_TriplePhoton_30_30_10_CaloIdLV2 = 1
        if self.checkHLT(event, 'HLT_TriplePhoton_30_30_10_CaloIdLV2_R9IdVL'):
          HLT_TriplePhoton_30_30_10_CaloIdLV2_R9IdVL = 1
        if self.checkHLT(event, 'HLT_TriplePhoton_35_35_5_CaloIdLV2_R9IdVL'):
          HLT_TriplePhoton_35_35_5_CaloIdLV2_R9IdVL = 1
        # Single photon triggers
        if self.checkHLT(event, 'HLT_Photon200'):
          HLT_Photon200 = 1
        if self.checkHLT(event, 'HLT_Photon300_NoHE'):
          HLT_Photon300_NoHE = 1
        if self.checkHLT(event, 'HLT_Photon60_R9Id90_CaloIdL_IsoL_DisplacedIdL_PFHT350MinPFJet15'):
          HLT_Photon60_R9Id90_CaloIdL_IsoL_DisplacedIdL_PFHT350MinPFJet15 = 1
        if self.checkHLT(event, 'HLT_Photon50_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3_PFMET50'):
          HLT_Photon50_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3_PFMET50 = 1
        if self.checkHLT(event, 'HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3'):
          HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3 = 1
        if self.checkHLT(event, 'HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ600DEta3'):
          HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ600DEta3 = 1
        if self.checkHLT(event, 'HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_CaloMJJ300_PFJetsMJJ400DEta3'):
          HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_CaloMJJ300_PFJetsMJJ400DEta3 = 1
        if self.checkHLT(event, 'HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_CaloMJJ400_PFJetsMJJ600DEta3'):
          HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_CaloMJJ400_PFJetsMJJ600DEta3 = 1
      
      # 2018: Early-run diphoton triggers from run 315252 to 315973
      if check_all or (run_number >= 315252 and run_number <= 315973):
        if self.checkHLT(event, 'HLT_Diphoton30_18_PVrealAND_R9Id_AND_IsoCaloId_AND_HE_R9Id_PixelVeto_Mass55'):
          HLT_Diphoton30_18_PVrealAND_R9Id_AND_IsoCaloId_AND_HE_R9Id_PixelVeto_Mass55 = 1
        if self.checkHLT(event, 'HLT_Diphoton30_18_PVrealAND_R9Id_AND_IsoCaloId_AND_HE_R9Id_NoPixelVeto_Mass55'):
          HLT_Diphoton30_18_PVrealAND_R9Id_AND_IsoCaloId_AND_HE_R9Id_NoPixelVeto_Mass55 = 1
      
      # 2018: Late-run triggers from run 315974 to 325175
      if check_all or (run_number >= 315974 and run_number <= 325175):
        if self.checkHLT(event, 'HLT_Photon110EB_TightID_TightIso'):
          HLT_Photon110EB_TightID_TightIso = 1
        if self.checkHLT(event, 'HLT_Photon120EB_TightID_TightIso'):
          HLT_Photon120EB_TightID_TightIso = 1
        if self.checkHLT(event, 'HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto_Mass55'):
          HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto_Mass55 = 1
        if self.checkHLT(event, 'HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto'):
          HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto = 1
      
      # 2018: Tau trigger from run 317509 to 325175
      if check_all or (run_number >= 317509 and run_number <= 325175):
        if self.checkHLT(event, 'HLT_Photon35_TwoProngs35'):
          HLT_Photon35_TwoProngs35 = 1

    # Set combined flags
    if (HLT_TriplePhoton_20_20_20_CaloIdLV2 == 1 or 
        HLT_TriplePhoton_20_20_20_CaloIdLV2_R9IdVL == 1 or 
        HLT_TriplePhoton_30_30_10_CaloIdLV2 == 1 or 
        HLT_TriplePhoton_30_30_10_CaloIdLV2_R9IdVL == 1 or 
        HLT_TriplePhoton_35_35_5_CaloIdLV2_R9IdVL == 1):
      HLT_passAnyTriplePhoton = 1
    
    if (HLT_DoublePhoton85 == 1 or HLT_DoublePhoton70 == 1):
      HLT_passAnyDoublePhoton = 1
    
    if (HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass90 == 1 or
        HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass95 == 1 or
        HLT_Diphoton30PV_18PV_R9Id_AND_IsoCaloId_AND_HE_R9Id_PixelVeto_Mass55 == 1 or
        HLT_Diphoton30_18_PVrealAND_R9Id_AND_IsoCaloId_AND_HE_R9Id_PixelVeto_Mass55 == 1 or
        HLT_Diphoton30_18_PVrealAND_R9Id_AND_IsoCaloId_AND_HE_R9Id_NoPixelVeto_Mass55 == 1 or
        HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto_Mass55 == 1 or
        HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto == 1):
      HLT_passAnyDiphoton = 1
    
    if (HLT_passAnyTriplePhoton == 1 or HLT_passAnyDoublePhoton == 1 or 
        HLT_passAnyDiphoton == 1 or HLT_Photon200 == 1 or HLT_Photon300_NoHE == 1 or
        HLT_Photon40_HoverELoose == 1 or HLT_Photon50_HoverELoose == 1 or
        HLT_Photon60_HoverELoose == 1 or HLT_Photon60_R9Id90_CaloIdL_IsoL_DisplacedIdL_PFHT350MinPFJet15 == 1 or
        HLT_Photon50_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3_PFMET50 == 1 or
        HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3 == 1 or
        HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ600DEta3 == 1 or
        HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_CaloMJJ300_PFJetsMJJ400DEta3 == 1 or
        HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_CaloMJJ400_PFJetsMJJ600DEta3 == 1 or
        HLT_Photon110EB_TightID_TightIso == 1 or HLT_Photon120EB_TightID_TightIso == 1 or
        HLT_Photon35_TwoProngs35 == 1):
      HLT_passAnyPhoton = 1

    # Filter events based on HLT flags
    # For data: require at least one photon-related HLT to fire
    # For MC: no filtering (store all events to study pass vs fail)
    if not self.is_mc and HLT_passAnyPhoton == 0:
      return False

    # Fill all HLT branches
    # Double photon
    self.out.fillBranch("HLT_DoublePhoton85", HLT_DoublePhoton85)
    self.out.fillBranch("HLT_DoublePhoton70", HLT_DoublePhoton70)
    # Diphoton
    self.out.fillBranch("HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass90", HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass90)
    self.out.fillBranch("HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass95", HLT_Diphoton30_22_R9Id_OR_IsoCaloId_AND_HE_R9Id_Mass95)
    self.out.fillBranch("HLT_Diphoton30PV_18PV_R9Id_AND_IsoCaloId_AND_HE_R9Id_PixelVeto_Mass55", HLT_Diphoton30PV_18PV_R9Id_AND_IsoCaloId_AND_HE_R9Id_PixelVeto_Mass55)
    self.out.fillBranch("HLT_Diphoton30_18_PVrealAND_R9Id_AND_IsoCaloId_AND_HE_R9Id_PixelVeto_Mass55", HLT_Diphoton30_18_PVrealAND_R9Id_AND_IsoCaloId_AND_HE_R9Id_PixelVeto_Mass55)
    self.out.fillBranch("HLT_Diphoton30_18_PVrealAND_R9Id_AND_IsoCaloId_AND_HE_R9Id_NoPixelVeto_Mass55", HLT_Diphoton30_18_PVrealAND_R9Id_AND_IsoCaloId_AND_HE_R9Id_NoPixelVeto_Mass55)
    self.out.fillBranch("HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto_Mass55", HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto_Mass55)
    self.out.fillBranch("HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto", HLT_Diphoton30_18_R9IdL_AND_HE_AND_IsoCaloId_NoPixelVeto)
    # Triple photon
    self.out.fillBranch("HLT_TriplePhoton_20_20_20_CaloIdLV2", HLT_TriplePhoton_20_20_20_CaloIdLV2)
    self.out.fillBranch("HLT_TriplePhoton_20_20_20_CaloIdLV2_R9IdVL", HLT_TriplePhoton_20_20_20_CaloIdLV2_R9IdVL)
    self.out.fillBranch("HLT_TriplePhoton_30_30_10_CaloIdLV2", HLT_TriplePhoton_30_30_10_CaloIdLV2)
    self.out.fillBranch("HLT_TriplePhoton_30_30_10_CaloIdLV2_R9IdVL", HLT_TriplePhoton_30_30_10_CaloIdLV2_R9IdVL)
    self.out.fillBranch("HLT_TriplePhoton_35_35_5_CaloIdLV2_R9IdVL", HLT_TriplePhoton_35_35_5_CaloIdLV2_R9IdVL)
    # Single photon
    self.out.fillBranch("HLT_Photon200", HLT_Photon200)
    self.out.fillBranch("HLT_Photon300_NoHE", HLT_Photon300_NoHE)
    self.out.fillBranch("HLT_Photon40_HoverELoose", HLT_Photon40_HoverELoose)
    self.out.fillBranch("HLT_Photon50_HoverELoose", HLT_Photon50_HoverELoose)
    self.out.fillBranch("HLT_Photon60_HoverELoose", HLT_Photon60_HoverELoose)
    self.out.fillBranch("HLT_Photon60_R9Id90_CaloIdL_IsoL_DisplacedIdL_PFHT350MinPFJet15", HLT_Photon60_R9Id90_CaloIdL_IsoL_DisplacedIdL_PFHT350MinPFJet15)
    self.out.fillBranch("HLT_Photon50_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3_PFMET50", HLT_Photon50_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3_PFMET50)
    self.out.fillBranch("HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3", HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ300DEta3)
    self.out.fillBranch("HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ600DEta3", HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_PFJetsMJJ600DEta3)
    self.out.fillBranch("HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_CaloMJJ300_PFJetsMJJ400DEta3", HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_CaloMJJ300_PFJetsMJJ400DEta3)
    self.out.fillBranch("HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_CaloMJJ400_PFJetsMJJ600DEta3", HLT_Photon75_R9Id90_HE10_IsoM_EBOnly_CaloMJJ400_PFJetsMJJ600DEta3)
    self.out.fillBranch("HLT_Photon110EB_TightID_TightIso", HLT_Photon110EB_TightID_TightIso)
    self.out.fillBranch("HLT_Photon120EB_TightID_TightIso", HLT_Photon120EB_TightID_TightIso)
    self.out.fillBranch("HLT_Photon35_TwoProngs35", HLT_Photon35_TwoProngs35)
    # Combined flags
    self.out.fillBranch("HLT_passAnyTriplePhoton", HLT_passAnyTriplePhoton)
    self.out.fillBranch("HLT_passAnyDoublePhoton", HLT_passAnyDoublePhoton)
    self.out.fillBranch("HLT_passAnyDiphoton", HLT_passAnyDiphoton)
    self.out.fillBranch("HLT_passAnyPhoton", HLT_passAnyPhoton)

    GoodPhoton_id = []
    FakePhoton_id = []

    photons = Collection(event, 'Photon')
    for ipho in range(0, event.nPhoton):
      pt_tmp=photons[ipho].pt
      bitmap=photons[ipho].vidNestedWPBitmap
      hoe_bits = (bitmap >> 4) & 0b11
      sigmaieie_bits = (bitmap >> 6) & 0b11
      pfcha_bits = (bitmap >> 8) & 0b11
      pfneu_bits = (bitmap >> 10) & 0b11
      pfpho_bits = (bitmap >> 12) & 0b11
      if photons[ipho].pt<20:continue
      if abs(photons[ipho].eta)>1.4442 and abs(photons[ipho].eta)<1.57:continue
      if photons[ipho].pixelSeed:continue
      if photons[ipho].cutBased>1:
        GoodPhoton_id.append(ipho)

      elif (sigmaieie_bits>1 and pfcha_bits>1 and pfneu_bits>1 and pfpho_bits>1) or (hoe_bits>1 and pfcha_bits>1 and pfneu_bits>1 and pfpho_bits>1) or (hoe_bits>1 and sigmaieie_bits>1 and pfneu_bits>1 and pfpho_bits>1) or (hoe_bits>1 and sigmaieie_bits>1 and pfcha_bits>1 and pfpho_bits>1) or (hoe_bits>1 and sigmaieie_bits>1 and pfcha_bits>1 and pfneu_bits>1):
        FakePhoton_id.append(ipho)

    LooseElectron_id = []
    eles = Collection(event, 'Electron')
    for iele in range(0, event.nElectron):
      if eles[iele].convVeto:continue
      if eles[iele].pt>10 and eles[iele].cutBased>0:
        LooseElectron_id.append(iele)

    LooseMuon_id = []
    muons = Collection(event, 'Muon')
    for imu in range(0, event.nMuon):
      if muons[imu].looseId and muons[imu].pt>10:
        LooseMuon_id.append(imu)

    jets = Collection(event, 'Jet')
    TightJet_id = []
    TightJet_pt = []
    TightJet_eta = []
    TightJet_phi = []
    TightJet_mass = []
    TightJet_v4 = []
    jet_v4_temp=TLorentzVector()
    lep_v4_temp=TLorentzVector()
    # Run3 uses different jet branch names (pt instead of pt_nom)
    use_nom = self.year not in ["2022", "2022EE"]
    for ijet in range(0, event.nJet):
      jet_pt = jets[ijet].pt_nom if use_nom else jets[ijet].pt
      jet_mass = jets[ijet].mass_nom if use_nom else jets[ijet].mass
      if abs(jets[ijet].eta)>4.7 or jet_pt<30: continue
      # Apply jetId cut if branch exists (may not exist in pre-skimmed files)
      try:
        if jets[ijet].jetId<6:continue
      except:
        pass
      jet_v4_temp.SetPtEtaPhiM(jet_pt,jets[ijet].eta,jets[ijet].phi,jet_mass)
      pass_mu_dr=1
      pass_ele_dr=1
      pass_jet_dr=1

      for imu in range(0,len(LooseMuon_id)):
        if pass_mu_dr<1:continue
        mid_tmp=LooseMuon_id[imu]
        lep_v4_temp.SetPtEtaPhiM(muons[mid_tmp].pt, muons[mid_tmp].eta, muons[mid_tmp].phi, muons[mid_tmp].mass)
        if jet_v4_temp.DeltaR(lep_v4_temp)<0.4:pass_mu_dr=0
      
      for iele in range(0,len(LooseElectron_id)):
        if pass_ele_dr<1:continue
        eid_tmp=LooseElectron_id[iele]
        lep_v4_temp.SetPtEtaPhiM(eles[eid_tmp].pt, eles[eid_tmp].eta, eles[eid_tmp].phi, eles[eid_tmp].mass)
        if jet_v4_temp.DeltaR(lep_v4_temp)<0.4:pass_ele_dr=0

      if len(TightJet_id)>0:
        for ij in range(0,len(TightJet_id)):
          if jet_v4_temp.DeltaR(TightJet_v4[ij])<0.4:pass_jet_dr=0

      if pass_mu_dr>0 and pass_ele_dr>0 and pass_jet_dr>0:
        TightJet_id.append(ijet)
        TightJet_v4.append(jet_v4_temp.Clone())
        TightJet_pt.append(jet_v4_temp.Clone().Pt())
        TightJet_eta.append(jet_v4_temp.Clone().Eta())
        TightJet_phi.append(jet_v4_temp.Clone().Phi())
        TightJet_mass.append(jet_v4_temp.Clone().M())

    self.out.fillBranch("TightJet_id", TightJet_id)
    self.out.fillBranch("TightJet_pt", TightJet_pt)
    self.out.fillBranch("TightJet_eta", TightJet_eta)
    self.out.fillBranch("TightJet_phi", TightJet_phi)
    self.out.fillBranch("TightJet_mass", TightJet_mass)
    self.out.fillBranch("GoodPhoton_id", GoodPhoton_id)
    self.out.fillBranch("FakePhoton_id", FakePhoton_id)

    # Require at least 1 photon (good or fake)
    if len(GoodPhoton_id)+len(FakePhoton_id)==0:return False

    # Initialize jet variables with default values
    j1_pt=-99
    j1_eta=-99
    j1_phi=-99
    j1_mass=-99
    j2_pt=-99
    j2_eta=-99
    j2_phi=-99
    j2_mass=-99
    dRjj=-99
    dEtajj=-99
    dPhijj=-99
    mjj=-99
    j1_p4=TLorentzVector()
    j2_p4=TLorentzVector()
    
    # Fill jet variables if jets exist
    if len(TightJet_id)>=1:
      j1_pt = jets[TightJet_id[0]].pt_nom if use_nom else jets[TightJet_id[0]].pt
      j1_eta=jets[TightJet_id[0]].eta
      j1_phi=jets[TightJet_id[0]].phi
      j1_mass = jets[TightJet_id[0]].mass_nom if use_nom else jets[TightJet_id[0]].mass
      j1_p4.SetPtEtaPhiM(j1_pt,j1_eta,j1_phi,j1_mass)

    if len(TightJet_id)>=2:
      j2_pt = jets[TightJet_id[1]].pt_nom if use_nom else jets[TightJet_id[1]].pt
      j2_eta=jets[TightJet_id[1]].eta
      j2_phi=jets[TightJet_id[1]].phi
      j2_mass = jets[TightJet_id[1]].mass_nom if use_nom else jets[TightJet_id[1]].mass
      j2_p4.SetPtEtaPhiM(j2_pt,j2_eta,j2_phi,j2_mass)
      dRjj=j1_p4.DeltaR(j2_p4)
      dEtajj=abs(j1_eta - j2_eta)
      dPhijj=j1_p4.DeltaPhi(j2_p4)
      mjj=(j1_p4 + j2_p4).M()
    
    self.out.fillBranch("j1_pt", j1_pt)
    self.out.fillBranch("j1_eta", j1_eta)
    self.out.fillBranch("j1_phi", j1_phi)
    self.out.fillBranch("j1_mass", j1_mass)
    self.out.fillBranch("j2_pt", j2_pt)
    self.out.fillBranch("j2_eta", j2_eta)
    self.out.fillBranch("j2_phi", j2_phi)
    self.out.fillBranch("j2_mass", j2_mass)
    self.out.fillBranch("dRjj", dRjj)
    self.out.fillBranch("dEtajj", dEtajj)
    self.out.fillBranch("dPhijj", dPhijj)
    self.out.fillBranch("mjj", mjj)

    SB_region=-1
    SR_region=-1
    # fake_flag for 3 photons: uses binary encoding
    # 0=all good(000), 1=p3 fake(001), 2=p2 fake(010), 3=p2&p3 fake(011), 
    # 4=p1 fake(100), 5=p1&p3 fake(101), 6=p1&p2 fake(110), 7=all fake(111)
    fake_flag=-99
    # Sideband variables (1 or 2 photons)
    pho1_pt_SB=-99
    pho1_eta_SB=-99
    pho1_phi_SB=-99
    pho2_pt_SB=-99
    pho2_eta_SB=-99
    pho2_phi_SB=-99
    dR_p1p2_SB=-99
    Maa_SB=-99
    # Signal region variables (3 photons)
    pho1_pt_SR=-99
    pho1_eta_SR=-99
    pho1_phi_SR=-99
    pho2_pt_SR=-99
    pho2_eta_SR=-99
    pho2_phi_SR=-99
    pho3_pt_SR=-99
    pho3_eta_SR=-99
    pho3_phi_SR=-99
    dR_p1p2_SR=-99
    dR_p1p3_SR=-99
    dR_p2p3_SR=-99
    dPhi_p1p2_SR=-99
    dPhi_p1p3_SR=-99
    dPhi_p2p3_SR=-99
    dEta_p1p2_SR=-99
    dEta_p1p3_SR=-99
    dEta_p2p3_SR=-99
    M_p1p2=-99
    M_p1p3=-99
    M_p2p3=-99
    Maaa=-99
    Ptaaa=-99
    Etaaaa=-99
    Phiaaa=-99

    photon1_p4=TLorentzVector()
    photon2_p4=TLorentzVector()
    photon3_p4=TLorentzVector()
    
    total_photons = len(GoodPhoton_id)+len(FakePhoton_id)
    
    # Sideband region: 1 photon
    if total_photons==1:
      SB_region=1
      if len(GoodPhoton_id)==1:
        pho1_pt_SB=photons[GoodPhoton_id[0]].pt
        pho1_eta_SB=photons[GoodPhoton_id[0]].eta
        pho1_phi_SB=photons[GoodPhoton_id[0]].phi
      else:
        pho1_pt_SB=photons[FakePhoton_id[0]].pt
        pho1_eta_SB=photons[FakePhoton_id[0]].eta
        pho1_phi_SB=photons[FakePhoton_id[0]].phi
      photon1_p4.SetPtEtaPhiM(pho1_pt_SB,pho1_eta_SB,pho1_phi_SB,0)

    # Sideband region: 2 photons
    elif total_photons==2:
      SB_region=2
      # Sort photons by pt (leading, sub-leading) - following ATLAS triphoton analysis methodology
      all_photon_ids_2 = GoodPhoton_id + FakePhoton_id
      all_photon_ids_2.sort(key=lambda idx: photons[idx].pt, reverse=True)
      p1_id_2 = all_photon_ids_2[0]  # Leading photon
      p2_id_2 = all_photon_ids_2[1]  # Sub-leading photon
      photon1_p4.SetPtEtaPhiM(photons[p1_id_2].pt,photons[p1_id_2].eta,photons[p1_id_2].phi,0)
      photon2_p4.SetPtEtaPhiM(photons[p2_id_2].pt,photons[p2_id_2].eta,photons[p2_id_2].phi,0)

      pho1_pt_SB=photon1_p4.Pt()
      pho1_eta_SB=photon1_p4.Eta()
      pho1_phi_SB=photon1_p4.Phi()
      pho2_pt_SB=photon2_p4.Pt()
      pho2_eta_SB=photon2_p4.Eta()
      pho2_phi_SB=photon2_p4.Phi()
      dR_p1p2_SB=photon1_p4.DeltaR(photon2_p4)
      Maa_SB=(photon1_p4+photon2_p4).M()

    # Signal region: 3 or more photons
    elif total_photons>=3:
      SR_region=1
      # Get three photon indices sorted by transverse momentum (pt) - following ATLAS triphoton analysis methodology
      all_photon_ids = GoodPhoton_id + FakePhoton_id
      # Sort by pt in descending order (leading, sub-leading, third-leading)
      all_photon_ids.sort(key=lambda idx: photons[idx].pt, reverse=True)
      p1_id = all_photon_ids[0]  # Leading photon (highest pt)
      p2_id = all_photon_ids[1]  # Sub-leading photon
      p3_id = all_photon_ids[2]  # Third-leading photon
      
      photon1_p4.SetPtEtaPhiM(photons[p1_id].pt,photons[p1_id].eta,photons[p1_id].phi,0)
      photon2_p4.SetPtEtaPhiM(photons[p2_id].pt,photons[p2_id].eta,photons[p2_id].phi,0)
      photon3_p4.SetPtEtaPhiM(photons[p3_id].pt,photons[p3_id].eta,photons[p3_id].phi,0)

      # Compute fake_flag using binary encoding: bit0=p3, bit1=p2, bit2=p1
      # 0 if photon is good, 1 if photon is fake
      fake_flag = 0
      if p1_id in FakePhoton_id:
        fake_flag += 4  # bit 2
      if p2_id in FakePhoton_id:
        fake_flag += 2  # bit 1
      if p3_id in FakePhoton_id:
        fake_flag += 1  # bit 0

      pho1_pt_SR=photon1_p4.Pt()
      pho1_eta_SR=photon1_p4.Eta()
      pho1_phi_SR=photon1_p4.Phi()
      pho2_pt_SR=photon2_p4.Pt()
      pho2_eta_SR=photon2_p4.Eta()
      pho2_phi_SR=photon2_p4.Phi()
      pho3_pt_SR=photon3_p4.Pt()
      pho3_eta_SR=photon3_p4.Eta()
      pho3_phi_SR=photon3_p4.Phi()
      
      dR_p1p2_SR=photon1_p4.DeltaR(photon2_p4)
      dR_p1p3_SR=photon1_p4.DeltaR(photon3_p4)
      dR_p2p3_SR=photon2_p4.DeltaR(photon3_p4)
      dPhi_p1p2_SR=photon1_p4.DeltaPhi(photon2_p4)
      dPhi_p1p3_SR=photon1_p4.DeltaPhi(photon3_p4)
      dPhi_p2p3_SR=photon2_p4.DeltaPhi(photon3_p4)
      dEta_p1p2_SR=abs(pho1_eta_SR - pho2_eta_SR)
      dEta_p1p3_SR=abs(pho1_eta_SR - pho3_eta_SR)
      dEta_p2p3_SR=abs(pho2_eta_SR - pho3_eta_SR)
      
      M_p1p2=(photon1_p4+photon2_p4).M()
      M_p1p3=(photon1_p4+photon3_p4).M()
      M_p2p3=(photon2_p4+photon3_p4).M()
      Maaa=(photon1_p4+photon2_p4+photon3_p4).M()
      Ptaaa=(photon1_p4+photon2_p4+photon3_p4).Pt()
      Etaaaa=(photon1_p4+photon2_p4+photon3_p4).Eta()
      Phiaaa=(photon1_p4+photon2_p4+photon3_p4).Phi()

    # Fill sideband branches
    self.out.fillBranch("pho1_pt_SB",pho1_pt_SB)
    self.out.fillBranch("pho1_eta_SB",pho1_eta_SB)
    self.out.fillBranch("pho1_phi_SB",pho1_phi_SB)
    self.out.fillBranch("pho2_pt_SB",pho2_pt_SB)
    self.out.fillBranch("pho2_eta_SB",pho2_eta_SB)
    self.out.fillBranch("pho2_phi_SB",pho2_phi_SB)
    self.out.fillBranch("dR_p1p2_SB",dR_p1p2_SB)
    self.out.fillBranch("Maa_SB",Maa_SB)
    # Fill signal region branches
    self.out.fillBranch("pho1_pt_SR",pho1_pt_SR)
    self.out.fillBranch("pho1_eta_SR",pho1_eta_SR)
    self.out.fillBranch("pho1_phi_SR",pho1_phi_SR)
    self.out.fillBranch("pho2_pt_SR",pho2_pt_SR)
    self.out.fillBranch("pho2_eta_SR",pho2_eta_SR)
    self.out.fillBranch("pho2_phi_SR",pho2_phi_SR)
    self.out.fillBranch("pho3_pt_SR",pho3_pt_SR)
    self.out.fillBranch("pho3_eta_SR",pho3_eta_SR)
    self.out.fillBranch("pho3_phi_SR",pho3_phi_SR)
    self.out.fillBranch("dR_p1p2_SR",dR_p1p2_SR)
    self.out.fillBranch("dR_p1p3_SR",dR_p1p3_SR)
    self.out.fillBranch("dR_p2p3_SR",dR_p2p3_SR)
    self.out.fillBranch("dPhi_p1p2_SR",dPhi_p1p2_SR)
    self.out.fillBranch("dPhi_p1p3_SR",dPhi_p1p3_SR)
    self.out.fillBranch("dPhi_p2p3_SR",dPhi_p2p3_SR)
    self.out.fillBranch("dEta_p1p2_SR",dEta_p1p2_SR)
    self.out.fillBranch("dEta_p1p3_SR",dEta_p1p3_SR)
    self.out.fillBranch("dEta_p2p3_SR",dEta_p2p3_SR)
    self.out.fillBranch("M_p1p2",M_p1p2)
    self.out.fillBranch("M_p1p3",M_p1p3)
    self.out.fillBranch("M_p2p3",M_p2p3)
    self.out.fillBranch("Maaa",Maaa)
    self.out.fillBranch("Ptaaa",Ptaaa)
    self.out.fillBranch("Etaaaa",Etaaaa)
    self.out.fillBranch("Phiaaa",Phiaaa)
    self.out.fillBranch("SB_region",SB_region)
    self.out.fillBranch("SR_region",SR_region)
    self.out.fillBranch("fake_flag",fake_flag)

    return True

TriPhoton2016apv = lambda: TriPhotonProducer("2016apv")
TriPhoton2016 = lambda: TriPhotonProducer("2016")
TriPhoton2017 = lambda: TriPhotonProducer("2017")
TriPhoton2018 = lambda: TriPhotonProducer("2018")
TriPhoton2022 = lambda: TriPhotonProducer("2022")
TriPhoton2022EE = lambda: TriPhotonProducer("2022EE")
