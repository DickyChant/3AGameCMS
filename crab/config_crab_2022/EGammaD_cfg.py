from WMCore.Configuration import Configuration

config = Configuration()

config.section_("General")
config.General.requestName = 'EGamma_D'
config.General.transferLogs = True

config.section_("JobType")
config.JobType.allowUndistributedCMSSW = True
config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'PSet.py'
config.JobType.scriptExe = '2022_script/crab_script_dataD.sh'
# hadd nano will not be needed once nano tools are in cmssw
config.JobType.inputFiles = ['crab_script.py', '../scripts/haddnano.py','keep_and_drop.txt','Cert_Collisions2022_355100_357900_Golden.json']
#config.JobType.sendPythonFolder = True

config.section_("Data")
config.Data.inputDataset = '/EGamma/Run2022D-22Sep2023-v1/NANOAOD'
config.Data.inputDBS = 'global'
config.Data.splitting = 'LumiBased'
config.Data.unitsPerJob = 80
config.Data.lumiMask = 'Cert_Collisions2022_355100_357900_Golden.json'
#config.Data.outLFNDirBase = '/store/group/phys_top/ExtraYukawa/TTC_version9/'
config.Data.publication = False
config.Data.outputDatasetTag = 'EGamma_D'

config.section_("Site")
config.Site.storageSite = "T2_CH_CERN"
