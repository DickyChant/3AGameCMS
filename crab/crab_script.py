#!/usr/bin/env python3
import os
import sys
import optparse
import ROOT
import re

from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.modules.common.countHistogramsModule import *
from PhysicsTools.NanoAODTools.postprocessing.analysis.modules.PhoIDSFProducer import *
from PhysicsTools.NanoAODTools.postprocessing.analysis.modules.TriPhotonProducer import *
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun2 import *
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun3 import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.puWeightProducer import *
from PhysicsTools.NanoAODTools.postprocessing.analysis.modules.PUWeightRun2 import *
from PhysicsTools.NanoAODTools.postprocessing.analysis.modules.PUWeightRun3 import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.PrefireCorr import *
from PhysicsTools.NanoAODTools.postprocessing.framework.crabhelper import inputFiles, runsAndLumis
### main python file to run ###

def main():

  usage = 'usage: %prog [options]'
  parser = optparse.OptionParser(usage)
  parser.add_option('--year', dest='year', help='which year sample', default='2018', type='string')
  parser.add_option('--era', dest='era', help='data era (C, D, E, F, G, etc.)', default=None, type='string')
  parser.add_option('-m', dest='ismc', help='to apply sf correction or not', default=True, action='store_true')
  parser.add_option('-d', dest='ismc', help='to apply sf correction or not', action='store_false')
  (opt, args) = parser.parse_args()

  if opt.ismc:
    if opt.year == "2016a":
      p = PostProcessor(".", inputFiles(), modules=[countHistogramsModule(),puWeight_2016_preAPV(),PhoIDSF2016apv(),jmeCorrections_UL2016APVMC(), TriPhoton2016apv()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2016b":
      p = PostProcessor(".", inputFiles(), modules=[countHistogramsModule(),puWeight_2016_postAPV(),PhoIDSF2016(),jmeCorrections_UL2016MC(),TriPhoton2016()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2017":
      # Run2 UL 2017: use CVMFS-based PUWeightRun2
      p = PostProcessor(".", inputFiles(), modules=[countHistogramsModule(),PUWeight2017(),PhoIDSF2017(),jmeCorrections_UL2017MC(),TriPhoton2017()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2018":
      # Run2 UL 2018: use CVMFS-based PUWeightRun2
      p = PostProcessor(".", inputFiles(), modules=[countHistogramsModule(),PUWeight2018(),PhoIDSF2018(),jmeCorrections_UL2018MC(),TriPhoton2018()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2022":
      # Run3 2022: use PUWeightRun3, no JME for now, no prefire
      jme_mod = createJMECorrector(isMC=True, dataYear="2022", runPeriod="CD")
      modules = [countHistogramsModule(), PUWeightRun3("2022"), PhoIDSF2022(), TriPhoton2022()]
      if jme_mod is not None:
        modules.insert(3, jme_mod)
      p = PostProcessor(".", inputFiles(), modules=modules, provenance=True, fwkJobReport=True, jsonInput=runsAndLumis(), outputbranchsel="keep_and_drop.txt")
    if opt.year == "2022EE":
      # Run3 2022EE: use PUWeightRun3, no JME for now, no prefire
      jme_mod = createJMECorrector(isMC=True, dataYear="2022EE", runPeriod="EFG")
      modules = [countHistogramsModule(), PUWeightRun3("2022EE"), PhoIDSF2022EE(), TriPhoton2022EE()]
      if jme_mod is not None:
        modules.insert(3, jme_mod)
      p = PostProcessor(".", inputFiles(), modules=modules, provenance=True, fwkJobReport=True, jsonInput=runsAndLumis(), outputbranchsel="keep_and_drop.txt")


# Sequence for data
  if not (opt.ismc):
    if opt.year == "2016b":
      p = PostProcessor(".", inputFiles(), modules=[jmeCorrections_UL2016B(),TriPhoton2016apv()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2016c":
      p = PostProcessor(".", inputFiles(), modules=[jmeCorrections_UL2016C(),TriPhoton2016apv()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2016d":
      p = PostProcessor(".", inputFiles(), modules=[jmeCorrections_UL2016D(),TriPhoton2016apv()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2016e":
      p = PostProcessor(".", inputFiles(), modules=[jmeCorrections_UL2016E(),TriPhoton2016apv()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2016f_apv":
      p = PostProcessor(".", inputFiles(), modules=[jmeCorrections_UL2016APVF(),TriPhoton2016apv()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2016f":
      p = PostProcessor(".", inputFiles(), modules=[jmeCorrections_UL2016F(),TriPhoton2016()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2016g":
      p = PostProcessor(".", inputFiles(), modules=[jmeCorrections_UL2016G(),TriPhoton2016()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2016h":
      p = PostProcessor(".", inputFiles(), modules=[jmeCorrections_UL2016H(),TriPhoton2016()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2017b":
      p = PostProcessor(".", inputFiles(), modules=[jmeCorrections_UL2017B(),TriPhoton2017()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2017c":
      p = PostProcessor(".", inputFiles(), modules=[jmeCorrections_UL2017C(),TriPhoton2017()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2017d":
      p = PostProcessor(".", inputFiles(), modules=[jmeCorrections_UL2017D(),TriPhoton2017()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2017e":
      p = PostProcessor(".", inputFiles(), modules=[jmeCorrections_UL2017E(),TriPhoton2017()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2017f":
      p = PostProcessor(".", inputFiles(), modules=[jmeCorrections_UL2017F(),TriPhoton2017()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2018a":
      p = PostProcessor(".", inputFiles(), modules=[jmeCorrections_UL2018A(),TriPhoton2018()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2018b":
      p = PostProcessor(".", inputFiles(), modules=[jmeCorrections_UL2018B(),TriPhoton2018()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2018c":
      p = PostProcessor(".", inputFiles(), modules=[jmeCorrections_UL2018C(),TriPhoton2018()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    if opt.year == "2018d":
      p = PostProcessor(".", inputFiles(), modules=[jmeCorrections_UL2018D(),TriPhoton2018()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt")
    # Run3 2022 data
    if opt.year == "2022" and opt.era:
      era_map = {"C": "2022C", "D": "2022D"}
      year_era = era_map.get(opt.era, "2022")
      jme_mod = createJMECorrector(isMC=False, dataYear="2022", runPeriod=opt.era)
      modules = [TriPhoton2022()]
      if jme_mod is not None:
        modules.insert(0, jme_mod)
      p = PostProcessor(".", inputFiles(), modules=modules, provenance=True, fwkJobReport=True, jsonInput=runsAndLumis(), outputbranchsel="keep_and_drop.txt")
    # Run3 2022EE data
    if opt.year == "2022EE" and opt.era:
      era_map = {"E": "2022E", "F": "2022F", "G": "2022G"}
      year_era = era_map.get(opt.era, "2022EE")
      jme_mod = createJMECorrector(isMC=False, dataYear="2022EE", runPeriod=opt.era)
      modules = [TriPhoton2022EE()]
      if jme_mod is not None:
        modules.insert(0, jme_mod)
      p = PostProcessor(".", inputFiles(), modules=modules, provenance=True, fwkJobReport=True, jsonInput=runsAndLumis(), outputbranchsel="keep_and_drop.txt")
  p.run()

if __name__ == "__main__":
    sys.exit(main())
