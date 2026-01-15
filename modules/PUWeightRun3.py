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
    # Map year to correction name and CVMFS path (jsonpog-integration)
    year_to_correction_name = {
      "2022": "Collisions2022_355100_357900_eraBCD_GoldenJson",
      "2022EE": "Collisions2022_359022_362760_eraEFG_GoldenJson",
    }
    self.correction_name = year_to_correction_name.get(year, None)
    year_to_cvmfs_path = {
      "2022": "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/LUM/2022_Summer22/puWeights.json.gz",
      "2022EE": "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/LUM/2022_Summer22EE/puWeights.json.gz",
    }
    self.pu_path = year_to_cvmfs_path.get(year, None)
    if self.pu_path is None:
      self.pu_path = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/analysis/data/year%s/pileup.json.gz" % (os.environ["CMSSW_BASE"], self.year)

  def beginJob(self):
    if not os.path.exists(self.pu_path):
      # Try alternative paths: without .gz, or in 2024-01-31 subdirectory, or old pileup.json.gz name
      alternatives = [
        self.pu_path.replace(".json.gz", ".json"),
        self.pu_path.replace("/latest/", "/2024-01-31/"),
        self.pu_path.replace("puWeights.json.gz", "pileup.json.gz"),
        self.pu_path.replace("/latest/puWeights.json.gz", "/pileup.json.gz"),
      ]
      found = False
      for alt in alternatives:
        if os.path.exists(alt):
          self.pu_path = alt
          found = True
          break
      if not found:
        raise FileNotFoundError(f"PU weight file not found: {self.pu_path}\nTried alternatives: {alternatives}")
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
      corr = self.evaluator[self.correction_name]
      # Correction signature: evaluate(NumTrueInteractions, weights)
      # where weights is "nominal", "up", or "down"
      w = corr.evaluate(ntrue, "nominal")
      w_up = corr.evaluate(ntrue, "up")
      w_down = corr.evaluate(ntrue, "down")
    except Exception as e:
      # Silently set to 1.0 for out-of-range ntrue values
      # Only print first few warnings to avoid log spam
      if not hasattr(self, '_pu_warn_count'):
        self._pu_warn_count = 0
      if self._pu_warn_count < 5:
        print(f"[PUWeightRun3] Warning: failed to evaluate PU weight for ntrue={ntrue}: {e}")
        self._pu_warn_count += 1
      elif self._pu_warn_count == 5:
        print(f"[PUWeightRun3] (suppressing further PU weight warnings)")
        self._pu_warn_count += 1

    self.out.fillBranch("puWeight", w)
    self.out.fillBranch("puWeightUp", w_up)
    self.out.fillBranch("puWeightDown", w_down)
    return True


PUWeight2022 = lambda: PUWeightRun3("2022")
PUWeight2022EE = lambda: PUWeightRun3("2022EE")

