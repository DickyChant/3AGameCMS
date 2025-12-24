#!/usr/bin/env python3
import os
import sys
import optparse
import ROOT
import re
import glob

from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.modules.common.countHistogramsModule import *
from PhysicsTools.NanoAODTools.postprocessing.analysis.modules.PhoIDSFProducer import *
from PhysicsTools.NanoAODTools.postprocessing.analysis.modules.TriPhotonProducer import *
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun2 import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.puWeightProducer import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.PrefireCorr import *
from PhysicsTools.NanoAODTools.postprocessing.framework.crabhelper import inputFiles, runsAndLumis
from PhysicsTools.NanoAODTools.postprocessing.analysis.modules.PUWeightRun3 import PUWeight2022, PUWeight2022EE
try:
    from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun3 import createJMECorrector
    HAS_RUN3_JME = True
except ImportError:
    HAS_RUN3_JME = False
    createJMECorrector = None
    print("[localrun] jetmetHelperRun3 not found; 2022/2022EE will run without JME corrections.")
### main python file to run ###

def main():

  usage = 'usage: %prog [options]'
  parser = optparse.OptionParser(usage)
  parser.add_option('--year', dest='year', help='which year sample (2016a, 2016b, 2017, 2018, 2022, 2022EE)', default='2018', type='string')
  parser.add_option('-m', dest='ismc', help='to apply sf correction or not', default=True, action='store_true')
  parser.add_option('-d', dest='ismc', help='to apply sf correction or not', action='store_false')
  parser.add_option('-n','--nEve', dest='nEvent', help='number of event', type='int', action='store')
  parser.add_option('-i', '--in', dest='inputs', help='input file, directory, or glob (e.g. /path/*.root)', default=None, type='string')
  parser.add_option('-o', '--out', dest='output', help='output directory with files', default=None, type='string')
  (opt, args) = parser.parse_args()

  # Expand input to a list of files
  input_files = []
  if opt.inputs:
    if os.path.isdir(opt.inputs):
      input_files = sorted(glob.glob(os.path.join(opt.inputs, "*.root")))
    else:
      globbed = sorted(glob.glob(opt.inputs))
      input_files = globbed if len(globbed) > 0 else [opt.inputs]
  if len(input_files) == 0:
    raise RuntimeError("No input files found for pattern/path: %s" % opt.inputs)

  def maybe_jme_2022(is_mc, era):
    """
    Return Run3 JME corrector module if available, otherwise None.
    era: "CD" (preEE) or "EFG" (postEE)
    """
    if not HAS_RUN3_JME:
      return None
    corrector = createJMECorrector(
      isMC=is_mc,
      dataYear="2022" if era == "CD" else "2022EE",
      runPeriod=era,
      applySmearing=is_mc,
      jetType="AK4PFchs"
    )
    return corrector()

  if opt.ismc:
    if opt.year == "2016a":
      p = PostProcessor(opt.output, input_files, modules=[countHistogramsModule(),puWeight_2016_preAPV(),PhoIDSF2016apv(),jmeCorrections_UL2016APVMC(), TriPhoton2016apv()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2016b":
      p = PostProcessor(opt.output, input_files, modules=[countHistogramsModule(),puWeight_2016_postAPV(),PhoIDSF2016(),jmeCorrections_UL2016MC(),TriPhoton2016()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2017":
      p = PostProcessor(opt.output, input_files, modules=[countHistogramsModule(),puWeight_2017(),PhoIDSF2017(),jmeCorrections_UL2017MC(),TriPhoton2017()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2018":
      p = PostProcessor(opt.output, input_files, modules=[countHistogramsModule(),puWeight_2018(),PhoIDSF2018(),jmeCorrections_UL2018MC(),TriPhoton2018()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2022":
      mods = [countHistogramsModule(), PUWeight2022(), PhoIDSF2022(), TriPhotonProducer("2022")]
      jme_mod = maybe_jme_2022(is_mc=True, era="CD")
      if jme_mod is not None:
        mods.insert(-1, jme_mod)
      p = PostProcessor(opt.output, input_files, modules=mods, provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2022EE":
      mods = [countHistogramsModule(), PUWeight2022EE(), PhoIDSF2022EE(), TriPhotonProducer("2022EE")]
      jme_mod = maybe_jme_2022(is_mc=True, era="EFG")
      if jme_mod is not None:
        mods.insert(-1, jme_mod)
      p = PostProcessor(opt.output, input_files, modules=mods, provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)


# Sequence for data
  if not (opt.ismc):
    if opt.year == "2016b":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2016B(),TriPhoton2016apv()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2016c":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2016C(),TriPhoton2016apv()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2016d":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2016D(),TriPhoton2016apv()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2016e":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2016E(),TriPhoton2016apv()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2016f_apv":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2016APVF(),TriPhoton2016apv()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2016f":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2016F(),TriPhoton2016()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2016g":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2016G(),TriPhoton2016()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2016h":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2016H(),TriPhoton2016()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2017b":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2017B(),TriPhoton2017()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2017c":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2017C(),TriPhoton2017()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2017d":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2017D(),TriPhoton2017()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2017e":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2017E(),TriPhoton2017()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2017f":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2017F(),TriPhoton2017()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2018a":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2018A(),TriPhoton2018()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2018b":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2018B(),TriPhoton2018()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2018c":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2018C(),TriPhoton2018()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2018d":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2018D(),TriPhoton2018()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2022":
      mods = [TriPhotonProducer("2022")]
      jme_mod = maybe_jme_2022(is_mc=False, era="CD")
      if jme_mod is not None:
        mods.insert(0, jme_mod)
      p = PostProcessor(opt.output, input_files, modules=mods, provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2022EE":
      mods = [TriPhotonProducer("2022EE")]
      jme_mod = maybe_jme_2022(is_mc=False, era="EFG")
      if jme_mod is not None:
        mods.insert(0, jme_mod)
      p = PostProcessor(opt.output, input_files, modules=mods, provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
  p.run()

if __name__ == "__main__":
    sys.exit(main())
