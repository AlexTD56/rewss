# -*- coding: utf-8 -*-
"""
Created on Tue Jan  1 20:09:14 2013

@author: Alex
"""
import numpy as np
import random

class Source:
    """Data structure for sources
    Takes an arbitrary name, which can be used as a reference in methods,
    classFlag for demand class (0 for electricity, etc.)
    refEff for reference efficiency that impacts are calculated at
    v is variability - 0 for naturally varying and uncontrolled (e.g. wind)
    1 for fully controlled and dispatchable (e.g. coal)
    2 for fully controlled levelling (one per class) (e.g. NG)
    3 for naturally varying but dispatchable (e.g. hydro)"""
    
    def __init__(self, name, classFlag, refEff=.97,refCF=1, v=1):
        self.name = name        
        self.demClass = classFlag
        self.variable = v 
        self.refEff=refEff
        self.refCF = refCF
        self.Modes = [[]]
        self.Modes.append([])
        self.Modes.append([])
        
    def addOpsMode(self, name, cf, eff):
        self.Modes[0].append(OpsMode(name,cf,eff))
        if len(self.Modes[0])>1:
            self.Modes[0][-1].LCADists = self.Modes[0][0].LCADists.copy()
            
    def addConstMode(self,name,years,minCap):
        self.Modes[1].append(ConstMode(name,years,minCap))
        if len(self.Modes[1])>1:
            self.Modes[1][-1].LCADists = self.Modes[1][0].LCADists.copy()
            
    def addFuelMode(self,name):
        self.Modes[2].append(Mode(name))
        if len(self.Modes[2])>1:
            self.Modes[2][-1].LCADists = self.Modes[2][0].LCADists.copy()
            
    def setLCA(self,stageFlag,modeFlag,data,row=0):
        data = np.array(data,ndmin=2)        
        if type(modeFlag) is int:
            self.Modes[stageFlag][modeFlag].LCADists[row:row+len(data)] = data
        elif type(modeFlag) is str:
            for modes in self.Modes[stageFlag]:
                if modeFlag in modes.name:
                    modes.LCADists[row:row+len(data)] = data
            
    def setLCABase(self,stageFlag,modeFlag,data,row=0):
        if type(modeFlag) is int:
            self.Modes[stageFlag][modeFlag].LCADists[row:row+len(data),0] = data
        elif type(modeFlag) is str:
            for modes in self.Modes[stageFlag]:
                if modeFlag in modes.name:
                    modes.LCADists[row:row+len(data),0] = data
                    
    def getLCAEst(self,stageFlag=None,modeFlag=None, mode=1):
        if stageFlag==None:
            sourceDist = []            
            for stages in self.Modes:
                if modeFlag==None:
                    sourceDist.append(np.array([m.getDist(mode) for m in stages]).squeeze().transpose().reshape((5,-1)))
                else: 
                    sourceDist.append(np.array(stages[mode].getDist()).squeeze().transpose().reshape((5,-1)))                    
            return sourceDist
        else:
            if modeFlag==None:
                return np.array([m.getDist(mode) for m in self.Modes[stageFlag]]).squeeze().transpose().reshape((5,-1))
            else: return self.Modes[stageFlag][modeFlag].getDist(mode)
        
    def genCF(self,modeFlag=0):
        return CalcDist(self.Modes[0][modeFlag].capFac)
        
    def genEff(self,modeFlag=0):
        return CalcDist(self.Modes[0][modeFlag].eff)
        
        
        
class Mode:
    "Basic structure for modes"
    
    def __init__(self,name):
        self.name=name
        self.LCADists = np.zeros((5,4))
        
    def __str__(self):
        return self.name
        
    def getDist(self, mode=1,row=None):
        if row==None:        
            return CalcDist(self.LCADists,mode)
        else: return CalcDist(self.LCADists[row],mode)
        
class OpsMode(Mode):

    "Operational Modes"
    
    def __init__(self, name, cf, eff):
        Mode.__init__(self,name)
        self.capFac = np.array(cf)
        self.eff = np.array(eff)
     
class ConstMode(Mode):
    "Construction Modes"
    
    def __init__(self, name, years, minCap):
        Mode.__init__(self,name)
        self.years = years
        self.minCap = minCap
        
        
def CalcDist(X,mode=1):
    
    if X.ndim == 1:
        X = X.reshape((1,X.shape[0]))
        
    out = np.zeros((X.shape[0],1))  
    
    if mode==0:
        for i,row in enumerate(X):
            if row[0]==-1: #lognormal
                out[i]=np.e**row[1]
            elif row[0]==-2:
                out[i]=row[1]
            elif row[0]==-3: #uniform
                out[i]=(row[1]+row[2])/2
            elif row[0]==-4:
                out[i]=row[2]
            elif row[0]==-5:
                out[i]=row[1]
            else:
                out[i]=row[0]
        return out
    
    for i,row in enumerate(X):
        if row[0]==-1: #lognormal
            out[i]=random.lognormvariate(row[1],row[2])
        elif row[0]==-2:
            t = random.random()
            for j in range(1,X.shape[1]):
                if t < row[1:1+j].sum():
                    out[i] = j-1
                    break
        elif row[0]==-3: #uniform
            out[i]=random.uniform(row[1],row[2])
        elif row[0]==-4:
            out[i]=random.triangular(row[1],row[2],row[3]) 
        elif row[0]==-5:
            out[i]=random.normalvariate(row[1],row[2])
        else:
            out[i]=row[0]
            
    return out
            
    
        