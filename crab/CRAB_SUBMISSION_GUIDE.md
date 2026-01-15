# CRAB Job Submission Guide

## Overview

This guide explains how to submit CRAB jobs for triphoton NanoAOD analysis. The repository contains a streamlined workflow for processing multiple data and MC samples across different years (2016-2022).

## Prerequisites

### 1. CMSSW Environment
```bash
# Must be in CMSSW environment
cd /home/sqian/Codes/3a_analysis/CMSSW_14_0_7/src/
cmsenv
```

### 2. Valid Grid Certificate
```bash
# Initialize your grid proxy (valid for 7 days)
voms-proxy-init --voms cms --valid 192:00

# Check proxy status
voms-proxy-info
```

### 3. CRAB3 Available
```bash
# Check CRAB is accessible (should be from CVMFS)
which crab
# Expected: /cvmfs/cms.cern.ch/common/crab

# Source CRAB environment if needed
source /cvmfs/cms.cern.ch/common/crab-setup.sh
```

## Required Files Checklist

All files are located in: `PhysicsTools/NanoAODTools/python/postprocessing/analysis/crab/`

### Core Submission Scripts
- [x] `submit_crab.sh` - Main orchestration script
- [x] `create_crab.py` - Configuration generator
- [x] `crab_script.py` - Analysis execution script (runs on worker nodes)

### CRAB Configuration Templates
- [x] `data_cfg.py` - Template for data samples (with lumi mask)
- [x] `mc_cfg.py` - Template for MC samples

### Helper Files
- [x] `PSet.py` - Dummy parameter set for CRAB
- [x] `haddnano.py` - Output file merger
- [x] `keep_and_drop.txt` - Branch selection rules

### Sample Definitions (JSON)
- [x] `samples2016apv.json` - Pre-APV 2016 data/MC
- [x] `samples2016.json` - Post-APV 2016 data/MC
- [x] `samples2017.json` - 2017 UL data/MC
- [x] `samples2018.json` - 2018 UL data/MC
- [x] `samples2022.json` - Run3 2022 data/MC
- [x] `samples2022EE.json` - Run3 2022 postEE data/MC

### Year-Specific Execution Scripts
- [x] `2016apv_script/` - Shell wrappers for 2016apv
- [x] `2016_script/` - Shell wrappers for 2016
- [x] `2017_script/` - Shell wrappers for 2017
- [x] `2018_script/` - Shell wrappers for 2018
- [x] `2022_script/` - Shell wrappers for 2022
- [x] `2022EE_script/` - Shell wrappers for 2022EE

Each directory contains:
- `crab_script.sh` - MC processing script
- `crab_script_data<Era>.sh` - Era-specific data processing scripts

### Analysis Modules (Parent Directory)
Located in: `PhysicsTools/NanoAODTools/python/postprocessing/`

#### Framework
- [x] `framework/crabhelper.py` - CRAB file handling utilities
- [x] `framework/postprocessor.py` - Event processing framework

#### Analysis Modules
- [x] `modules/jme/jetmetHelperRun2.py` - JME corrections
- [x] `modules/common/PhoIDSFProducer.py` - Photon ID scale factors
- [x] `modules/common/puWeightProducer.py` - Pileup reweighting
- [x] `modules/common/PrefireCorr.py` - L1 prefire corrections
- [x] `analysis/TriPhoton.py` - Triphoton selection module

## Sample JSON Format

Each `samples<YEAR>.json` file defines datasets to process:

```json
{
  "EGammaC": ["EGamma_C", "/EGamma/Run2022C-22Sep2023-v1/NANOAOD", "crab_script_dataC.sh"],
  "TTGG": ["TTGG", "/TTGG_TuneCP5_13p6TeV_amcatnlo-madspin-pythia8/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM"]
}
```

Format:
- **Data samples**: `[sample_name, DAS_path, era_script.sh]`
- **MC samples**: `[sample_name, DAS_path]`

## Quick Start

### Step 1: Navigate to CRAB Directory
```bash
cd PhysicsTools/NanoAODTools/python/postprocessing/analysis/crab/
```

### Step 2: Choose Your Year
Available years: `2016apv`, `2016`, `2017`, `2018`, `2022`, `2022EE`

### Step 3: Generate Configurations Only (Dry Run)
```bash
./submit_crab.sh 2022 config
```

This will:
- Read `samples2022.json`
- Create `config_crab_2022/` directory
- Generate individual `<sample>_cfg.py` files for each dataset
- Use appropriate Golden JSON for data samples

### Step 4: Review Generated Configs
```bash
ls config_crab_2022/
cat config_crab_2022/TTGG_cfg.py  # Example: check MC config
cat config_crab_2022/EGammaC_cfg.py  # Example: check data config
```

### Step 5: Submit All Jobs
```bash
./submit_crab.sh 2022 submit
```

This will:
- Generate configs (if not already done)
- Submit each sample using `crab submit -c <config>`
- Create `crab_<sample>/` directories
- Clean up tarballs after submission

### Step 6: Monitor Jobs
```bash
# Check status of all jobs
./submit_crab.sh 2022 status

# Check specific job
crab status -d crab_TTGG/

# Get detailed report
crab report -d crab_TTGG/
```

### Step 7: Resubmit Failed Jobs (if needed)
```bash
# Resubmit all failed jobs
./submit_crab.sh 2022 resubmit

# Resubmit specific job
crab resubmit -d crab_TTGG/
```

## Workflow Details

### Configuration Generation (`create_crab.py`)

For each sample in `samples<YEAR>.json`:

1. Determines if sample is data or MC (based on JSON entry format)
2. Copies appropriate template:
   - `data_cfg.py` → Data samples (with lumi mask)
   - `mc_cfg.py` → MC samples
3. Uses `sed` to substitute:
   - `SAMPLENAME` → Sample identifier
   - `DATASETNAME` → DAS dataset path
   - `SCRIPTNAME` → Era-specific execution script
   - `JSONDATASET` → Golden JSON URL for data
4. Saves to `config_crab_<YEAR>/<SAMPLE>_cfg.py`

### Job Execution on Worker Nodes

When a CRAB job runs:

1. Worker node receives files from CRAB scheduler
2. Executes `<YEAR>_script/crab_script.sh` (or era-specific version)
3. Script calls `crab_script.py --year <YEAR> --era <ERA>`
4. `crab_script.py`:
   - Uses `crabhelper.inputFiles()` to get input NanoAOD files
   - Loads year-specific corrections:
     - JME corrections (jetmetHelperRun2)
     - Photon ID scale factors
     - Pileup weights
     - L1 prefire corrections (pre-2022)
   - Runs `TriPhoton` analysis module
   - Produces output ROOT file with selected branches
5. CRAB merges outputs if multiple files per job
6. Output stored at: `T2_CH_CERN` storage element

### Data vs MC Processing

**Data samples**:
- Require Golden JSON for certified luminosity
- Split by `LumiBased` (typically 80 lumisections/job)
- Apply era-specific corrections (C, D, E, F, G, etc.)
- Use era-specific execution scripts

**MC samples**:
- No lumi mask needed
- Split by `FileBased` (1 file per job)
- Apply pileup reweighting
- Use generic `crab_script.sh`

### Golden JSON URLs

Automatically configured in `create_crab.py`:

- **2016apv/2016**: `Cert_271036-284044_13TeV_Legacy2016_Collisions16_JSON.txt`
- **2017**: `Cert_294927-306462_13TeV_UL2017_Collisions17_GoldenJSON.txt`
- **2018**: `Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt`
- **2022**: `Cert_Collisions2022_355100_362760_Golden.json`
- **2022EE**: `Cert_Collisions2022_359022_362760_Golden.json`

## CRAB Configuration Parameters

### Data Configuration (`data_cfg.py`)
```python
config.Data.splitting = 'LumiBased'
config.Data.unitsPerJob = 80  # Lumisections per job
config.Data.lumiMask = '<Golden JSON URL>'
```

### MC Configuration (`mc_cfg.py`)
```python
config.Data.splitting = 'FileBased'
config.Data.unitsPerJob = 1  # Files per job
# No lumiMask needed
```

### Common Settings
```python
config.General.transferOutputs = True
config.General.transferLogs = True
config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'PSet.py'
config.Data.publication = False
config.Site.storageSite = 'T2_CH_CERN'
```

## Output Files

### Location
Output stored at CERN Tier-2:
```
/store/user/<username>/crab_<sample>/...
```

### Retrieval
```bash
# List output files
crab getoutput -d crab_TTGG/ --dump

# Download outputs
crab getoutput -d crab_TTGG/
```

### Merging
Output files are automatically merged by CRAB using `haddnano.py`, which:
- Handles branches present in some but not all files
- Preserves ROOT compression settings
- Creates `tree_hadd.root` or similar

## Troubleshooting

### Proxy Issues
```bash
# Error: "Cannot find a valid proxy"
voms-proxy-init --voms cms --valid 192:00

# Check proxy expiration
voms-proxy-info | grep "timeleft"
```

### Job Failures
```bash
# Check error logs
crab status -d crab_<sample>/
crab getlog -d crab_<sample>/ --short

# Common fixes:
# 1. Increase memory: Add to config: config.JobType.maxMemoryMB = 4000
# 2. Increase runtime: Add to config: config.JobType.maxJobRuntimeMin = 2880
# 3. Resubmit failed: crab resubmit -d crab_<sample>/
```

### Missing Input Files
```bash
# Check DAS for dataset availability
dasgoclient --query="dataset=<dataset_path>"

# Verify files exist
dasgoclient --query="file dataset=<dataset_path>" | head
```

### Configuration Errors
```bash
# Test config locally before submission
crab submit -c config_crab_2022/TTGG_cfg.py --dryrun

# Validate PSet.py
cmsRun PSet.py
```

## Advanced Usage

### Submit Specific Samples Only
```bash
# Edit samples<YEAR>.json to include only desired samples
# Then run:
./submit_crab.sh 2022 submit
```

### Modify Job Parameters
Edit `data_cfg.py` or `mc_cfg.py` templates before running `create_crab.py`:
```python
# Example: Increase memory
config.JobType.maxMemoryMB = 4000

# Example: Change splitting
config.Data.unitsPerJob = 100  # More lumis per job
```

### Test Locally Before Submission
```bash
# Run crab_script.py locally with test file
cd PhysicsTools/NanoAODTools/python/postprocessing/analysis/crab/
python crab_script.py --year 2022 --era C
```

## Best Practices

1. **Always check proxy before submitting**
   ```bash
   voms-proxy-info
   ```

2. **Start with dry run**
   ```bash
   ./submit_crab.sh 2022 config  # Check configs first
   ```

3. **Monitor regularly**
   ```bash
   watch -n 300 './submit_crab.sh 2022 status'  # Every 5 minutes
   ```

4. **Keep logs**
   ```bash
   ./submit_crab.sh 2022 submit 2>&1 | tee submit_2022.log
   ```

5. **Clean up completed jobs**
   ```bash
   # After downloading outputs
   crab kill -d crab_<sample>/
   rm -rf crab_<sample>/
   ```

## Summary of Commands

```bash
# Setup
cd PhysicsTools/NanoAODTools/python/postprocessing/analysis/crab/
voms-proxy-init --voms cms --valid 192:00

# Generate configs only
./submit_crab.sh 2022 config

# Submit all jobs
./submit_crab.sh 2022 submit

# Check status
./submit_crab.sh 2022 status
crab status -d crab_<sample>/

# Resubmit failures
./submit_crab.sh 2022 resubmit
crab resubmit -d crab_<sample>/

# Get outputs
crab getoutput -d crab_<sample>/

# Get report (luminosity, efficiency)
crab report -d crab_<sample>/
```

## Contact & Support

For issues specific to this analysis:
- Check `crab_script.py` for module configurations
- Review `samples<YEAR>.json` for dataset paths
- Verify Golden JSON URLs are up-to-date

For CRAB-specific issues:
- CRAB Documentation: https://twiki.cern.ch/twiki/bin/view/CMSPublic/SWGuideCrab
- CRAB Hypernews: https://hypernews.cern.ch/HyperNews/CMS/get/computing-tools.html

## Verification Checklist

Before submitting CRAB jobs, verify:

- [ ] Valid VOMS proxy (at least 24 hours remaining)
- [ ] CMSSW environment sourced (`cmsenv`)
- [ ] Sample JSON file exists for your year
- [ ] Year-specific script directory exists
- [ ] Golden JSON URL is valid (check in `create_crab.py`)
- [ ] CRAB command available (`which crab`)
- [ ] DAS datasets accessible (`dasgoclient --query="dataset=..."`)
- [ ] Sufficient storage quota at T2_CH_CERN

All required files are present in this repository!
