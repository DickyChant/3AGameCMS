from WMCore.Configuration import Configuration

config = Configuration()

config.section_("General")
config.General.requestName = 'DiPhoton_40to80'
config.General.transferLogs = True

config.section_("JobType")
config.JobType.allowUndistributedCMSSW = True
config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'PSet.py'
config.JobType.scriptExe = '2022_script/crab_script.sh'
# hadd nano will not be needed once nano tools are in cmssw
config.JobType.inputFiles = ['crab_script.py', '../scripts/haddnano.py','keep_and_drop.txt']
#config.JobType.sendPythonFolder = True

config.section_("Data")
config.Data.inputDataset = '/DiPhotonJetsBox_MGG-40to80_13p6TeV_sherpa/Run3Summer22NanoAODv12-130X_mcRun3_2022_realistic_v5-v2/NANOAODSIM'
config.Data.inputDBS = 'global'
config.Data.splitting = 'FileBased'
#config.Data.outLFNDirBase = '/store/group/phys_top/ExtraYukawa/TTC_version9/'
config.Data.unitsPerJob = 1
config.Data.totalUnits = -1
config.Data.publication = False
config.Data.outputDatasetTag = 'DiPhoton_40to80'

config.section_("Site")
config.Site.storageSite = "T2_CH_CERN"
