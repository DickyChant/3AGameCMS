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
from PhysicsTools.NanoAODTools.postprocessing.modules.common.puWeightProducer import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.PrefireCorr import *
from PhysicsTools.NanoAODTools.postprocessing.framework.crabhelper import inputFiles, runsAndLumis
from PhysicsTools.NanoAODTools.postprocessing.analysis.modules.PUWeightRun2 import PUWeight2016apv, PUWeight2016, PUWeight2017, PUWeight2018
from PhysicsTools.NanoAODTools.postprocessing.analysis.modules.PUWeightRun3 import PUWeight2022, PUWeight2022EE
from PhysicsTools.NanoAODTools.postprocessing.analysis.modules.JMECorrectionsCVMFS import JMECorrections2016apv, JMECorrections2016, JMECorrections2017, JMECorrections2018
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
  parser.add_option('-i', '--in', dest='inputs', help='input file, directory, or glob (e.g. /path/*.root)', default=[], action='append', type='string')
  parser.add_option('-o', '--out', dest='output', help='output directory with files', default=None, type='string')
  parser.add_option('--keep-and-drop', dest='keep_and_drop', help='path to keep_and_drop.txt file (default: auto-detect from script location)', default=None, type='string')
  parser.add_option('--postfix', dest='postfix', help='postfix for output files (e.g., _Skim)', default=None, type='string')
  parser.add_option('--hadd-output', dest='hadd_output', help='if multiple inputs, merge them into this output file', default=None, type='string')
  (opt, args) = parser.parse_args()

  # Find keep_and_drop.txt - use provided path or auto-detect
  if opt.keep_and_drop:
    keep_and_drop = opt.keep_and_drop
    if not os.path.exists(keep_and_drop):
      raise RuntimeError(f"Specified keep_and_drop file not found: {keep_and_drop}")
  else:
    # Auto-detect: look in script directory, then analysis root
    script_dir = os.path.dirname(os.path.realpath(__file__))
    keep_and_drop = os.path.join(script_dir, "keep_and_drop.txt")
    if not os.path.exists(keep_and_drop):
      analysis_root = os.path.dirname(os.path.dirname(script_dir))
      keep_and_drop = os.path.join(analysis_root, "keep_and_drop.txt")
    if not os.path.exists(keep_and_drop):
      raise RuntimeError(f"Cannot find keep_and_drop.txt. Looked in {script_dir} and {analysis_root}. Use --keep-and-drop to specify path.")

  # Expand input to a list of files
  # opt.inputs is now a list (can have multiple -i arguments)
  input_files = []
  if opt.inputs:
    for input_pattern in opt.inputs:
      if os.path.isdir(input_pattern):
        input_files.extend(sorted(glob.glob(os.path.join(input_pattern, "*.root"))))
      else:
        globbed = sorted(glob.glob(input_pattern))
        input_files.extend(globbed if len(globbed) > 0 else [input_pattern])
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
    # corrector might be None if JME not implemented yet for Run3
    return corrector() if corrector is not None else None

  if opt.ismc:
    if opt.year == "2016a":
      p = PostProcessor(opt.output, input_files, modules=[countHistogramsModule(),PUWeight2016apv(),PhoIDSF2016apv(),JMECorrections2016apv(is_mc=True),TriPhoton2016apv()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2016b":
      p = PostProcessor(opt.output, input_files, modules=[countHistogramsModule(),PUWeight2016(),PhoIDSF2016(),JMECorrections2016(is_mc=True),TriPhoton2016()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2017":
      p = PostProcessor(opt.output, input_files, modules=[countHistogramsModule(),PUWeight2017(),PhoIDSF2017(),JMECorrections2017(is_mc=True),TriPhoton2017()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2018":
      p = PostProcessor(opt.output, input_files, modules=[countHistogramsModule(),PUWeight2018(),PhoIDSF2018(),JMECorrections2018(is_mc=True),TriPhoton2018()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2022":
      mods = [countHistogramsModule(), PUWeight2022(), PhoIDSF2022(), TriPhoton2022()]
      jme_mod = maybe_jme_2022(is_mc=True, era="CD")
      if jme_mod is not None:
        mods.insert(-1, jme_mod)
      p = PostProcessor(opt.output, input_files, modules=mods, provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent,haddFileName=opt.hadd_output)
    if opt.year == "2022EE":
      mods = [countHistogramsModule(), PUWeight2022EE(), PhoIDSF2022EE(), TriPhoton2022EE()]
      jme_mod = maybe_jme_2022(is_mc=True, era="EFG")
      if jme_mod is not None:
        mods.insert(-1, jme_mod)
      p = PostProcessor(opt.output, input_files, modules=mods, provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent,haddFileName=opt.hadd_output)


# Sequence for data
  if not (opt.ismc):
    if opt.year == "2016b":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2016B(),TriPhoton2016apv()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2016c":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2016C(),TriPhoton2016apv()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2016d":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2016D(),TriPhoton2016apv()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2016e":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2016E(),TriPhoton2016apv()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2016f_apv":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2016APVF(),TriPhoton2016apv()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2016f":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2016F(),TriPhoton2016()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2016g":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2016G(),TriPhoton2016()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2016h":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2016H(),TriPhoton2016()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2017b":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2017B(),TriPhoton2017()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2017c":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2017C(),TriPhoton2017()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2017d":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2017D(),TriPhoton2017()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2017e":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2017E(),TriPhoton2017()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2017f":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2017F(),TriPhoton2017()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2018a":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2018A(),TriPhoton2018()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2018b":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2018B(),TriPhoton2018()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2018c":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2018C(),TriPhoton2018()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2018d":
      p = PostProcessor(opt.output, input_files, modules=[jmeCorrections_UL2018D(),TriPhoton2018()], provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent)
    if opt.year == "2022":
      mods = [TriPhoton2022()]
      jme_mod = maybe_jme_2022(is_mc=False, era="CD")
      if jme_mod is not None:
        mods.insert(0, jme_mod)
      p = PostProcessor(opt.output, input_files, modules=mods, provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent,haddFileName=opt.hadd_output)
    if opt.year == "2022EE":
      mods = [TriPhoton2022EE()]
      jme_mod = maybe_jme_2022(is_mc=False, era="EFG")
      if jme_mod is not None:
        mods.insert(0, jme_mod)
      p = PostProcessor(opt.output, input_files, modules=mods, provenance=True,fwkJobReport=False,postfix=opt.postfix if opt.postfix else None, jsonInput=runsAndLumis(),outputbranchsel=keep_and_drop,maxEntries=opt.nEvent,haddFileName=opt.hadd_output)
  p.run()

if __name__ == "__main__":
    sys.exit(main())
