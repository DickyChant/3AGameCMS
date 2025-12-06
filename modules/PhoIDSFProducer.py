import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection 
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

import math
import os

class PhoIDSFProducer(Module):
  def __init__( self , year ):
    self.year = year
    self.pixel_veto = "Pho_PV.root"
    self.id_medium = "Pho_Medium.root"
    self.id_tight = "Pho_Tight.root"
    self.SF_location_path = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/analysis/data/year%s/" %(os.environ['CMSSW_BASE'], self.year)
    print('SF location:', self.SF_location_path)

  def beginJob(self):
    print('begin to set Photon ID SF --->>>')
    print('start to open SF root file --->>>')
    # init the TH2F
    self.pixel_veto_med_dir= ROOT.TDirectoryFile()
    self.pixel_veto_tig_dir= ROOT.TDirectoryFile()
    self.pixel_veto_med_th1f= ROOT.TH1F()
    self.pixel_veto_tig_th1f= ROOT.TH1F()
    self.id_medium_th2f= ROOT.TH2F()
    self.id_tight_th2f= ROOT.TH2F()
    #Open the SF root file
    self.file_pixel_veto= ROOT.TFile.Open(self.SF_location_path+self.pixel_veto)
    self.file_id_medium= ROOT.TFile.Open(self.SF_location_path+self.id_medium)
    self.file_id_tight= ROOT.TFile.Open(self.SF_location_path+self.id_tight)
    #access to the TH2F
    self.file_pixel_veto.GetObject('MediumID', self.pixel_veto_med_dir)
    self.file_pixel_veto.GetObject('TightID', self.pixel_veto_tig_dir)
    self.pixel_veto_med_dir.GetObject('SF_HasPix_MediumID', self.pixel_veto_med_th1f)
    self.pixel_veto_tig_dir.GetObject('SF_HasPix_TightID', self.pixel_veto_tig_th1f)
    self.file_id_medium.GetObject('EGamma_SF2D', self.id_medium_th2f)
    self.file_id_tight.GetObject('EGamma_SF2D', self.id_tight_th2f)
    print('open SF files successfully --->>>')

  def endJob(self):
    print('close SF root file --->>>')
    self.file_pixel_veto.Close()
    self.file_id_medium.Close()
    self.file_id_tight.Close()
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
      if photons[ipho].pt < 500: 
        Photon_CutBased_MediumID_SF.append(self.id_medium_th2f.GetBinContent(self.id_medium_th2f.FindBin(photons[ipho].eta, photons[ipho].pt)))
        Photon_CutBased_MediumID_SFerr.append(self.id_medium_th2f.GetBinError(self.id_medium_th2f.FindBin(photons[ipho].eta, photons[ipho].pt)))
        Photon_CutBased_TightID_SF.append(self.id_tight_th2f.GetBinContent(self.id_tight_th2f.FindBin(photons[ipho].eta, photons[ipho].pt)))
        Photon_CutBased_TightID_SFerr.append(self.id_tight_th2f.GetBinError(self.id_tight_th2f.FindBin(photons[ipho].eta, photons[ipho].pt)))
        if abs(photons[ipho].eta)<1.566:
          Photon_PixelVeto_MediumID_Inc_SF.append(self.pixel_veto_med_th1f.GetBinContent(1))
          Photon_PixelVeto_MediumID_Inc_SFerr.append(self.pixel_veto_med_th1f.GetBinError(1))
          Photon_PixelVeto_TightID_Inc_SF.append(self.pixel_veto_tig_th1f.GetBinContent(1))
          Photon_PixelVeto_TightID_Inc_SFerr.append(self.pixel_veto_tig_th1f.GetBinError(1))
          if photons[ipho].r9>0.96:
            Photon_PixelVeto_MediumID_high_SF.append(self.pixel_veto_med_th1f.GetBinContent(2))
            Photon_PixelVeto_MediumID_high_SFerr.append(self.pixel_veto_med_th1f.GetBinError(2))
            Photon_PixelVeto_TightID_high_SF.append(self.pixel_veto_tig_th1f.GetBinContent(2))
            Photon_PixelVeto_TightID_high_SFerr.append(self.pixel_veto_tig_th1f.GetBinError(2))
          else:
            Photon_PixelVeto_MediumID_high_SF.append(self.pixel_veto_med_th1f.GetBinContent(3))
            Photon_PixelVeto_MediumID_high_SFerr.append(self.pixel_veto_med_th1f.GetBinError(3))
            Photon_PixelVeto_TightID_high_SF.append(self.pixel_veto_tig_th1f.GetBinContent(3))
            Photon_PixelVeto_TightID_high_SFerr.append(self.pixel_veto_tig_th1f.GetBinError(3))
        else:
          Photon_PixelVeto_MediumID_Inc_SF.append(self.pixel_veto_med_th1f.GetBinContent(4))
          Photon_PixelVeto_MediumID_Inc_SFerr.append(self.pixel_veto_med_th1f.GetBinError(4))
          Photon_PixelVeto_TightID_Inc_SF.append(self.pixel_veto_tig_th1f.GetBinContent(4))
          Photon_PixelVeto_TightID_Inc_SFerr.append(self.pixel_veto_tig_th1f.GetBinError(4))
          if photons[ipho].r9>0.96:
            Photon_PixelVeto_MediumID_high_SF.append(self.pixel_veto_med_th1f.GetBinContent(5))
            Photon_PixelVeto_MediumID_high_SFerr.append(self.pixel_veto_med_th1f.GetBinError(5))
            Photon_PixelVeto_TightID_high_SF.append(self.pixel_veto_tig_th1f.GetBinContent(5))
            Photon_PixelVeto_TightID_high_SFerr.append(self.pixel_veto_tig_th1f.GetBinError(5))
          else:
            Photon_PixelVeto_MediumID_high_SF.append(self.pixel_veto_med_th1f.GetBinContent(6))
            Photon_PixelVeto_MediumID_high_SFerr.append(self.pixel_veto_med_th1f.GetBinError(6))
            Photon_PixelVeto_TightID_high_SF.append(self.pixel_veto_tig_th1f.GetBinContent(6))
            Photon_PixelVeto_TightID_high_SFerr.append(self.pixel_veto_tig_th1f.GetBinError(6))

      else: 
        Photon_CutBased_MediumID_SF.append(self.id_medium_th2f.GetBinContent(self.id_medium_th2f.FindBin(photons[ipho].eta, 499)))
        Photon_CutBased_MediumID_SFerr.append(self.id_medium_th2f.GetBinError(self.id_medium_th2f.FindBin(photons[ipho].eta, 499)))
        Photon_CutBased_TightID_SF.append(self.id_tight_th2f.GetBinContent(self.id_tight_th2f.FindBin(photons[ipho].eta, 499)))
        Photon_CutBased_TightID_SFerr.append(self.id_tight_th2f.GetBinError(self.id_tight_th2f.FindBin(photons[ipho].eta, 499)))
        if abs(photons[ipho].eta)<1.566:
          Photon_PixelVeto_MediumID_Inc_SF.append(self.pixel_veto_med_th1f.GetBinContent(1))
          Photon_PixelVeto_MediumID_Inc_SFerr.append(self.pixel_veto_med_th1f.GetBinError(1))
          Photon_PixelVeto_TightID_Inc_SF.append(self.pixel_veto_tig_th1f.GetBinContent(1))
          Photon_PixelVeto_TightID_Inc_SFerr.append(self.pixel_veto_tig_th1f.GetBinError(1))
          if photons[ipho].r9>0.96:
            Photon_PixelVeto_MediumID_high_SF.append(self.pixel_veto_med_th1f.GetBinContent(2))
            Photon_PixelVeto_MediumID_high_SFerr.append(self.pixel_veto_med_th1f.GetBinError(2))
            Photon_PixelVeto_TightID_high_SF.append(self.pixel_veto_tig_th1f.GetBinContent(2))
            Photon_PixelVeto_TightID_high_SFerr.append(self.pixel_veto_tig_th1f.GetBinError(2))
          else:
            Photon_PixelVeto_MediumID_high_SF.append(self.pixel_veto_med_th1f.GetBinContent(3))
            Photon_PixelVeto_MediumID_high_SFerr.append(self.pixel_veto_med_th1f.GetBinError(3))
            Photon_PixelVeto_TightID_high_SF.append(self.pixel_veto_tig_th1f.GetBinContent(3))
            Photon_PixelVeto_TightID_high_SFerr.append(self.pixel_veto_tig_th1f.GetBinError(3))
        else:
          Photon_PixelVeto_MediumID_Inc_SF.append(self.pixel_veto_med_th1f.GetBinContent(4))
          Photon_PixelVeto_MediumID_Inc_SFerr.append(self.pixel_veto_med_th1f.GetBinError(4))
          Photon_PixelVeto_TightID_Inc_SF.append(self.pixel_veto_tig_th1f.GetBinContent(4))
          Photon_PixelVeto_TightID_Inc_SFerr.append(self.pixel_veto_tig_th1f.GetBinError(4))
          if photons[ipho].r9>0.96:
            Photon_PixelVeto_MediumID_high_SF.append(self.pixel_veto_med_th1f.GetBinContent(5))
            Photon_PixelVeto_MediumID_high_SFerr.append(self.pixel_veto_med_th1f.GetBinError(5))
            Photon_PixelVeto_TightID_high_SF.append(self.pixel_veto_tig_th1f.GetBinContent(5))
            Photon_PixelVeto_TightID_high_SFerr.append(self.pixel_veto_tig_th1f.GetBinError(5))
          else:
            Photon_PixelVeto_MediumID_high_SF.append(self.pixel_veto_med_th1f.GetBinContent(6))
            Photon_PixelVeto_MediumID_high_SFerr.append(self.pixel_veto_med_th1f.GetBinError(6))
            Photon_PixelVeto_TightID_high_SF.append(self.pixel_veto_tig_th1f.GetBinContent(6))
            Photon_PixelVeto_TightID_high_SFerr.append(self.pixel_veto_tig_th1f.GetBinError(6))

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
