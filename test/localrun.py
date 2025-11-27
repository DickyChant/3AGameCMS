import os
import sys
import optparse
import ROOT
import re

from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.modules.common.countHistogramsModule import *
from PhysicsTools.NanoAODTools.postprocessing.analysis.modules.PhoIDSFProducer import *
from PhysicsTools.NanoAODTools.postprocessing.analysis.modules.EWAAProducer import *
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun2 import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.puWeightProducer import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.PrefireCorr import *
from PhysicsTools.NanoAODTools.postprocessing.framework.crabhelper import inputFiles, runsAndLumis
### main python file to run ###

def main():

  usage = 'usage: %prog [options]'
  parser = optparse.OptionParser(usage)
  parser.add_option('--year', dest='year', help='which year sample', default='2018', type='string')
  parser.add_option('-m', dest='ismc', help='to apply sf correction or not', default=True, action='store_true')
  parser.add_option('-d', dest='ismc', help='to apply sf correction or not', action='store_false')
  parser.add_option('-n','--nEve', dest='nEvent', help='number of event', type='int', action='store')
  parser.add_option('-i', '--in', dest='inputs', help='input directory with files', default=None, type='string')
  parser.add_option('-o', '--out', dest='output', help='output directory with files', default=None, type='string')
  (opt, args) = parser.parse_args()

  if opt.ismc:
    if opt.year == "2016a":
      p = PostProcessor(opt.output, [opt.inputs], modules=[countHistogramsModule(),puWeight_2016_preAPV(),PhoIDSF2016apv(),jmeCorrections_UL2016APVMC(), EWAAA2016apv()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2016b":
      p = PostProcessor(opt.output, [opt.inputs], modules=[countHistogramsModule(),puWeight_2016_postAPV(),PhoIDSF2016(),jmeCorrections_UL2016MC(),EWAAA2016()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2017":
      p = PostProcessor(opt.output, [opt.inputs], modules=[countHistogramsModule(),puWeight_2017(),PhoIDSF2017(),jmeCorrections_UL2017MC(),EWAAA2017()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2018":
      p = PostProcessor(opt.output, [opt.inputs], modules=[countHistogramsModule(),puWeight_2018(),PhoIDSF2018(),jmeCorrections_UL2018MC(),EWAAA2018()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)


# Sequence for data
  if not (opt.ismc):
    if opt.year == "2016b":
      p = PostProcessor(opt.output, [opt.inputs], modules=[jmeCorrections_UL2016B(),EWAAA2016apv()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2016c":
      p = PostProcessor(opt.output, [opt.inputs], modules=[jmeCorrections_UL2016C(),EWAAA2016apv()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2016d":
      p = PostProcessor(opt.output, [opt.inputs], modules=[jmeCorrections_UL2016D(),EWAAA2016apv()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2016e":
      p = PostProcessor(opt.output, [opt.inputs], modules=[jmeCorrections_UL2016E(),EWAAA2016apv()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2016f_apv":
      p = PostProcessor(opt.output, [opt.inputs], modules=[jmeCorrections_UL2016APVF(),EWAAA2016apv()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2016f":
      p = PostProcessor(opt.output, [opt.inputs], modules=[jmeCorrections_UL2016F(),EWAAA2016()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2016g":
      p = PostProcessor(opt.output, [opt.inputs], modules=[jmeCorrections_UL2016G(),EWAAA2016()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2016h":
      p = PostProcessor(opt.output, [opt.inputs], modules=[jmeCorrections_UL2016H(),EWAAA2016()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2017b":
      p = PostProcessor(opt.output, [opt.inputs], modules=[jmeCorrections_UL2017B(),EWAAA2017()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2017c":
      p = PostProcessor(opt.output, [opt.inputs], modules=[jmeCorrections_UL2017C(),EWAAA2017()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2017d":
      p = PostProcessor(opt.output, [opt.inputs], modules=[jmeCorrections_UL2017D(),EWAAA2017()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2017e":
      p = PostProcessor(opt.output, [opt.inputs], modules=[jmeCorrections_UL2017E(),EWAAA2017()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2017f":
      p = PostProcessor(opt.output, [opt.inputs], modules=[jmeCorrections_UL2017F(),EWAAA2017()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2018a":
      p = PostProcessor(opt.output, [opt.inputs], modules=[jmeCorrections_UL2018A(),EWAAA2018()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2018b":
      p = PostProcessor(opt.output, [opt.inputs], modules=[jmeCorrections_UL2018B(),EWAAA2018()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2018c":
      p = PostProcessor(opt.output, [opt.inputs], modules=[jmeCorrections_UL2018C(),EWAAA2018()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
    if opt.year == "2018d":
      p = PostProcessor(opt.output, [opt.inputs], modules=[jmeCorrections_UL2018D(),EWAAA2018()], provenance=True,fwkJobReport=True, jsonInput=runsAndLumis(),outputbranchsel="keep_and_drop.txt",maxEntries=opt.nEvent)
  p.run()

if __name__ == "__main__":
    sys.exit(main())
