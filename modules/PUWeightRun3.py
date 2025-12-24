import os
import correctionlib._core

from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module


class PUWeightRun3(Module):
  """
  Pileup weights for Run3 (2022/2022EE) using correctionlib JSON from CVMFS.
  Produces branches: puWeight, puWeightUp, puWeightDown.
  """
  def __init__(self, year):
    self.year = year
    # Map year to correctionlib era and CVMFS path
    year_to_era = {
      "2022": "2022preEE",
      "2022EE": "2022postEE",
    }
    self.era = year_to_era.get(year, year)
    year_to_cvmfs_path = {
      "2022": "/cvmfs/cms-griddata.cern.ch/cat/metadata/LUM/Run3-22CDSep23-Summer22-NanoAODv12/pileup.json.gz",
      "2022EE": "/cvmfs/cms-griddata.cern.ch/cat/metadata/LUM/Run3-22EFGSep23-Summer22EE-NanoAODv12/pileup.json.gz",
    }
    self.pu_path = year_to_cvmfs_path.get(year, None)
    if self.pu_path is None:
      self.pu_path = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/analysis/data/year%s/pileup.json.gz" % (os.environ["CMSSW_BASE"], self.year)

  def beginJob(self):
    if not os.path.exists(self.pu_path):
      alt = self.pu_path.replace(".json.gz", ".json")
      if os.path.exists(alt):
        self.pu_path = alt
      else:
        raise FileNotFoundError(f"PU weight file not found: {self.pu_path}")
    self.evaluator = correctionlib._core.CorrectionSet.from_file(self.pu_path)

  def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
    self.out = wrappedOutputTree
    self.out.branch("puWeight", "F")
    self.out.branch("puWeightUp", "F")
    self.out.branch("puWeightDown", "F")

  def analyze(self, event):
    ntrue = getattr(event, "Pileup_nTrueInt", None)
    if ntrue is None:
      # If branch not present (e.g. data), just pass through
      self.out.fillBranch("puWeight", 1.0)
      self.out.fillBranch("puWeightUp", 1.0)
      self.out.fillBranch("puWeightDown", 1.0)
      return True

    w = 1.0
    w_up = 1.0
    w_down = 1.0
    try:
      corr = self.evaluator["PU"]
      w = corr.evaluate(self.era, "nominal", ntrue)
      w_up = corr.evaluate(self.era, "up", ntrue)
      w_down = corr.evaluate(self.era, "down", ntrue)
    except Exception as e:
      print(f"[PUWeightRun3] Warning: failed to evaluate PU weight: {e}")

    self.out.fillBranch("puWeight", w)
    self.out.fillBranch("puWeightUp", w_up)
    self.out.fillBranch("puWeightDown", w_down)
    return True


PUWeight2022 = lambda: PUWeightRun3("2022")
PUWeight2022EE = lambda: PUWeightRun3("2022EE")

