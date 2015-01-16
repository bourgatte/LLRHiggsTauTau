import FWCore.ParameterSet.Config as cms
process = cms.Process("TEST")

#set this cut in the cfg file
try: APPLYELECORR
except NameError:
    APPLYELECORR="None"
ELECORRTYPE=APPLYELECORR
try: IsMC
except NameError:
    IsMC=True
try: LEPTON_SETUP
except NameError:
    LEPTON_SETUP=2012
try: APPLYFSR
except NameError:
    APPLYFSR=False
### ----------------------------------------------------------------------
### Set the GT
### ----------------------------------------------------------------------
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")
if IsMC:
    #process.GlobalTag.globaltag = 'PLS170_V6AN1::All'#'GR_70_V2_AN1::All'   #MC in 70X, cf https://twiki.cern.ch/twiki/bin/view/CMS/MiniAOD
    process.GlobalTag.globaltag = 'PHYS14_25_V1::All' #MC in PHYS14
else :
    process.GlobalTag.globaltag = 'GR_70_V2_AN1::All'   # data in 70X, cf https://twiki.cern.ch/twiki/bin/view/CMS/MiniAOD
print process.GlobalTag.globaltag

### ----------------------------------------------------------------------
### Standard stuff
### ----------------------------------------------------------------------
process.load("FWCore.MessageService.MessageLogger_cfi")
process.load("Configuration.StandardSequences.GeometryDB_cff")
process.load("Configuration.StandardSequences.MagneticField_38T_cff")
process.load("TrackingTools.TransientTrack.TransientTrackBuilder_cfi")
process.options = cms.untracked.PSet( wantSummary = cms.untracked.bool(True) )


process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(-1)
)

### ----------------------------------------------------------------------
### Trigger bit Requests 
### ----------------------------------------------------------------------
import HLTrigger.HLTfilters.hltHighLevel_cfi 
# !!!!!!!!!!!!

#process.L1GtStableParametersRcdSource = cms.ESSource("EmptyESSource",
#    iovIsRunNotTime = cms.bool(True),
#    recordName = cms.string('L1GtStableParametersRcd'),
#    firstValid = cms.vuint32(1)
#)

process.hltFilterDiMu = HLTrigger.HLTfilters.hltHighLevel_cfi.hltHighLevel.clone()
process.hltFilterDiMu.TriggerResultsTag = cms.InputTag("TriggerResults","","HLT")
process.hltFilterDiMu.throw = cms.bool(False) #FIXME: beware of this!
process.hltFilterDiMu.HLTPaths = TRIGGERLIST
#process.hltCsc2DRecHits.wireDigiTag  = cms.InputTag("simMuonCSCDigis","MuonCSCWireDigi")
#process.hltCsc2DRecHits.stripDigiTag = cms.InputTag("simMuonCSCDigis","MuonCSCStripDigi")
process.hltFilterDiMu.throw = cms.bool(False)
# !!!!!!!!!!!!

#MC stuff

process.load("SimGeneral.HepPDTESSource.pythiapdt_cfi")
process.drawTree = cms.EDAnalyzer("ParticleTreeDrawer",
                                   src = cms.InputTag("genParticlesPruned"),
                                   printP4 = cms.untracked.bool(False),
                                   printPtEtaPhi = cms.untracked.bool(False),
                                   printVertex = cms.untracked.bool(False),
                                   printStatus = cms.untracked.bool(True),
                                   printIndex = cms.untracked.bool(False) )


process.printTree = cms.EDAnalyzer("ParticleListDrawer",
                                   maxEventsToPrint = cms.untracked.int32(-1),
                                   printVertex = cms.untracked.bool(False),
                                   src = cms.InputTag("genParticlesPruned")
                                   )


process.RandomNumberGeneratorService = cms.Service("RandomNumberGeneratorService",
                                                   calibratedPatElectrons = cms.PSet(
                                                       initialSeed = cms.untracked.uint32(1),
                                                       engineName = cms.untracked.string('TRandom3')
                                                       ),
                                                   )


process.goodPrimaryVertices = cms.EDFilter("VertexSelector",
  #src = cms.InputTag("offlinePrimaryVertices"),
  src = cms.InputTag("offlineSlimmedPrimaryVertices"),
  cut = cms.string(PVERTEXCUT),
  filter = cms.bool(True),
)


### Mu Ghost cleaning
process.cleanedMu = cms.EDProducer("PATMuonCleanerBySegments",
                                   src = cms.InputTag("slimmedMuons"),
                                   preselection = cms.string("track.isNonnull"),
                                   passthrough = cms.string("isGlobalMuon && numberOfMatches >= 2"),
                                   fractionOfSharedSegments = cms.double(0.499))


process.bareSoftMuons = cms.EDFilter("PATMuonRefSelector",
    src = cms.InputTag("cleanedMu"),
    cut = cms.string(MUCUT)
#    Lowering pT cuts
#    cut = cms.string("(isGlobalMuon || (isTrackerMuon && numberOfMatches>0)) &&" +
#                     "pt>3 && p>3.5 && abs(eta)<2.4")
)


# MC matching. As the genParticles are no more available in cmg, we re-match with genParticlesPruned.
process.muonMatch = cms.EDProducer("MCMatcher", # cut on deltaR, deltaPt/Pt; pick best by deltaR
                                   src     = cms.InputTag("softMuons"), # RECO objects to match  
                                   matched = cms.InputTag("genParticlesPruned"),   # mc-truth particle collection
                                   mcPdgId     = cms.vint32(13), # one or more PDG ID (13 = muon); absolute values (see below)
                                   checkCharge = cms.bool(True), # True = require RECO and MC objects to have the same charge
                                   mcStatus = cms.vint32(1),     # PYTHIA status code (1 = stable, 2 = shower, 3 = hard scattering)
                                   maxDeltaR = cms.double(0.5),  # Minimum deltaR for the match
                                   maxDPtRel = cms.double(0.5),  # Minimum deltaPt/Pt for the match
                                   resolveAmbiguities = cms.bool(True),     # Forbid two RECO objects to match to the same GEN object
                                   resolveByMatchQuality = cms.bool(False), # False = just match input in order; True = pick lowest deltaR pair first
                                   )

process.softMuons = cms.EDProducer("MuFiller",
    src = cms.InputTag("bareSoftMuons"),
    sampleType = cms.int32(LEPTON_SETUP),                     
    setup = cms.int32(LEPTON_SETUP), # define the set of effective areas, rho corrections, etc.
#    cut = cms.string("userFloat('SIP')<100"),
#    cut = cms.string("userFloat('dxy')<0.5 && userFloat('dz')<1."),
    cut = cms.string(""),
    flags = cms.PSet(
        ID = cms.string("userFloat('isPFMuon')" ), # PF ID
        isGood = cms.string(MUCUT)
    )
)

process.muons =  cms.Sequence(process.cleanedMu + process.bareSoftMuons+ process.softMuons)
    

###
### Electrons
###
##--- Electron regression+calibrarion must be applied after BDT is recomputed
## NOTE patElectronsWithRegression->eleRegressionEnergy;  calibratedElectrons-> calibratedPatElectrons
## Default: NEW ECAL regression + NEW calibration + NEW combination
#process.load('EgammaAnalysis.ElectronTools.electronRegressionEnergyProducer_cfi')
#process.eleRegressionEnergy.inputElectronsTag = cms.InputTag('patElectronsWithTrigger')
#process.eleRegressionEnergy.energyRegressionType = 2 ## 1: ECAL regression w/o subclusters 2 (default): ECAL regression w/ subclusters)
##process.eleRegressionEnergy.vertexCollection = cms.InputTag('goodPrimaryVertices')
#process.load("EgammaAnalysis.ElectronTools.calibratedPatElectrons_cfi")
#process.calibratedPatElectrons.correctionsType = 2 # 1 = old regression, 2 = new regression, 3 = no regression, 0 = nothing
#process.calibratedPatElectrons.combinationType = 3
#process.calibratedPatElectrons.lumiRatio = cms.double(1.0)
#process.calibratedPatElectrons.isMC    = IsMC
#process.calibratedPatElectrons.synchronization = cms.bool(False)
#
##if (LEPTON_SETUP == 2011):
##   process.eleRegressionEnergy.rhoCollection = cms.InputTag('kt6PFJetsForIso:rho')
##   if (IsMC):
##       process.calibratedPatElectrons.inputDataset = "Fall11"
##   else :
##       process.calibratedPatElectrons.inputDataset = "Jan16ReReco"
##else :
##if (IsMC):
#process.calibratedPatElectrons.inputDataset = "Summer12_LegacyPaper"
##   else :
##process.calibratedPatElectrons.inputDataset = "22Jan2013ReReco"

    

process.bareSoftElectrons = cms.EDFilter("PATElectronRefSelector",
   src = cms.InputTag("slimmedElectrons"),#"calibratedPatElectrons"),
   cut = cms.string(ELECUT)
   )


process.softElectrons = cms.EDProducer("EleFiller",
   src    = cms.InputTag("bareSoftElectrons"),
   sampleType = cms.int32(LEPTON_SETUP),          
   setup = cms.int32(LEPTON_SETUP), # define the set of effective areas, rho corrections, etc.
#    cut = cms.string("userFloat('SIP')<100"),
#   cut = cms.string("userFloat('dxy')<0.5 && userFloat('dz')<1"),
   cut = cms.string(""),
   flags = cms.PSet(
        ID = cms.string("userFloat('isBDT')"), # BDT MVA ID
        isGood = cms.string("")
        )
   )

#process.electrons = cms.Sequence(process.eleRegressionEnergy + process.calibratedPatElectrons + process.bareSoftElectrons) #+ process.softElectrons)
process.electrons = cms.Sequence(process.bareSoftElectrons + process.softElectrons)

# Handle special cases
if ELECORRTYPE == "None" :   # No correction at all. Skip correction modules.
    process.bareSoftElectrons.src = cms.InputTag('slimmedElectrons')#patElectronsWithTrigger')#RH
    process.electrons = cms.Sequence(process.bareSoftElectrons + process.softElectrons)

elif ELECORRTYPE == "Moriond" : # Moriond corrections: OLD ECAL regression + OLD calibration + OLD combination 
    if (LEPTON_SETUP == 2011):
        process.eleRegressionEnergy.regressionInputFile = cms.string("EgammaAnalysis/ElectronTools/data/eleEnergyReg2011Weights_V1.root")
    else :
        process.eleRegressionEnergy.regressionInputFile = cms.string("EgammaAnalysis/ElectronTools/data/eleEnergyReg2012Weights_V1.root")
    process.eleRegressionEnergy.energyRegressionType = 1
    process.calibratedPatElectrons.correctionsType   = 1
    process.calibratedPatElectrons.combinationType   = 1

elif ELECORRTYPE == "Paper" : # NEW ECAL regression + NO calibration + NO combination
    process.eleRegressionEnergy.energyRegressionType = 2
    process.calibratedPatElectrons.correctionsType   = 0
    process.calibratedPatElectrons.combinationType   = 0
    

process.electronMatch = cms.EDProducer("MCMatcher",       # cut on deltaR, deltaPt/Pt; pick best by deltaR
                                       src         = cms.InputTag("bareSoftElectrons"), # RECO objects to match
                                       matched     = cms.InputTag("genParticlesPruned"), # mc-truth particle collection
                                       mcPdgId     = cms.vint32(11),               # one or more PDG ID (11 = electron); absolute values (see below)
                                       checkCharge = cms.bool(True),               # True = require RECO and MC objects to have the same charge
                                       mcStatus    = cms.vint32(1),                # PYTHIA status code (1 = stable, 2 = shower, 3 = hard scattering)
                                       maxDeltaR   = cms.double(0.5),              # Minimum deltaR for the match
                                       maxDPtRel   = cms.double(0.5),              # Minimum deltaPt/Pt for the match
                                       resolveAmbiguities    = cms.bool(True),     # Forbid two RECO objects to match to the same GEN object
                                       resolveByMatchQuality = cms.bool(False),    # False = just match input in order; True = pick lowest deltaR pair first
                                       )


### ----------------------------------------------------------------------
### Lepton Cleaning (clean electrons collection from muons)
### ----------------------------------------------------------------------

process.cleanSoftElectrons = cms.EDProducer("PATElectronCleaner",
    # pat electron input source
    src = cms.InputTag("softElectrons"),
    # preselection (any string-based cut for pat::Electron)
    preselection = cms.string(''),
    # overlap checking configurables
    checkOverlaps = cms.PSet(
        muons = cms.PSet(
           src       = cms.InputTag("softMuons"), # Start from loose lepton def
           algorithm = cms.string("byDeltaR"),
           preselection        = cms.string("(isGlobalMuon || userFloat('isPFMuon'))"), #
           deltaR              = cms.double(0.05),  
           checkRecoComponents = cms.bool(False), # don't check if they share some AOD object ref
           pairCut             = cms.string(""),
           requireNoOverlaps   = cms.bool(True), # overlaps don't cause the electron to be discared
        )
    ),
    # finalCut (any string-based cut for pat::Electron)
    finalCut = cms.string(''),
)

##
## Taus
##
process.bareTaus = cms.EDFilter("PATTauRefSelector",
   src = cms.InputTag("slimmedTaus"),
   cut = cms.string(TAUCUT)
   )

process.softTaus = cms.EDProducer("TauFiller",
   src = cms.InputTag("bareTaus"),
   cut = cms.string(TAUCUT),
   discriminator = cms.string(TAUDISCRIMINATOR),
   flags = cms.PSet(
        isGood = cms.string("")
        )
   )

process.tauMatch = cms.EDProducer("MCMatcher",
    src = cms.InputTag("softTaus"),
    maxDPtRel = cms.double(999.9),
    mcPdgId = cms.vint32(15),
    mcStatus = cms.vint32(2),
    resolveByMatchQuality = cms.bool(False),
    maxDeltaR = cms.double(999.9),
    checkCharge = cms.bool(True),
    resolveAmbiguities = cms.bool(True),
    matched = cms.InputTag("genParticlesPruned")
    )


process.taus=cms.Sequence(process.bareTaus + process.softTaus)

### ----------------------------------------------------------------------
### Search for FSR candidates
### ----------------------------------------------------------------------
process.load("UFHZZAnalysisRun2.FSRPhotons.fsrPhotons_cff")
process.appendPhotons = cms.EDProducer("LeptonPhotonMatcher",
    muonSrc = cms.InputTag("softMuons"),
    electronSrc = cms.InputTag("cleanSoftElectrons"),
    photonSrc = cms.InputTag("boostedFsrPhotons"),#cms.InputTag("cmgPhotonSel"),
    matchFSR = cms.bool(True)
    )

process.fsrSequence = cms.Sequence(process.fsrPhotonSequence + process.appendPhotons)
muString = "appendPhotons:muons"
eleString = "appendPhotons:electrons"
if not APPLYFSR : 
    process.fsrSequence = cms.Sequence()
    muString = "softMuons"
    eleString = "softElectrons"
    tauString = "softTaus"
#Leptons
process.softLeptons = cms.EDProducer("CandViewMerger",
    #src = cms.VInputTag(cms.InputTag("slimmedMuons"), cms.InputTag("slimmedElectrons"),cms.InputTag("slimmedTaus"))
    src = cms.VInputTag(cms.InputTag(muString), cms.InputTag(eleString),cms.InputTag(tauString))
)
#print: "lepton collection built"

#
#Jets
#
process.jets = cms.EDFilter("PATJetRefSelector",
                           src = cms.InputTag("slimmedJets"),
                           cut = cms.string(JETCUT)
)
##
## Build ll candidates (here OS)
##
process.barellCand = cms.EDProducer("CandViewShallowCloneCombiner",
                                    decay = cms.string("softLeptons@+ softLeptons@-"),
                                    cut = cms.string(LLCUT),
                                    checkCharge = cms.bool(True)
)




## ----------------------------------------------------------------------
## MVA MET
## ----------------------------------------------------------------------

# plugin initialization

process.load("RecoJets.JetProducers.ak4PFJets_cfi")
process.ak4PFJets.src = cms.InputTag("packedPFCandidates")

from JetMETCorrections.Configuration.DefaultJEC_cff import ak4PFJetsL1FastL2L3

# output collection is defined here, its name is pfMVAMEt
# access this through pfMVAMEtSequence

process.load("RecoMET.METPUSubtraction.mvaPFMET_cff")
#process.pfMVAMEt.srcLeptons = cms.VInputTag("slimmedElectrons") # srcLeptons contains all the hard scatter products, is set later
process.pfMVAMEt.srcPFCandidates = cms.InputTag("packedPFCandidates")
process.pfMVAMEt.srcVertices = cms.InputTag("offlineSlimmedPrimaryVertices")
process.pfMVAMEt.minNumLeptons = cms.int32(2) # this is important to skip void collections in the loop on pairs

process.puJetIdForPFMVAMEt.jec = cms.string('AK4PF')
#process.puJetIdForPFMVAMEt.jets = cms.InputTag("ak4PFJets")
process.puJetIdForPFMVAMEt.vertexes = cms.InputTag("offlineSlimmedPrimaryVertices")
process.puJetIdForPFMVAMEt.rho = cms.InputTag("fixedGridRhoFastjetAll")



# python trick: loop on all pairs for pair MET computation

if USEPAIRMET:
   print "Using pair MET"

   # template of unpacker
   UnpackerTemplate = cms.EDProducer ("PairUnpacker",
                                   src = cms.InputTag("barellCand"))

   process.METSequence = cms.Sequence(process.ak4PFJets + process.calibratedAK4PFJetsForPFMVAMEt + process.puJetIdForPFMVAMEt)

   MVAPairMET = ()
   for index in range(100):
      UnpackerName = "PairUnpacker%i" % index
      UnpackerModule = UnpackerTemplate.clone( pairIndex = cms.int32(index) )
      setattr(process, UnpackerName, UnpackerModule)   #equiv to process.<UnpackerName> = <UnpackerModule>
      process.METSequence += UnpackerModule

      MVAMETName = "pfMETMVA%i" % index
      MVAModule = process.pfMVAMEt.clone( srcLeptons = cms.VInputTag (cms.InputTag(UnpackerName) ) )
      setattr(process, MVAMETName, MVAModule)
      process.METSequence += MVAModule
    
      MVAPairMET += (cms.InputTag(MVAMETName),)
    
else:
   print "Using event MET (same MET for all pairs)"
   process.pfMVAMEt.minNumLeptons = cms.int32(0) # ONLY FOR DEBUG PURPOSE, OTHERWISE DOES NOT COMPUTE MET AND SVFIT CRASHES DUE TO A SINGULAR MATRIX
   process.METSequence = cms.Sequence(
       process.ak4PFJets         +
       process.pfMVAMEtSequence
   )



## ----------------------------------------------------------------------
## SV fit
## ----------------------------------------------------------------------
process.SVllCand = cms.EDProducer("SVfitInterface",
                                  srcPairs   = cms.InputTag("barellCand"),
                                  #srcMET     = cms.InputTag("pfMVAMEt"),
                                  #srcMET     = cms.InputTag("slimmedMETs"),
                                  usePairMET = cms.untracked.bool(USEPAIRMET),
								  useMVAMET  = cms.untracked.bool(True)								
)

if USEPAIRMET:
   process.SVllCand.srcMET    = cms.VInputTag(MVAPairMET)
else:
   process.SVllCand.srcMET    = cms.VInputTag("pfMVAMEt")



#Global configuration
TreeSetup = cms.EDAnalyzer("HTauTauNtuplizer",
                      CandCollection = cms.untracked.string("SVllCand"),
                      fileName = cms.untracked.string ("CosaACaso"),
                      skipEmptyEvents = cms.bool(True),
                      applyFSR = cms.bool(APPLYFSR),
                      triggerResultsLabel = cms.InputTag("TriggerResults", "", "HLT"),
                      )

process.HTauTauTree = TreeSetup.clone()

##
## Paths
##
process.PVfilter = cms.Path(process.goodPrimaryVertices)
#process.triggerDiMu = cms.Path(process.hltFilterDiMu)
#SkimPaths = cms.vstring('triggerDiMu') #Do not apply skim 

# Prepare lepton collections
process.Candidates = cms.Sequence(
    process.hltFilterDiMu     + 
    process.muons             +
    process.electrons         + process.cleanSoftElectrons +
    process.taus              +
    process.fsrSequence       +
    process.softLeptons       + process.barellCand +
    process.jets              +
    process.METSequence       +
	process.SVllCand          + process.HTauTauTree
    )
