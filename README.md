# Triple Photon Analysis (γγγ)

This repository contains the CMS analysis framework for **triple photon (γγγ)** events. The analysis selects events with three photons.

## Analysis Overview

- **Signal Region (SR)**: Events with ≥3 photons
- **Sideband Regions (SB)**: Events with 1-2 photons (for background estimation)
- **Variables**: Triple photon invariant mass (Maaa), pair masses (M_p1p2, M_p1p3, M_p2p3), kinematic variables for all three photons
- **Optional jet variables**: If jets are present in the event, jet-photon angular variables are computed

## CMSSW Setup

### Option 1: CMSSW_10_6_30 (Legacy)

0. login to lxplus8 or lxplus9, execute "cmssw-el7" to launch the singularity. **This must be done before set up the CMSSW**, otherwise there will be imcompatibility between arch and cmssw
1. cmsrel CMSSW_10_6_30
2. Set up NanoAOD tools
   ```bash
   cd CMSSW_10_6_30/src

   git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git PhysicsTools/NanoAODTools

   cd PhysicsTools/NanoAODTools

   cmsenv

   scram b
   ```

### Option 2: CMSSW_13_0_X or later (Recommended for Run 3)

For Run 3 analyses, NanoAOD-tools is integrated into newer CMSSW releases:

```bash
# On lxplus9 (no singularity needed)
cmsrel CMSSW_13_0_13
cd CMSSW_13_0_13/src
cmsenv

# NanoAOD-tools is already available in PhysicsTools/NanoAODTools
scram b
```

### Option 3: CMSSW_14_X (Latest)

For the latest features and Run 3 UL corrections:

```bash
cmsrel CMSSW_14_0_7
cd CMSSW_14_0_7/src
cmsenv
scram b
```

## Set up analysis codes

```bash
cd $CMSSW_BASE/src/PhysicsTools/NanoAODTools/python/postprocessing

##clone this repository
git clone <this-repository-url> analysis

cd $CMSSW_BASE/src

scram b
```

Note: The `crab_help.py` is written in python3, hence the `scram b` in CMSSW would leave some error message. Since this crab helper normally would not be included by other codes, you can ignore these errors.

## Initialize for specific year

```bash
cd $CMSSW_BASE/src/PhysicsTools/NanoAODTools/python/postprocessing/analysis

source init.sh 2017
```

## submit jobs

cd analysis/crab

using the configure files under 'configs', namely,

crab submit -c configs/DoubleEGB_cfg.py

rm crab_DoubleEG_B/inputs/*.tgz 

You can also check `crab/auto_crab_example` to run crab jobs batchly and automatically.

## corrections

the modules (most of them are corrections) used can be seen from analysis/crab/crab_script.py,

N.B. the egamma correction is already applied default in NanoAOD

#### for MC:

countHistogramsModule(): store the opsitive and negative events number for weight apply

puWeight_2017(): pileup reweight

PrefCorr(): L1-prefiring correction

muonIDISOSF2017(): muon ID/ISO SF

muonScaleRes2017(): muon momentum correction, i.e., the Rochester correction

eleRECOSF2017(): electron RECO SF

eleIDSF2017(): electron IS SF

jmeCorrections_UL2017MC(): JetMET correction

#### for Data:

muonScaleRes2017(): muon momentum correction, i.e., the Rochester correction

jmeCorrections_UL2017*(): JetMET correction

### 1. pileup reweight 
(this correction is applied using the official module, so we need to update the rootfiles for pileup and do some modification on the official module. The files under others/for_pileup/ can be used directly)

#### data

according to https://twiki.cern.ch/twiki/bin/view/CMS/PileupJSONFileforData#Centrally_produced_ROOT_histogra, use histograms under /afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions17/13TeV/PileUp/UltraLegacy/, combine three histograms to a single one with name “pileup, pileup_plus, pileup_minus”

#### MC

https://twiki.cern.ch/twiki/bin/view/CMS/PileupScenariosRun2

move "mcPileupUL2017.root" and "PileupHistogram-goldenJSON-13tev-UL2017-99bins_withVar.root" to python/postprocessing/data/pileup/, and move "puWeightProducer.py" to python/postprocessing/modules/common/

### 2. prefiring correction 
(needed files are in others/for_prefiring, can be used directly)

details are here: Pre-firing: https://twiki.cern.ch/twiki/bin/viewauth/CMS/L1ECALPrefiringWeightRecipe#Accessing_the_UL2017_maps, in order to use the current NanoAOD module, extract separate rootfiles from https://github.com/cms-data/PhysicsTools-PatUtils/raw/master/L1PrefiringMaps.root

#### data & MC

move "others/for_prefiring/*.root" to NanoAODTools/data/prefire_maps/, and move "others/for_prefiring/PrefireCorr.py" to postprocessing/modules/common/

### 3. JME correction
(needed files are in others/for_jme, can be used directly)
move the *.tgz to PhysicsTools/NanoAODTools/data/jme, and move "jetmetHelperRun2.py" to PhysicsTools/NanoAODTools/python/postprocessing/modules/jme

## After finisihing all the file moving, please remember delete the "others" directory, as the crab submission have size limit.
