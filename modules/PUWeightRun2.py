import os
import correctionlib._core

from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module


class PUWeightRun2(Module):
  """
  Pileup weights for Run2 UL (2016/2017/2018) using correctionlib JSON from CVMFS.
  Produces branches: puWeight, puWeightUp, puWeightDown.
  """
  def __init__(self, year):
    self.year = year
    # Map year to correction name and CVMFS path
    year_to_correction_name = {
      "2016apv": "Collisions16_UltraLegacy_goldenJSON",
      "2016": "Collisions16_UltraLegacy_goldenJSON",
      "2017": "Collisions17_UltraLegacy_goldenJSON",
      "2018": "Collisions18_UltraLegacy_goldenJSON",
    }
    self.correction_name = year_to_correction_name.get(year, None)
    year_to_cvmfs_path = {
      "2016apv": "/cvmfs/cms-griddata.cern.ch/cat/metadata/LUM/Run2-2016preVFP-UL-NanoAODv9/latest/puWeights.json.gz",
      "2016": "/cvmfs/cms-griddata.cern.ch/cat/metadata/LUM/Run2-2016postVFP-UL-NanoAODv9/latest/puWeights.json.gz",
      "2017": "/cvmfs/cms-griddata.cern.ch/cat/metadata/LUM/Run2-2017-UL-NanoAODv9/latest/puWeights.json.gz",
      "2018": "/cvmfs/cms-griddata.cern.ch/cat/metadata/LUM/Run2-2018-UL-NanoAODv9/latest/puWeights.json.gz",
    }
    self.pu_path = year_to_cvmfs_path.get(year, None)
    if self.pu_path is None:
      # Fallback to local path if year not in mapping
      self.pu_path = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/data/pileup/puWeights_%s.json.gz" % (os.environ["CMSSW_BASE"], self.year)
    print(f'[PUWeightRun2] Year: {self.year}')
    print(f'[PUWeightRun2] Correction name: {self.correction_name}')
    print(f'[PUWeightRun2] PU weights path: {self.pu_path}')

  def beginJob(self):
    if not os.path.exists(self.pu_path):
      # Try alternative paths: without .gz, or old path structure
      alternatives = [
        self.pu_path.replace(".json.gz", ".json"),
        self.pu_path.replace("/latest/", "/"),
        self.pu_path.replace("/latest/puWeights.json.gz", "/puWeights.json.gz"),
      ]
      found = False
      for alt in alternatives:
        if os.path.exists(alt):
          self.pu_path = alt
          found = True
          break
      if not found:
        raise FileNotFoundError(f"PU weight file not found: {self.pu_path}\nTried alternatives: {alternatives}")

    print(f'[PUWeightRun2] Loading PU weights from: {self.pu_path}')
    self.evaluator = correctionlib._core.CorrectionSet.from_file(self.pu_path)
    print(f'[PUWeightRun2] Successfully loaded PU weights')

  def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
    self.out = wrappedOutputTree
    self.out.branch("puWeight", "F")
    self.out.branch("puWeightUp", "F")
    self.out.branch("puWeightDown", "F")

  def endJob(self):
    pass

  def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
    pass

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
      # Correction signature: evaluate(NumTrueInteractions, variation)
      # where variation is "nominal", "up", or "down"
      w = corr.evaluate(ntrue, "nominal")
      w_up = corr.evaluate(ntrue, "up")
      w_down = corr.evaluate(ntrue, "down")
    except Exception as e:
      # Silently set to 1.0 for out-of-range ntrue values
      # Only print first few warnings to avoid log spam
      if not hasattr(self, '_pu_warn_count'):
        self._pu_warn_count = 0
      if self._pu_warn_count < 5:
        print(f"[PUWeightRun2] Warning: failed to evaluate PU weight for ntrue={ntrue}: {e}")
        self._pu_warn_count += 1
      elif self._pu_warn_count == 5:
        print(f"[PUWeightRun2] (suppressing further PU weight warnings)")
        self._pu_warn_count += 1

    self.out.fillBranch("puWeight", w)
    self.out.fillBranch("puWeightUp", w_up)
    self.out.fillBranch("puWeightDown", w_down)
    return True


# Factory functions for each year
PUWeight2016apv = lambda: PUWeightRun2("2016apv")
PUWeight2016 = lambda: PUWeightRun2("2016")
PUWeight2017 = lambda: PUWeightRun2("2017")
PUWeight2018 = lambda: PUWeightRun2("2018")
