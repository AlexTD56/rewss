# -*- coding: utf-8 -*-
"""
Created on Fri Jan  4 23:57:35 2013
@author: Alex
"""

import SourceData
import DataClasses as dc
import numpy as np
import os
import time

def main(scenData, trials=1, store=0, mode=1):
    """Main calculation method for REWSS Model
    
    Takes either string or tuple as primary scenData input
    Store = 1 will write data to location specified using scenData
    Mode = 0 will use central rather than random distribution values
    
    Returns ((Fleet, impsbyClass, impswithErr, impsbyStage, annReqs), MCATI)
    
    """
    astr = np.array_str
    
#########################################
#Setup national scenario 
#########################################
    
    sources=SourceData.main()
    names = [s.name for s in sources] #source name key    
    refEffs = [[s.refEff,s.refCF] for s in sources] #reference efficiencies


    if type(scenData) is str:
        brN,brD,knownCap,rparams,rpolicy,rprops = scenRead(scenData)
        scenname = scenData
    elif type(scenData) is tuple:
        brN,brD,knownCap,rparams,rpolicy,rprops,scenname = scenData
    
        
    syr = brD[0,1:]
    sflags = brD[1:,0].astype(int)
    baseReqs = brD[1:,1:] #the pure reqs data
    sourceNames = brN[1:] #Source names
    ssources = baseReqs[np.mod(sflags,2)==1,:] #source mix data, excluding demand
    sourceNames = sourceNames[np.mod(sflags,2)==1,:].squeeze().tolist()  
    
    totalClasses = int(sflags.max()/2)
    totalYears = int(syr[-1]-syr[0]+1)
    totalSources = int(ssources.shape[0])    
    
    sdemand = np.zeros((totalClasses,baseReqs.shape[1]))
    for cl in range(totalClasses): #Collect all demand for a given class
        sdemand[cl,:] = baseReqs[sflags==(cl+1)*2,:].sum(0)    
    
    sflags = sflags[np.mod(sflags,2)==1]
    sflags = (sflags+1)/2-1
    
    classflags = [sflags==0]
    for i in range(1,max(sflags)+1):
        classflags.append(sflags==i)
    print classflags
                
    for i in range(baseReqs.shape[1]): #normalize per-source scenario demand to avoid interpolation errors
         for j in range(totalClasses):
             print j
             ssources[classflags[j],i] = ssources[classflags[j],i]/ssources[classflags[j],i].sum(0)

    
    #Check LCA sources vs. scenario sources - if there are more in the scenario,
    #add blank sources to the stack. If there are more in the built-ins, the
    #code will just ignore the last N built-ins. 
    
    for i in range(totalSources):
            if names.count(sourceNames[i])>0: #if things just don't match, warn
                if names[i] == sourceNames[i]:
                    pass                    
                    #print names[i],'row match'
                else:
                    print 'Source ',names[i],' found. Row does not match'
            else: #if there's no source by that name, add one
                SourceData.addSource(sources,sourceNames[i],sflags[i])
                names.append(sourceNames[i])
                refEffs.append([.97,1])
                print 'Added',sourceNames[i],'to LCA sources. No data included'
    refEffs = np.array(refEffs,ndmin=2)

    #TODO user-defined sources/modes get input here

  
########################################
# Begin actual data processing - interpolate scenario requirements to ensure annual data
########################################

    reqsNat = np.zeros((totalSources,totalYears))
    demandNat = np.zeros((totalClasses,totalYears))
    reqsNat[:,0] = ssources[:,0]
    demandNat[:,0] = sdemand[:,0]    

    j=0
    for i in range(1,baseReqs.shape[1]):
        
        diff = int(syr[i]-syr[i-1])
        if diff==1: #no missing years
            reqsNat[:,i+j] = ssources[:,i]
            demandNat[:,i+j] = sdemand[:,i]
        else:
            base = j-1
            for j in range(j,j+diff):
                reqsNat[:,i+j] = reqsNat[:,i+base] + (ssources[:,i]-ssources[:,i-1])*(j-base)/(diff)
                demandNat[:,i+j] = demandNat[:,i+base] + (sdemand[:,i]-sdemand[:,i-1])*(j-base)/(diff)
   
    
###################################
# Set up capacity variables and information
###################################    
    #Adjust dates on known plants if necessary
    if knownCap[0,4] >100:   
        knownCap[:,4] = knownCap[:,4]-syr[0] #Adjust years to indices 
    
    #Parse regional requirements into annual floor/ceiling reqs
    policyLimits = np.zeros((totalSources,totalYears,3))
    if rpolicy[0,2]>100:    
        rpolicy[:,2:4] = rpolicy[:,2:4]-syr[0] #Index years rather than use absolutes
    #rpolicy(:,5) = rpolicy(:,5)/100; #fix %s to actual values
        
    if rparams[0,7]>100:
        rparams[:,7:9] -= syr[0]
    
    #Step 1: Set up fleet basics
    fleet = np.zeros((totalSources,totalYears,7))    
    fleet[:,0,0:3] = rprops[:,3:6]
    fleet[:,0,5:7] = rprops[:,6:8]
    #Build modes structure - known probabilities and space for specifics
    modes = []    
    for i,s in enumerate(sources):
        fleet[i,0,4] = s.variable
        modes.append([])
        for m in s.Modes:
            if len(m) == 1:
                modes[-1].append(np.ones((1,totalYears,2)))
            else:
                modes[-1].append(np.vstack((np.ones((1,totalYears,2)),np.zeros((len(m)-1,totalYears,2)))))

    
    #Step 2: set up mode probabiities
    for props in rprops:
        s = int(props[0]) 
        modes[s][0][:,0,1] = props[8:8+modes[s][0].shape[0]]
        modes[s][1][:,0,1] = props[13:13+modes[s][1].shape[0]]    
        modes[s][2][:,0,1] = props[18:18+modes[s][2].shape[0]]
    
    #Step 3: Include scenario-specific mode splits 
    for rp in rparams: 
        s = int(rp[0])
        st = int(rp[1])
        for yr in range(int(rp[7]),int(rp[8])+1):
            modes[s][st][:,yr,0] = rp[2:2+modes[s][st].shape[0]]
        
    #TODO Time-series adjustments to mode probabilities here   
    if 'AZ' in scenname:
        modes[7][0][1,:totalYears/4,0] = np.linspace(.2,.3,totalYears/4)
        modes[7][0][1,totalYears/4:,0] = np.linspace(.3,.05,totalYears*3/4+1)
        modes[7][0][2,:totalYears/2,0] = np.linspace(.1,.3,totalYears/2)
        modes[7][0][3,5:totalYears*3/4,0] = np.linspace(.05,.3,totalYears*3/4-5)

    #Copy mode splits forward
    for m in modes:
        for st in m:
            for opt in range(len(st[:,0,0])):
                for yr in range(1,totalYears):                
                    if (st[opt,yr-1,0]!=1 and st[opt,yr,0]==1) or (st[opt,yr-1,0]!=0 and st[opt,yr,0]==0): #if this year is default but the previous one isn't
                        st[opt,yr,0] = st[opt,yr-1,0]
                    if (st[opt,yr-1,1]!=1 and st[opt,yr,1]==1) or (st[opt,yr-1,1]!=0 and st[opt,yr,1]==0): #if this year is default but the previous one isn't
                        st[opt,yr,1] = st[opt,yr-1,1]
                        
    if 'AZ' in scenname:
        modes[7][0][0,:,0] = 1-modes[7][0][1:4,:,0].sum(0)
        modes[7][1][:,:,0] = modes[7][0][:,:,0]
                

    for plim in rpolicy:
        if plim[0] >0:
            for yr in range(int(plim[2]),int(plim[3])):
                if plim[1] == 1 or plim[1] == 2: #individual
                    policyLimits[plim[0],yr,0:2] = [plim[1],plim[4]]
#                elif plim[1] == 2: #ceiling
#                    policyLimits[plim[0],yr,1] = plim[4]
                elif plim[1] == 4: #group floor
                    policyLimits[plim[0],yr,2] = plim[4]
                     
    


    
#########################################
#Static demand regionalization
#Adjusts national data and includes regional polices
#Also blends known capacity changes to account for mix changes
#########################################
    
    if 'PA' in scenname:
        DrP = np.array([0.0557,0.036,0.0394,.0225,.047]) # 2010 Percentage of national demand consumed in target region - EIA data for PA for elec, transport, heat, water, wastewater
        #DrP = np.array([0.0557,0.036,0.0329,.0225,1]) # 1990 Percentage of national demand consumed in target region - EIA data for PA for elec, transport, heat, water, wastewater
        PrP = -.0001/0.0095 #General Line      
        #PrP = .003/0.0105 #Validation line Annual regional population growth rate over annual national population growth rate
        ElExports = .65
    elif 'AZ' in scenname:
        DrP = np.array([0.02709,0.01631,0.00603,1,1]) # 2010 Percentage of national demand consumed in target region - EIA data for AZ for elec, transport, heat, water, wastewater
        #DrP = np.array([0.02066,0.01455,0.00497,1,1]) # 1990 Percentage of national demand consumed in target region - EIA data for AZ for elec, transport, heat, water, wastewater
        PrP = 0.0192/0.0095 #Annual regional population growth rate over annual national population growth rate
        #PrP = 0.023/0.0105 #Annual regional population growth rate over annual national population growth rate
        ElExports = .66
    elif 'US' in scenname:
        DrP = np.array([1,1,1,1,1]) # Percentage of national demand consumed in target region - EIA data for AZ for elec, transport, heat, water, wastewater
        PrP = 0.0095/0.0095 #Annual regional population growth rate over annual national population growth rate
        ElExports = 1.0
    
    reqsReg = np.zeros(reqsNat.shape) #Reg. mix, # by source
    demandReg = np.zeros(demandNat.shape) #Reg. demand, amount by class
    reqsReg[:,0] = rprops[:,2]
    print reqsNat[0,:5]
    
    #Determine Regional Demand from current share (initial profile) and projected
    #population growth vs. nation for national scenarios.
    demandReg[:,0] = demandNat[:,0]*DrP
    for yr in range(1,totalYears):
        demandReg[:,yr] = demandReg[:,yr-1] + (demandNat[:,yr]-demandNat[:,yr-1])*DrP*PrP
        #demandReg[:,i] = demandReg[:,i-1]*(demandNat[:,i]/demandNat[:,i-1]*PrP)    
    
    print astr(fleet[:12,0,5].transpose())
    
    for i in range(totalYears):            
        
        if i>0:        
            #Basic adjustment - regional demand times national source % change
            reqsReg[:,i] = reqsReg[:,i-1]*(prefFlipArr(((reqsNat[:,i]+.00000001)/(reqsNat[:,i-1]+.00000001)-1),fleet[:,0,5])+1)
        
        for j in range(totalClasses):
            reqsReg[classflags[j],i] = reqsReg[classflags[j],i]/reqsReg[classflags[j],i].sum()    
    
        knownThisYear = knownCap[knownCap[:,4]==i]
        if i>0:        
            reqDiff = reqsReg[:,i]-reqsReg[:,i-1]  #already expected shift - we only want to adjust the mix if this additional project exceeds expectations    
        else:
            reqDiff = np.zeros((totalSources,1))
        
        for kp in knownThisYear:
            s,yr = int(kp[0]),int(kp[4])
            #Capacity factor and heat rate adjustment
            fleet[s,yr,1] = (fleet[s,yr,0]*fleet[s,yr,1]+kp[1]*kp[2])/(fleet[s,yr,0]+kp[1])
            fleet[s,yr,2] = (fleet[s,yr,0]*fleet[s,yr,2]+kp[1]*kp[3])/(fleet[s,yr,0]+kp[1])
            
            #Source methods adjustment
            for st in range(3):
                curModes = fleet[s,yr,0]*modes[s][st][:,yr,1]
                curModes[kp[6+st]] += kp[1]
                modes[s][st][:,yr,1] = curModes/curModes.sum()
            
            #Total capacity adjustment
            fleet[s,yr,0] += kp[1]
            
            #Construction breakdown
            if kp[5]>0 and kp[1]>0:         
                for k in range(yr):
                    if yr-k >= 1:
                        fleet[s,yr-k,3] += kp[1]/kp[5]
                        
            #Demand adjustment for retirements/additions
            srcClass = sflags[s]
            repPerc = kp[1]*8760*kp[2]/(demandReg[srcClass,i]*1e6) # Potential production as percentage of demand that year
            reqDiff[s] -= repPerc #Avoid excess reduction or addition

            if reqDiff[s]*repPerc < 0 and abs(reqDiff[s])<abs(repPerc):
                repPerc = reqDiff[s]*-1
            elif reqDiff[s]*repPerc > 0:
                repPerc = 0
            
            if repPerc != 0:
                reqsReg[kp[0],yr:] += repPerc  # For retirements, prod is negative      
                if kp[9] >=0: #assign extra demand to a particular source
                    reqsReg[kp[9],yr:] -= repPerc 
                elif kp[9] == -1: #Assign/remove demand to class default
                    defSource = np.argmax(np.logical_and(classflags[srcClass],fleet[:,0,4]==2))
                    reqsReg[defSource,yr:] -= repPerc
                elif kp[9] == -2 or kp[9]==-3: #Assign/remove demand from all 
                    srcs = (classflags[srcClass])
                    if kp[9] == -2:
                        srcs[np.argmax(rprops[srcs,0]==kp[0])] = 0 #zero out the base source's data
                    intVal = prefFlipArr(reqsReg[srcs,yr]/reqsReg[srcs,yr].sum(),fleet[srcs,0,5:7].prod(1)) #adjust relevant sources     
                    reqsReg[srcs,yr:] -= repPerc*intVal[:,np.newaxis]/intVal.sum()

        
#Policy limits inclusion - individual sources first, then any remaining group limits

        #Individual source limits block
        for k in range(totalSources):
            if (policyLimits[k,i,0]==1 and reqsReg[k,i]<policyLimits[k,i,1]) or (policyLimits[k,i,0]==2 and reqsReg[k,i]>policyLimits[k,i,1]):
                reqsReg[k,i]=policyLimits[k,i,1]
            if reqsReg[k,i]<0:
                reqsReg[k,i]=0
        
        for j in range(totalClasses):
            reqsReg[classflags[j],i] = reqsReg[classflags[j],i]/reqsReg[classflags[j],i].sum()    
            
                
        #Group-based limits block
        if np.unique(policyLimits[:,i,2]).shape[0]>1: #if there are group-based limits like AEPs
            groupClasses = np.unique(sflags[policyLimits[:,i,2]!=0]) #pull all the classes that have values to be set
            
            for classNum in groupClasses: #go through all classes that have group policies one by one
                #Check to see if the requirements are met - if they are, get rid of the requirement                
                groupFloors = np.unique(policyLimits[classflags[classNum],i,2])
                for floor in groupFloors[1:]: #0 is the null case
                    if reqsReg[np.logical_and(classflags[classNum],policyLimits[:,i,2]==floor),i].sum()>=floor:
                        policyLimits[policyLimits[:,i,2]==floor,i,2] = 0
    
                #Identify those groups that did not meet their floor (if any)
                groupFloors = np.unique(policyLimits[classflags[classNum],i,2])
                if groupFloors.sum()>0: #if there are unmet groups
                    totalSet = groupFloors.sum() #total specified percentage of class
                    reqsReg[np.logical_and(classflags[classNum],policyLimits[:,i,2]==0),i] *= (1-totalSet)/reqsReg[np.logical_and(classflags[classNum],policyLimits[:,i,2]==0),i].sum() #adjust unaffected sources to equal unspecified percentage of class
                    for floor in groupFloors[1:]:
                        tarSrc = np.logical_and(classflags[classNum],policyLimits[:,i,2]==floor)                        
                        if floor/reqsReg[tarSrc,i].sum()>1: #if the total from the sources does not exceed the policy
                            intVal = reqsReg[tarSrc,i]*(prefFlipArr(floor/reqsReg[tarSrc,i].sum()-1,fleet[tarSrc,0,5:7].prod(1))+1) #adjust relevant sources to match total value
                            reqsReg[tarSrc,i] =intVal*floor/intVal.sum()
        


        #Overall renormalization
        for j in range(totalClasses):
            reqsReg[classflags[j],i] = reqsReg[classflags[j],i]/reqsReg[classflags[j],i].sum()    

    #Determine regional annual per-source demand
    for i in range(totalYears):
        for j in range(totalClasses):
            reqsReg[classflags[j],i] = reqsReg[classflags[j],i]*demandReg[j,i]*1e6 #Create per-source regional demand

     

    #At this point, we have a policy-compliant demand requirement for all 
    #sources, and known capacity information - all fixed for the scenario.
    #Remaining information has randomness to it, so we do that in a loop.

#########################################
#Monte Carlo loop
#########################################
    MCATI = np.zeros((trials,totalClasses,totalYears,6,3),dtype='float32')   
    ImpactsReg = np.zeros((totalSources,totalYears,6,3),dtype='float32')
    exGen = np.zeros((totalSources))
    classRegFrac = np.zeros((5,totalYears))
    baseDem = np.zeros((5,1))
    
    
    (LCIAMed,null) = LCAGen(sources,modes,year=0, mode=0)    
    np.savetxt('../Scenarios/'+scenname+'/LCIAMed.csv',np.vstack((LCIAMed[:,:,0],LCIAMed[:,:,1],LCIAMed[:,:,2])),fmt='%.4e',delimiter=',')
    print time.time()-startTime,'Seconds'

    for trial in range(trials): 
    
    
        #Initialize randomly affected variables
        ImpactsReg[:] = 0
        fleetAdj = fleet.copy()
        reqsRegAdj = reqsReg.copy()
        exGen[:] = 0
        classRegFrac[:,:] = 0
        baseDem[:]=0
        
        #add regional data and calculate capacity requirements
        MCACapGen(sources,modes,reqsRegAdj, fleetAdj)
        
        #print time.time()-startTime,'Seconds'
        #LCA Calcs
        (LCIA,colLCA) = LCAGen(sources,modes,year=0,mode=mode)
        baseLU = fleetAdj[:,0,0]*LCIA[:,3,1]    
        
        for yr in range(totalYears):
            
            #Adjust naturally variable sources                
            exGen[:] = 0            
            #Calculate difference between capacity at factor (small annual variations) and reqs
            exGen[fleet[:,0,4]==0] = fleetAdj[fleet[:,0,4]==0,yr,0]*fleetAdj[fleet[:,0,4]==0,yr,1]*8760*np.random.normal(1,.01,((fleet[:,0,4]==0).sum(),1))-reqsRegAdj[fleet[:,0,4]==0,yr]          
            #Calculate random offset for annually varying sources             
            exGen[fleet[:,0,4]==3] = reqsRegAdj[fleet[:,0,4]==3,yr]*np.random.normal(0,.03,(fleet[:,0,4]==3).sum())         
            for cl in range(totalClasses):
                #Sum per-class changes and assign to default
                exGen[np.logical_and(fleet[:,0,4]==2,classflags[cl])] = -exGen[classflags[cl]].sum()
            
            #Adjust all sources for extra generation
            reqsRegAdj[:,yr] += exGen
            
            #Calculate updated LCIA factors
            (LCIA,null) = LCAGen(sources,modes, year=yr,mode=2,colLCA=colLCA) #Get data for the appriopriate year
#            if yr<4:
#                print (reqsRegAdj[1:3,yr],LCIA[1:3,0,0], refEffs[1:3,0]/fleetAdj[1:3,yr,2])
            for imp in range(5):
                ImpactsReg[:,yr,imp,0] = reqsRegAdj[:,yr]*LCIA[:,imp,0]*refEffs[:,0]/(fleetAdj[:,yr,2]) #Generation/O&M Impacts, adjusted for ongoing efficiency
                ImpactsReg[:,yr,imp,1] = fleetAdj[:,yr,3]*LCIA[:,imp,1] #Construction Impacts
                ImpactsReg[:,yr,imp,2] = reqsRegAdj[:,yr]/(fleetAdj[:,imp,2]/refEffs[:,0]+.000001)*LCIA[:,imp,2] #Fuel Impacts
                if imp==3:
                    if yr==0: #Add LU for existing infrastructure to first year, leaving rest of years open for accurate summation or analysis
                        ImpactsReg[:,yr,5,0] = baseLU
                    else:
                        ImpactsReg[:,yr,5,0] = baseLU + ImpactsReg[:,:yr,3,1].sum(1) #Construction Impacts included in ongoing operational land use
            
                for cl in range(totalClasses):
                    MCATI[trial,cl,yr,imp,:] = ImpactsReg[classflags[cl],yr,imp,:].sum(0)
                    if imp==3:
                         MCATI[trial,cl,yr,5,:] = ImpactsReg[classflags[cl],yr,5,:].sum(0)

        #print astr(ImpactsReg[4:9,:5,0,:].sum(2),precision=2)
        MCATI[trial,0,:,:,:] *= ElExports

        for cl in range(5):        
            baseDem[cl] = reqsRegAdj[classflags[cl],0].sum()
        
        
       
        for yr in range(totalYears):
            #Remove GWP from in-region transport from electricity                    
            MCATI[trial,0,yr,0,2] -= np.dot(rprops[classflags[0],1],ImpactsReg[classflags[0],yr,0,2]*.8)
            #Remove GWP from in-region transport from heat                    
            MCATI[trial,2,yr,0,2] -= np.dot(rprops[classflags[2],1],ImpactsReg[classflags[2],yr,0,2]*.8)
            
            AnnElDem = reqsRegAdj[classflags[0],yr].sum()
            AnnElDemMJ = AnnElDem * 3600
            AnnWatDem = reqsRegAdj[classflags[3],yr].sum()    
                       
            #Adjust electricity impacts based on change in water energy intensity
            MCATI[trial,0,yr,:,:] += MCATI[trial,0,yr,:,:]/AnnElDem*.8*(MCATI[trial,3,yr,1,(0,2)]-MCATI[trial,3,0,1,(0,2)]*AnnWatDem/baseDem[3]).sum()/3600                
            #Adjust electricity impacts based on change in wastewater energy intensity
            MCATI[trial,0,yr,:,:] += MCATI[trial,0,yr,:,:]/AnnElDem*.8*(MCATI[trial,4,yr,1,(0,2)]-MCATI[trial,4,0,1,(0,2)]*reqsRegAdj[classflags[4],yr].sum()/baseDem[4]).sum()/3600                
            #Adjust water impacts based on change in electricity water intensity
            MCATI[trial,3,yr,:,:] += MCATI[trial,3,yr,:,:]/AnnWatDem*(MCATI[trial,0,yr,2,(0,2)]-MCATI[trial,0,0,2,(0,2)]*AnnElDem/baseDem[0]).sum()              
            #Adjust water impacts based on change in transport water intensity
            MCATI[trial,3,yr,:,:] += MCATI[trial,3,yr,:,:]/AnnWatDem*(MCATI[trial,1,yr,2,(0,2)]-MCATI[trial,1,0,2,(0,2)]*reqsRegAdj[classflags[1],yr].sum()/baseDem[1]).sum()                
            #Adjust water impacts based on change in heating water intensity
            MCATI[trial,3,yr,:,:] += MCATI[trial,3,yr,:,:]/AnnWatDem*(MCATI[trial,2,yr,2,(0,2)]-MCATI[trial,2,0,2,(0,2)]*reqsRegAdj[classflags[2],yr].sum()/baseDem[2]).sum()                
            
            
            #Move electric vehicle impacts from elec to trans
            MCATI[trial,1,yr,:,:] += MCATI[trial,0,yr,:,:]*reqsRegAdj[14,yr]/AnnElDemMJ
            MCATI[trial,0,yr,:,:] *= 1-reqsRegAdj[14,yr]/AnnElDemMJ                            
            #Move water treatment impacts from elec to water                
            MCATI[trial,3,yr,:,(0,2)] += MCATI[trial,0,yr,:,(0,2)]*.8*MCATI[trial,3,yr,1,0]/AnnElDemMJ                    
            MCATI[trial,0,yr,:,(0,2)] *= 1-.8*MCATI[trial,3,yr,1,0]/AnnElDemMJ
            #Move wastewater treatment impacts from elec to wastewater
            MCATI[trial,4,yr,:,(0,2)] += MCATI[trial,0,yr,:,(0,2)]*.8*MCATI[trial,4,yr,1,0]/AnnElDemMJ
            MCATI[trial,0,yr,:,(0,2)] *= 1-.8*MCATI[trial,4,yr,1,0]/AnnElDemMJ
                
 ###### End of Impacts Calculation   
        
        if np.mod(trial,int(trials/10))==0:
            print '{0}% Complete'.format(100./trials*trial)
            print time.time()-startTime,'Seconds'
        
##########################################
#Process finished data
###########################################
#    print 'Ops v'    
#    print np.array_str(LCIA[:,:,0],precision=2)
#    print 'Const v'
#    print np.array_str(LCIA[:,:,1],precision=2)
#    print 'Fuel v'
#    print np.array_str(LCIA[:,:,2],precision=2)
#    

    

    MCATI.sort(0)

    impClass = np.zeros((totalClasses*6,totalYears),dtype='float32')
    impStage = np.zeros((18,totalYears),dtype='float32')
    
    imp50 = MCATI[int(trials*.5),:,:,:,:].sum(3).sum(0).transpose()
    imp05 = MCATI[int(trials*.05),:,:,:,:].sum(3).sum(0).transpose()
    imp95 = MCATI[int(trials*.95),:,:,:,:].sum(3).sum(0).transpose()
    impRange = np.vstack((imp50,imp05,imp95))
    
    for imp in range(6):
        impClass[imp*5:imp*5+5,:] = MCATI[int(trials*.5),:,:,imp,:].sum(2)
        impStage[imp*3:imp*3+3,:] = MCATI[int(trials*.5),:,:,imp,:].sum(0).transpose()
        
    
    if store==1:
        scenStore(scenname,(fleetAdj,impClass,impRange,impStage,reqsReg))
        
    return ((fleetAdj, impClass,impRange,  impStage,reqsRegAdj), MCATI[:,:,20,:,:].sum(3).sum(1)) #int(trials*.5)])





def MCACapGen(sources, modes, reqsReg, fleet):
        
    
    for yr in range(0,reqsReg.shape[1]):
    
        if yr>0 and (fleet[:,yr,0]!=0).any():
            #First, integrate any known plant data with previous year
            fleet[:,yr,1] = (fleet[:,yr,0]*fleet[:,yr,1]+fleet[:,yr-1,0]*fleet[:,yr-1,1])/(fleet[:,yr,0]+fleet[:,yr-1,0]+.0000001)
            fleet[:,yr,2] = (fleet[:,yr,0]*fleet[:,yr,2]+fleet[:,yr-1,0]*fleet[:,yr-1,2])/(fleet[:,yr,0]+fleet[:,yr-1,0]+.0000001)
            #Source methods adjustment
            for i,m in enumerate(modes):
                for st in m:
                    curModes = fleet[i,yr-1,0]*st[:,yr-1,1] + fleet[i,yr,0]*st[:,yr,1]
                    st[:,yr,1] = curModes/curModes.sum()
                    if curModes.sum()==0:
                        print yr,i,st
            fleet[:,yr,0] += fleet[:,yr-1,0]
        elif yr>0: #if no new capacity exists for any source, just move data forward
            fleet[:,yr,:3] = fleet[:,yr-1,:3]
            for i,m in enumerate(modes):
                for st in m:
                    st[:,yr,1] = st[:,yr-1,1]
            
        
        #Calculate difference between present capacity/generation and necessary
        #supply to meet scenario demands
        potGen = fleet[:,yr,0]*fleet[:,yr,1]*8760
        mismatch = reqsReg[:,yr]-potGen #difference between known generation at given cap fac and necessary generation this year
                
        for sn,s in enumerate(sources):
            
            if mismatch[sn]>0:         
                newMds = np.array([dc.CalcDist(np.hstack((-2,st[:,yr,0])).squeeze()) for st in modes[sn]]).squeeze().astype(int)           
                newCF = s.genCF(newMds[0])
                newEff = s.genEff(newMds[0])
                constMode = s.Modes[1][newMds[1]]
                newGen = mismatch[sn]/(newCF*8760) #per-source extra generation necessary   
                
                if (s.variable==0 and newGen > 0) or newGen > constMode.minCap:
                    if newGen < constMode.minCap:#If available is simply insufficient for non-dispatchables
                        newGen = constMode.minCap
                        
                    newGen = np.ceil(newGen)
                    
                    for k in range(constMode.years):
                        if yr-k >= 0:
                            fleet[sn,yr-k,3] += newGen/constMode.years
    
                    
                    fleet[sn,yr,1] = (fleet[sn,yr,0]*fleet[sn,yr,1]+newGen*newCF)/(fleet[sn,yr,0]+newGen)
                    fleet[sn,yr,2] = (fleet[sn,yr,0]*fleet[sn,yr,2]+newGen*newEff)/(fleet[sn,yr,0]+newGen)
                    
                    for st in range(3):
                        curModes = fleet[sn,yr,0]*modes[sn][st][:,yr,1]
                        curModes[newMds[st]] += newGen
                        modes[sn][st][:,yr,1] = curModes/curModes.sum()
                    
                    fleet[sn,yr,0] += newGen
                    




def LCAGen(sources,mSplit,year=0,mode=1,colLCA=None):
    
    totalSources = len(sources)
    LCIA = np.zeros((totalSources,5,3)) #Final fully collapsed output
    
    if mode==0 or mode==1: #Need to collapse distributions
        colLCA = [s.getLCAEst(mode=mode) for s in sources]        
    
    #loop to collapse options based on regional variations
    for source in range(totalSources):
        for stage in range(3): 
            for imp in range(5):
                LCIA[source,imp,stage] = np.dot(colLCA[source][stage][imp],mSplit[source][stage][:,year,1])

    return (LCIA, colLCA)
    
def prefFlipArr(change, pref):
    out = np.zeros((pref.shape))
    for i in range(pref.shape[0]):    
        if type(change)==np.ndarray:
            if change[i]>0:
                out[i] = change[i]*pref[i]
            else:
                out[i] = change[i]/pref[i]
        else:
            if change>0:
                out[i] = change*pref[i]
            else:
                out[i] = change/pref[i]
                
        if out[i]<-1:
            out[i]=-.99
            
    #print out
    return out
    
def prefFlip(change,pref):
    if change>0:
        out= change*pref
    else:
        out= change/pref
    
    if out<-1:
        out =-.99
    
    return out
    




#Takes a filename and returns the rows as a list of lists. headers are ignored
def csvRead(filename, strCols=1):
    full = np.genfromtxt(filename,delimiter=',',skip_header=1,autostrip=True,dtype=(str))   
    textCols = full[:,:strCols].astype(str)
    dataCols = full[:,strCols:].astype(float)
    return (textCols, dataCols)
    
    
def scenRead(scenname):
    sn = '../Scenarios/'+scenname+'/'+scenname    
    
    (brN,brD) = csvRead(sn+'-basicReqs.csv')
    (null,rpolicy) = csvRead(sn+'-regPolicy.csv')
    (null,rprops) = csvRead(sn+'-regProps.csv')
    (null,rparams) = csvRead(sn+'-regParams.csv')
    (null,knownCap) = csvRead(sn+'-knownPlants.csv',0)
    return (brN,brD,knownCap,rparams,rpolicy,rprops)
    
def scenStore(scenname, scenResults):
    fn = '../Scenarios/'+scenname+'/'

    if not os.path.isdir(fn):
        os.mkdir(fn)
    fleetAdj,impClass,impRange,impStage,reqsReg = scenResults
    np.savetxt(fn+scenname+'-TI.csv',impRange,fmt='%.4e',delimiter=',')
    np.savetxt(fn+scenname+'-Fleet.csv',np.vstack((fleetAdj[:,:,0],fleetAdj[:,:,1],fleetAdj[:,:,2],fleetAdj[:,:,3])),delimiter=',')
    np.savetxt(fn+scenname+'-Reqs.csv',reqsReg,fmt='%.4e',delimiter=',')        
    np.savetxt(fn+scenname+'-ImpClass.csv',impClass,fmt='%.4e',delimiter=',')
    np.savetxt(fn+scenname+'-ImpStage.csv',impStage,fmt='%.4e',delimiter=',')

        
    
    
    
def stateCap(filename, state):
    (plantNames, plantData) = csvRead(filename,3)
    plantTypes = set(plantNames[:,0])
    stateCFs = dict()
    stateCap = dict()
    for fuel in plantTypes:
        stateFuelPlants = np.logical_and(plantNames[:,0]==state,plantNames[:,1] == fuel)
        stateCFs[fuel] = plantData[stateFuelPlants,3].sum()/(plantData[stateFuelPlants,2].sum()*8760)
        stateCap[fuel] = plantData[stateFuelPlants,2].sum()
        
    return (stateCFs, stateCap)
    
            


if __name__ == '__main__':
    startTime = time.time()
    (fleet, impClass,impTI,  impStage,reqs),ImpsAll = main('BAU_PA',100, store=1)
   # (fleet2, impClass2,impTI2,  impStage2,reqs2),ImpsAll2 = main('DES_AZ',10, store=0)
   # (fleet3, impClass3,impTI3,  impStage3,reqs3),ImpsAll3 = main('REN_DES_AZ',10, store=0)

    #(ImpMed, FleetMed, ReqsMed, ImpsAllMed) = main('BAU_PA',100, mode=0)
        
    print time.time()-startTime,'Seconds'
