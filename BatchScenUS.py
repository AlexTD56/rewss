# -*- coding: utf-8 -*-
"""
Created on Sun Jan 27 17:03:56 2013

@author: Alex
"""

import ScenModelUS as smUS
import numpy as np
import time

def main(scenname, setCode, trials):
    print 'Starting', scenname
    startTime=time.time()
    
    if scenname.find('_')>2:
        regCode = scenname[-2:]
    else:
        regCode = scenname[:2]
    
    scenData = smUS.scenRead(scenname)
    #tuple order: brN,brD,knownCap,rparams,rpolicy,rprops
    scenData += scenname,    
    rprops = scenData[5].copy()
    
    #Base run
#    scenResults,MCATI = smUS.main(scenData,trials)
#    smUS.scenStore(regCode+'_'+setCode,scenResults)

    amped = rprops[:,6]>1 #Pick only amped values
    scenData[5][:,6] = 1
    scenData[5][amped,6] = rprops[amped,6]
    scenResults,MCATI = smUS.main(scenData,trials)
    smUS.scenStore(regCode+'_'+setCode+'A',scenResults)  
    
    damped = rprops[:,6]<1 #Pick only dampened values
    scenData[5][:,6] = 1
    scenData[5][damped,6] = rprops[damped,6]
    scenResults,MCATI = smUS.main(scenData,trials)
    smUS.scenStore(regCode+'_'+setCode+'D',scenResults) 
    
    scenData[5][:,6] = rprops[:,6] #Reset to original values
    
    
    trialsTI = np.zeros((60,26))    
    
    for i in range(1,10):
        #BAU Scen        
        if 'MSH' in setCode:
            scenData[5][(1,12,15),6] = i #MS Scen
            scenData[5][(0,2,9,10,11,15,17),6] = 1./i
        
        if 'DES' in setCode:
            scenData[5][22,6] = i #DES Scen
            
        if 'REN' in setCode or 'BAU' in setCode:
            scenData[5][4:9,6] = i  #REN scen
            scenData[5][(14,18),6] = i #EVs and Biomass heat
            scenData[5][(0,1,2,9,12,15,17),6] = 1./i
            if i>2:            
                scenData[5][(10,11,16),6] = 1./(i-1)
        
        print 'Trial '+str(i)+' Running!'
        scenResults,MCATI = smUS.main(scenData,trials)
        trialsTI[i*6:i*6+6,:] = scenResults[2][0:6,:]
        
    smUS.scenStore(regCode+'_'+setCode+'Opt',(scenResults[:2]+ (trialsTI,) + scenResults[3:]))
    
    print 'Finished!'
    print time.time()-startTime, 'Seconds'
    
    
    
if __name__ == '__main__':
    #main('Old_AZ','Old',6500)
    #main('Old_PA','Old',6500)
#    main('BAU_PA','BAU',6500)    
 #   main('BAU_AZ','BAU',6500)        
    main('DES_AZ','DES',2500)
    main('REN_DES_AZ','REN_DES',2500)
    main('MSH_PA','MSH',2500)
    main('REN_PA','REN',2500)

    #main('BAU_RFC_PA','BAU_RFC',1000)
#    main('BAU_WECC_AZ','BAU_WECC',1000)