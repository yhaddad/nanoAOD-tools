import ROOT
import os
import numpy as np
ROOT.PyConfig.IgnoreCommandLineOptions = True

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

class lepSFProducer(Module):
    def __init__(self, muonSelectionTag, electronSelectionTag):
        if muonSelectionTag=="LooseWP_2016":
            mu_f=["EfficienciesAndSF_RunBtoF_Nov17Nov2017.root",
                  "RunBCDEF_mc_ID.root",
                  "RunBCDEF_mc_ISO.root"]
            mu_h = [
                "IsoMu27_PtEtaBins/pt_abseta_ratio",
                "NUM_LooseID_DEN_genTracks_pt_abseta",
                #"MC_NUM_LooseID_DEN_genTracks_PAR_pt_eta/pt_abseta_ratio",
                "NUM_LooseRelIso_DEN_LooseID_pt_abseta"
                #"LooseISO_LooseID_pt_eta/pt_abseta_ratio"
            ]
        if electronSelectionTag=="GPMVA90_2016":
            el_f = ["2017_ElectronMVA90.root",
                    "egammaEffi.txt_EGM2D_runBCDEF_passingRECO.root",
                    "egammaEffi.txt_EGM2D_runBCDEF_passingRECO_lowEt.root"
                    ]
            el_h = ["EGamma_SF2D", "EGamma_SF2D", "EGamma_SF2D"]
        mu_f = ["%s/src/PhysicsTools/NanoAODTools/python/postprocessing/data/leptonSF/" % os.environ['CMSSW_BASE'] + f for f in mu_f]
        el_f = ["%s/src/PhysicsTools/NanoAODTools/python/postprocessing/data/leptonSF/" % os.environ['CMSSW_BASE'] + f for f in el_f]
        self.mu_f = ROOT.std.vector(str)(len(mu_f))
        self.mu_h = ROOT.std.vector(str)(len(mu_f))
        for i in range(len(mu_f)): self.mu_f[i] = mu_f[i]; self.mu_h[i] = mu_h[i];
        self.el_f = ROOT.std.vector(str)(len(el_f))
        self.el_h = ROOT.std.vector(str)(len(el_f))
        for i in range(len(el_f)): self.el_f[i] = el_f[i]; self.el_h[i] = el_h[i];
        if "/LeptonEfficiencyCorrector_cc.so" not in ROOT.gSystem.GetLibraries():
            print "Load C++ Worker"
            ROOT.gROOT.ProcessLine(".L %s/src/PhysicsTools/NanoAODTools/python/postprocessing/helpers/LeptonEfficiencyCorrector.cc+" % os.environ['CMSSW_BASE'])
    def beginJob(self):
        self._worker_mu = ROOT.LeptonEfficiencyCorrector(self.mu_f,self.mu_h)
        self._worker_el = ROOT.LeptonEfficiencyCorrector(self.el_f,self.el_h)

    def endJob(self):
        pass
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.out.branch("Muon_SF"       , "F", lenVar="nMuon"    )
        self.out.branch("Muon_SFErr"    , "F", lenVar="nMuon"    )
        self.out.branch("Electron_SF"   , "F", lenVar="nElectron")
        self.out.branch("Electron_SFErr", "F", lenVar="nElectron")

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass
    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        muons     = Collection(event, "Muon")
        electrons = Collection(event, "Electron")

        sf_el = [ self._worker_el.getSF(el.pdgId,el.pt,el.eta) for el in electrons ]
        sf_mu = [ self._worker_mu.getSF(mu.pdgId,mu.pt,mu.eta) for mu in muons ]
        sferr_mu = [ self._worker_mu.getSFErr(mu.pdgId,mu.pt,mu.eta) for mu in muons ]
        sferr_el = [ self._worker_el.getSFErr(el.pdgId,el.pt,el.eta) for el in electrons ]
        self.out.fillBranch("Muon_SF"       , sf_mu)
        self.out.fillBranch("Electron_SF"   , sf_el)
        self.out.fillBranch("Muon_SFErr"    , sferr_mu)
        self.out.fillBranch("Electron_SFErr", sferr_el)

        return True

# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed

lepSF = lambda : lepSFProducer( "LooseWP_2016", "GPMVA90_2016")

