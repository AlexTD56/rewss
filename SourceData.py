# -*- coding: utf-8 -*-
"""
Created on Tue Jan  1 21:53:30 2013

@author: Alex
"""

import DataClasses as dc
import numpy as np
import copy

##################################
# Begin Electricity Built-ins
##################################
#Units are Ops (/MWh delivered) Const (/MW built) Fuel (/thermal MWh delivered)
def main():
    sources = [dc.Source('Coal',1,.35,.6)]
    sources[0].addOpsMode('Open-Loop',[-4,.4,.6,.8], [-4,.3,.35,.4])
    sources[0].setLCA(0,0,[
            [-4,580,830,1070], #NREL Harmonization
            [33.8,0,0,0], #MJ/MWh, CED based on ecoinvent US plant average sem inf & EVoF
            [1.1356,0,0,0], #m^3/MWh #from EPRI's 400 gal/MWh avg. + ReCiPe evaluation on RFC plants
            [0.39e-9,0,0,0], #km^2/MWh, F&K operations
            [49,0,0,0]]) #EIA Fixed O&M + Interest @7%,30yrs
    sources[0].addConstMode('Pulverized',4,500)
    sources[0].setLCA(1,0,[
            [-5,224134,50011,0],# #kg CO2-eq/MW cap, estimated from NG
            [-4,3.29e6,2.13e6,5.16e6],# #MJ/MW
            [-5,2268,623,0],# #m^3/MW  needs checking
            [-4,0.002904,.00118,.00679],# #km^2/MW, F&K based on 1000MW in 500acres (avg of their values)
            [-3,2.8e6,3.2e6,0]])# #$/MW installed, EIA Overnight capital costs from AEO 2011
    sources[0].addFuelMode('Surface')
    sources[0].setLCA(2,0,[
            [150,0,0,0],
            [247,0,0,0],
            [.08395,0,0,0],
            [-4,400e-9,43e-9,840e-9], ##F&K based on 35# CU
            [5,0,0,0]]) #EIA Fixed O&M + Interest @7%,30yrs
    sources[0].addFuelMode('Underground')
    sources[0].setLCA(2,1,[90,0,3.23e-5,0],0) #Water from Harvard Study
    sources[0].setLCA(2,1,[-4,67e-9,2.3e-9,200e-9],3)
    sources[0].addOpsMode('Closed-Loop',[-4,.2,.5,.8], [-4,.35,.3,.4])
    sources[0].setLCA(0,1,[1.817],2)  
    
    sources.append(dc.Source('Natural Gas',1,.35,.35, v=2))
    sources[1].addOpsMode('CT',[-4,.15,.35,.8], [-4,.38,.3,.45])
    sources[1].setLCA(0,0,[
            [500,0,0,0], #kg/MWh, data from Jaramillo
            [48.4,0,0,0], #MJ/MWh, CED based on ecoinvent US plant average sem inf
            [-3,.681,1.13,0], #EPRI, range covering NGCC to CT with towers
            [30/1e9,0,0,0], #km^2/MWh, F&K (needs assumptions checked)
            [28,0,0,0]]) #EIA Fixed O&M + Interest @7%,30yrs
            #,0.379,1.817 for water alternatives
    sources[-1].addOpsMode('Closed-Loop',[-4,.2,.5,.8], [-4,.35,.3,.4])
    sources[-1].setLCA(0,1,[-3,1.1356,1.817,0],2)    
    sources[1].addConstMode('CT', 3, 100)
    sources[1].setLCA(1,0,[
            [-5,4.74e4,1.76e4,0], #kg CO2-eq/MW, ecoinvent 300MWe plant
            [-5,5.59e6,2.2e5,0], #MJ/MW, ecoinvent 300MWe plant + CED 1.08
            [-5,281,76.7,0], #m^3/MW, ecoinvent 300MWe plant + ReCiPe H2O depletion
            [0.001023,0,0,0], #km^2/MW, F&K inference
            [-4,665e3,927e3,1003e3]]) #EIA Study   
    sources[1].addFuelMode('pipeline')
    sources[1].setLCA(2,0,[
            [93.2,0,0,0],
            [180,0,0,0], #Based on EROI of 20:1
            [-4,0.037,0.018,0.054],
            [240e-9,0,0,0],
            [-5,3.8,.2,0]])   
    sources[1].addFuelMode('Marcellus')
    sources[1].setLCA(2,1,[
            [-4,117,129,240], #Our Study, 37% efficient
            [-4,180,197.3,900], #Our study, 90% confidence
            [-4,0.028,0.057,0.117],#Harvard study
            [120e-9,0,0,0]],0) #500km of pipeline
        
        
        #Oil
    sources.append(dc.Source('Oil',1,.35,.35))
    sources[2].addOpsMode('CT',[-4,.1,.35,.4],[-4,.3,.35,.4])
    sources[2].addConstMode('CT',3,100)
    sources[2].addFuelMode('Pipeline')
    sources[2].setLCA(0,0,[
            [700,0,0,0], #kg/MWh, data from Jaramillo
            [630,0,0,0], #MJ/MWh, CED based on ecoinvent US plant average sem inf
            [-3,0.681,1.136,0], #EPRI, range covering NGCC to CT with towers
            [30/1e9,0,0,0], #km^2/MWh, F&K (needs assumptions checked)
            [30,0,0,0]]) #EIA Fixed O&M + Interest @7%,30yrs      
    sources[-1].addOpsMode('Closed-Loop',[-4,.2,.5,.8], [-4,.35,.3,.4])
    sources[-1].setLCA(0,1,[-3,1.136,1.817,0],2)    
            
    sources[2].setLCA(1,0,[
            [5e4,0,0,0], #kg CO2-eq/MW, estimated from NG
            [-5,7.56e5,2.2e5,0], #MJ/MW, ecoinvent 300MWe plant + CED 1.08
            [287,0,0,0], #m^3/MW, ecoinvent 300MWe plant + ReCiPe H2O depletion
            [0.001023,0,0,0], #km^2/MW, assumed same as NG from F&K
            [-4,665e3,974e3,1003e3]]) #EIA Study (No one will build an oil fired plant)
    
    sources[2].setLCA(2,0,[
            [93,0,0,0], #assume same as NG
            [328,0,0,0],
            [-4,0.9e-3,1.1e-3,1.3e-3],
            [0,0,0,0],
            [-5,27.73,1,0]])#estimates based on 75-91 $/bbl and .30 reference efficiency
        
        #Nuclear
    sources.append(dc.Source('Nuclear',1,.35,.85))
    sources[3].addOpsMode('Closed-Loop',[-4,.7,.85,.95],[.97,0,0,0])    
    sources[3].setLCA(0,0,[
            [-4,8,4,15], #kg/MWh, from F&K, baseline matches with Hondo
            [23,0,0,0], #MJ/MWh, CED based on ecoinvent PWR sem inf and fuel
            [-5,2.725,.15,0], #m^3/MWh 400-720gal/MWh from EPRI
            [5/1e9,0,0,0], #km^2/MW, F&K, no fuel disposal
            [69,0,0,0]]) #$/MWh operations, via PNE Nuclear - 5000/kW, 10# discount
    sources[3].addOpsMode('Open-Loop',[-4,.7,.85,.95],[.97,0,0,0])
    sources[3].setLCABase(0,1,[1.514],2)    
    sources[3].addConstMode('Normal',10,1200)
    sources[3].setLCA(1,0,[
            [-4,6.64e5,2.97e5,9.978e5], # Converted from F&K using 40yrs and .85
            [-5,1.13e7,4.98e6,0], #MJ/MW, ecoinvent 1000MWe PWR, US case
            [3460,0,0,0], #m^3/MW, ecoinvent 1000MWe PWR, US case
            [-4,0.00211,.00106,.00413], #km^2/MW, Angra 3 (benefits of shared inf.) F&K value of 0.016
            [-3,4.6e6,6e6,0]]) #$/MW installed, EIA overnight costs with range from PNE    
    sources[3].addFuelMode('Diffusion')
    sources[3].setLCA(2,0,[
            [-4,15,11,27], #F&K range
            [129,0,0,0], #CED for 1MWh worth of fuel from ecoinvent
            [-4,.351,.185,.517], #Harvard Study
            [(30+10+3)/1e9,0,0,0], #F&K Mining and milling/GWh
            [6.68,0,0,0]]) #NEI/DOE data       
    sources[3].addFuelMode('Centrifuge')
    sources[3].setLCABase(2,1,[32,0,0,6.8],1)
        
        #Hydro - combination of US and BR data
    sources.append(dc.Source('Hydro',1,refCF=.55, v=3))
    sources[-1].addFuelMode('Default')
    sources[4].addOpsMode('Boreal',[-4,.4,.55,.7],[.97,0,0,0])
    sources[4].addConstMode('Boreal',5,1000)
    sources[4].setLCA(0,0,[
            [-5,11.48,1.2,0],  #-4,29,4.3,77 kg/MWh, data from Fearnside and Rosa, 10# SD for uncertainty
            [0.54,0,0,0], #MJ/MWh, CED based on ecoinvent US plant average sem inf
            [-5,2.62,1,0], #m^3/MWh
            [0,0,0,0], #km^2/MW
            [42+2.5,0,0,0]]) #EIA Fixed O&M + Interest @7%,30yrs, + Variable O&M  
    sources[4].setLCA(1,0,[
            [3.91e6,0,0,0], #kg CO2-eq/MW cap, based on Ribeiro LCI for Itaipu 6.9e5 for Chinese EIO-LCA based study
            [-5,1.52e7, 1e6,0], #MJ/MW, ecoinvent non-alpine dam (at 2500MW avg.), median Chinese, low Ribeiro, high ecoinvent
            [9682,0,0,0], #m^3/MW, ecoinvent non-alpine (@2500MW avg.), large wet gravel usage accounts for 63# of original
            [-5,0.3672,0.035,0], #km^2/MW weighted average of 23 BR Dams - Scenario_Data
            [-5,2.347e6,1e5,0]]) #$/MW installed, EIA Overnight costs
    
        #Biomass - Brazilian Data right now
    sources.append(dc.Source('Biomass',1,.35,.35, v=3))    
    sources[5].addOpsMode('Upgrade',[-4,.2,.35,.5],[-3,.18,.25,0])
    sources[5].addConstMode('Upgrade',2,50)
    sources[5].setLCA(0,0,[
            [25,0,0,0], #kg/MWh, Arguments of allocation from Seabra, 25 in JEPO 2011, 7 from van den Broek
            [140,0,0,0], #MJ/MWh, 140 based on Mauritius study (about x2 NG from CED in ecoinvent)
            [-3,1.158,1.817,0], #From EPRI's 400gal/MWh avg. (224 for Mauritius, but that is likely irrigated)
            [9.16e-6,0,0,0], #from F&K (land is occupied even if it's not consumed) (.00203 from Mauritius - allocation?)
            [133,0,0,0]]) #$/MWh operations, Seabra & Macedo, allocated based on value of products
        
    sources[5].setLCA(1,0,[
            [4e4,0,0,0],
            [1e6,0,0,0],
            [300,0,0,0],
            [0.00203,0,0,0], #(.00203 from Mauritius - allocation?)
            [-4,100e3,200e3,700e3]])# USDA TechLine    
    sources[5].addConstMode('New',3,50)
    sources[5].setLCA(1,1,[[-5,3.86e6,1e5,0]],4) #EIA overnight costs
    sources[5].addFuelMode('Wood')
    sources[5].setLCA(2,0,[
            [-3,48,54,0], #JEPO 2011
            [-1,np.log(10**2.0901),.25,0],
            [0,0,0,0], #Assumption that it's not irrigated
            [-4,1.43e-7,2.14e-7,4.29e-7], #FromUSFS study - White, 2010 
            [5,0,0,0]]) #Varible O&M from EIA
        
    #Wind: impacts per turbine (/MW direct), with number of turbines
    #required coming from the interaction of scenario requirements.
    sources.append(dc.Source('Wind',1,refCF=.35,v=0))    
    sources[-1].addFuelMode('Default')
    sources[6].addOpsMode('Onshore',[-4,.25,.32,.40],[.97,0,0,0])
    sources[6].addOpsMode('Offshore',[-4,.35,.45,.5],[.97,0,0,0])
    sources[6].addConstMode('Onshore',1,10)
    sources[6].setLCA(0,0,[
            [-4,1.3,.12,6.7], #kg/MWh
            [4,0,0,0], #MJ/MWh, CED based on ecoinvent 800kW plant average sem inf
            [0,0,0,0], #m^3/MWh
            [0,0,0,0], #km^2/MW
            [73,0,0,0]]) #$/MWh, Investment costs from PNE for hydro at 10# discount. Itaipu contract in 2009 is 113, but operations costs via INL are $7/MWh
    sources[-1].setLCABase(0,1,[173],4)
    
    sources[6].setLCA(1,0,[
            [-4,620000,190000,2300000], #kg CO2-eq/MW, offshore from ecoinvent, needs more wires
            [-5,5.2e6,1e5,0], #MJ/MW, onshore from Lenzen & Wachsmann (BR)
            [8.08e3,0,0,0], #m^3/MW, onshore (2MW) from ecoinvent, ReCiPe
            [-4,0.15,.2,.25], #km^2/MW, from NREL estimates of 5MW/km2
            [-4,2e6,2.4e6,2.8e6]]) #$/MW installed, http://www.nrel.gov/docs/fy12osti/53510.pdf
    sources[-1].addConstMode('Offshore',2,40)
    sources[-1].setLCA(1,1,[
            [-4,620000,190000,2300000],
            [-5,9.72e6,1e5,0],
            [14.04e3,0,0,0],
            [0,0,0,0],
            [-4,3.59e6,4.25e6,5.9e6]]) #ARUP report on future costs
        
        #Solar
        #7.19 $/MWh for hybrid plant
      
    sources.append(dc.Source('Solar',1,refCF=.35,v=0))  
    sources[-1].addFuelMode('Default')
    sources[-1].addOpsMode('PV',[-4,.18,.12,.22],[.97,0,0,0])
    sources[-1].addOpsMode('CST0',[-4,.30,.25,.35],[-4,.37,.32,.39])
    sources[7].addOpsMode('CST6',[-4,.45,.4,.5],[-4,.37,.32,.39])
    sources[7].addOpsMode('CST12',[-4,.60,.5,.65],[-4,.37,.32,.39])
    sources[-1].addConstMode('PV',1,0.05)
    sources[-1].addConstMode('CST',2,1)
    sources[7].addConstMode('CST6',2,1)
    sources[7].addConstMode('CST12',2,1)

    ##CST Data
    sources[-1].setLCA(0,'CST',[
            [10.55,0,0,0], #kg/MWh
            [156,0,0,0], #MJ/MWh, CED based on ecoinvent US plant average sem inf
            [4.17,0,0,0], #m^3/MWh CST
            [0,0,0,0], #km^2/MW
            [143,0,0,0]]) #$/MWh
    sources[-1].setLCA(1,'CST',[
            [1.29e6,0,0,0], #kg CO2-eq/MW, Heath
            [2.13e7,0,0,0], #MJ/MW
            [4.32e4,0,0,0], #m^3/MW
            [0.00926,0,0,0], # From NREL paper by Denholm and Margolis, at 70W/m^2 including spacing for roads
            [-5,4.7e6,2e5,0]]) #$/MW installed, PDE wind section (2000 costs adjusted by US CPI)

    #PV Data
    sources[7].setLCA(0,'PV',[
            [2,0,0,0], #kg/MWh
            [0,0,0,0], #MJ/MWh, CED based on ecoinvent US plant average sem inf
            [0.12,0,0,0], #m^3/MWh PV
            [0,0,0,0], #km^2/MW
            [129,0,0,0]]) #$/MWh, Investment costs from PNE for hydro at 10# discount. Itaipu contract in 2009 is 113, but operations costs via INL are $7/MWh 
    sources[7].setLCA(1,'PV',[
            [-1,6.2227,1,0], #kg CO2-eq/MW, Based on NREL Harmonization & SimaPro
            [-5,3.23e7,1e6,0], #MJ/MW
            [-3,236,1971,0], #m^3/MW
            [0.014,0,0,0], # From NREL paper by Denholm and Margolis, at 70W/m^2 including spacing for roads
            [-5,4.8e6,2e5,0]]) #$/MW installed, EIA Overnight Cost
        
    
    sources[7].setLCABase(1,'CST6',[1.7e6,2.71e7,6.25e4])
    sources[7].setLCABase(1,'CST12',[2.12e6,3.29e7,8.18e4])
    sources[7].setLCABase(0,'Hybrid',[7.19],4)
    
    sources.append(dc.Source('Geothermal',1,refCF=.8,v=0))
    sources[-1].addFuelMode('Default')
    sources[-1].addOpsMode('Standard',[-4,.7,.8,.9],[.97,0,0,0])
    sources[-1].setLCA(0,0,[
            [-3,50,70,0],
            [141,0,0,0],
            [-3,1.136,1.817,0],
            [0,0,0,0],
            [54,0,0,0]]) #EIA Fixed O&M + Interest @7%,30yrs + variable O&M
    sources[-1].addConstMode('Standard',1,10)
    sources[-1].setLCABase(1,0,[4.141e6],4)
    sources[-1].setLCA(1,0,[-4,.84,1.16,1.69],3)
    
    #######################################
    # End of Electricity Built-ins
    #
    # Start of Transport Built-ins 
    #TODO split transit into passenger and freght?
    #######################################
    # Units are Ops (/MJ delivered) Const (/MJ/hr built) Fuel (/MJ delivered)
    # Reference efficiency for all sources is 4.71 MJ/km (8.06 MJ/hr for a 15k 
    # driving cycle, and 17.09 mi/gge), which is assigned a
    # capacity factor of 1. This excludes air and rail transport, which
    # account for ~10% of total energy.
    
    sources.append(dc.Source('Petroleum',2, v=2))
    sources[-1].addOpsMode('ICE',[-4,.542,.62,.72],[.97,0,0,0]) #Cfs for 31.5, 27.5 (CAFE), and 23.5 (CAFE trucks)
    sources[-1].setLCABase(0,0,[.074,0.0753,0,0,.015]) #gwp, CED from Notter ES&T
    sources[-1].addConstMode('ICE',1,5) #5 MJ/hr is energy requirement for 30mpg car at 10k miles/yr
    sources[-1].setLCABase(1,0,[1360,24600,0,0,3350]) #GWP & Energy data from NOtter, ES&T 2010
    sources[-1].setLCA(1,0,[-4,12.925,15.6,20.725],2) #Based on Volkswagon figures and 5 MJ/hr    
    sources[-1].addOpsMode('Hyb',[-4,.33,.542,.62],[1.3,0,0,0]) #1.3 on efficiency to account for less gasoline usage
    sources[-1].addConstMode('Hyb',1,2.63)
    sources[-1].setLCABase(1,1,[5990,27200,0,0,3450]) #GWP & Energy data from NOtter, ES&T 2010
    sources[-1].addFuelMode('Conventional US')
    sources[-1].setLCABase(2,0,[.0205,.233,2.9e-5,2e-10]) #GREET, Scown
    sources[-1].setLCA(2,0,[-5,.016,.003,0],4)
    
    sources.append(dc.Source('Ethanol',2, v=3))
    sources[-1].addOpsMode('ICE',[-4,.542,.62,.72],[.97,0,0,0])
    sources[-1].setLCABase(0,0,[.073,0.075,0,0,.018]) #Greet cost from $2000/yr operating costs for car
    sources[-1].addConstMode('ICE',1,3.828)
    sources[-1].setLCABase(1,0,[1360,24600,0,0,3350])
    sources[-1].setLCA(1,0,[-4,12.925,15.6,20.725],2) #Based on Volkswagon figures and 5 MJ/hr    
    sources[-1].addFuelMode('Corn')
    sources[-1].setLCA(2,0,[
            [-.0084,0,0,0],
            [-3,1.08,1.38,0],
            [-4,3.0e-4,4.1e-3,1.4e-2],
            [-5,1.25e-7,1.9e-8,0],
            [0.023,0,0,0]],0) #Greet
    
    sources.append(dc.Source('Biodiesel',2, v=3))
    sources[-1].addOpsMode('ICE',[-4,.542,.62,.72],[.97,0,0,0])
    sources[-1].setLCABase(0,0,[.072,0.075,0,0,.018])
    sources[-1].addConstMode('ICE',1,3.828)
    sources[-1].setLCABase(1,0,[1360,24600,0,0,3350])
    sources[-1].setLCA(1,0,[-4,12.925,15.6,20.725],2) #Based on Volkswagon figures and 5 MJ/hr    
    sources[-1].addFuelMode('Soybean')
    sources[-1].setLCABase(2,0,[-.0054,.35],0) #Greet for GWP, energy from Mulder
    sources[-1].setLCA(2,0,[
            [-3,2.2e-2,3.4e-2,0], #Mulder 2009
            [-5,3.3e-7,1.2e-8,0],#Dominguez-Faus 2009
            [0.0178,0,0,0]],2) #Greet cost

    sources[-1].addFuelMode('Soybean-NoIrr')
    sources[-1].setLCA(2,1,[-3,2.2e-4,3.4e-4,0],2) #Mulder 2009/100
            
    sources[-1].addFuelMode('Algae')
    sources[-1].setLCA(2,2,[
            [-4,.156,.3,.56], #Sander + Mulder, system expansion
            [-3,.033,.036,0], #Guieysse 2013, WF = water demanded. Yes, it's ridiculously high
            [-5,2.5e-8,.2e-8,0]],1)
    
    sources.append(dc.Source('CNG',2))
    sources[-1].addOpsMode('ICE',[-4,.542,.62,.72],[.95,0,0,0])
    sources[-1].setLCABase(0,0,[.058,0.075,0,0,7.8e-3]) #Energy from GREET
    sources[-1].addConstMode('ICE',1,3.828)
    sources[-1].setLCABase(1,0,[1360,24600,0,0,3450]) #TODO assumed similar as gasoline for construction
    sources[-1].setLCA(1,0,[-4,12.925,15.6,20.725],2) #Based on Volkswagon figures and 5 MJ/hr    
    sources[-1].addFuelMode('Conventional US')
    sources[-1].setLCABase(2,0,[.028,.177,0,2.67e-11,0]) 
    sources[-1].setLCA(2,0,[-4,2.3e-3,4.7e-3,7.6e-3],4) #cost is origin-blind
    sources[-1].addFuelMode('Marcellus')
    sources[-1].setLCABase(2,1,[.0137,.177,5.02e-6],0)
    
    sources.append(dc.Source('Hydrogen',2))
    sources[-1].addOpsMode('ICE',[-4,.542,.62,.72],[1.2,0,0,0])
    sources[-1].setLCABase(0,0,[.001],0)
    sources[-1].addConstMode('ICE',1,3.828)
    sources[-1].setLCABase(1,0,[1360,24600,0,0,3600]) # Costs from RAND study
    sources[-1].setLCA(1,0,[-4,12.925,15.6,20.725],2) #Based on Volkswagon figures and 5 MJ/hr    
    sources[-1].addFuelMode('Conventional US')
    sources[-1].setLCABase(2,0,[.142,.820,7.27e-4,0,.0272]) #cost data in operation, GWP,CED from GREET
    
    sources.append(dc.Source('Electric',2))
    sources[-1].addOpsMode('Elec',[-4,.15,.17,.2],[1.2,0,0,0])
    sources[-1].setLCABase(0,0,[.001],0)
    sources[-1].addConstMode('ICE',1,3.828)
    sources[-1].setLCABase(1,0,[1360,24600,0,0,3600]) # Costs from RAND study
    sources[-1].setLCA(1,0,[-4,12.925,15.6,20.725],2) #Based on Volkswagon figures and 5 MJ/hr    
    sources[-1].addFuelMode('Default')
    
    
    
    #######################################
    # End of Transport Built-ins
    #
    # Start of Heating Built-ins
    #######################################
    # Heating differentiated using capacity factor normalized by a reference unit
    # with 80% AFUE as a national average. Seasonal effects can be ignored - we're comparing capacity 
    # based on a power level from an annual average. Unlike electricity and 
    # transport, no simple metric for the service provided exists,, so we use 
    # capacity factor to transform efficiency into th operational side
    #Units are: Ops (/MJ delivered) Const (/MJ/hr built) Fuel (/MJ produced)
    
     
    sources.append(dc.Source('Coal',3))
    sources[-1].addOpsMode('Combustion',[1,0,0,0],[.99,0,0,0])
    sources[-1].setLCABase(0,0,[.089,0,0,0,.0045]) #EIA coal costs
    sources[-1].addConstMode('Furnace',1,1) #arbitrarily low mincap
    sources[-1].setLCABase(1,0,[4.22,76,31,0,63.19]) #TODO Same as NG for now
    #TODO get coal furnace data
    sources[-1].addFuelMode('Surface')
    sources[-1].setLCABase(2,0,[0.0145,.024,8.16e-6,400e-13,.0039])
    sources[-1].addFuelMode('Underground')
    sources[-1].setLCABase(2,1,[.0087,.024,8.16e-6,67e-13,.0039])
    
    
    sources.append(dc.Source('Natural Gas',3, v=2))
    sources[-1].addOpsMode('Combustion',[-4,.84,.9,1],[.99,0,0,0]) #boiler or furnace, Ries
    sources[-1].setLCABase(0,0,[.0504,0,0,0,.0085]) 
    sources[-1].addConstMode('Furnace',1,1) #arbitrarily low mincap
    sources[-1].setLCABase(1,0,[4.22,76,31,0,63.19])
    sources[-1].addFuelMode('Conventional US')
    sources[-1].setLCABase(2,0,[.009,.065,0,2.67e-11,0])
    sources[-1].setLCA(2,0,[-5,5.72e-3,1.35e-3,0],4) #EIA Costs - 2010 average, stdev from 2006-2011
    sources[-1].addFuelMode('Marcellus')
    sources[-1].setLCABase(2,1,[0.0137,0.065,5.02e-6],0)
    
    
    sources.append(dc.Source('Oil',3))
    sources[-1].addOpsMode('Combustion',[-4,.84,.9,1],[.99,0,0,0])
    sources[-1].setLCABase(0,0,[.0706,0,0,0,.008]) 
    sources[-1].addConstMode('Furnace',1,1) #arbitrarily low mincap
    sources[-1].setLCABase(1,0,[4.22,76,31,0,63.19]) #Ecoinvent w/ CED and BEES 
    sources[-1].addFuelMode('Conventional')
    sources[-1].setLCABase(2,0,[0.02,.208,.00027,2e-14,0])
    sources[-1].setLCA(2,0,[-5,.016,.003,0],4)
    
    sources.append(dc.Source('Biomass',3, v=3))
    sources[-1].addOpsMode('Combustion',[-4,1,1.1,1.6],[.97,0,0,0])
    sources[-1].setLCABase(0,0,[.0682,0,0,0])  #Modeled as identical to natral gas during combustion
    sources[-1].addConstMode('Furnace',1,1000)
    sources[-1].setLCABase(1,0,[4.22,76,31,0,190]) #USDA TechLine article
    sources[-1].addFuelMode('Woody Biomass')
    sources[-1].setLCABase(2,0,[-.0582,0,0,0,.0041]) #Modeled as identical to natural gas but negative, coproduct for land use
    sources[-1].setLCA(2,0,[-4,4.0e-11,5.9e-11,1.2e-10],3)
    
    #######################################
    # End of Heating Built-ins
    #
    # Start of Water Built-ins
    #######################################
    
    
    sources.append(dc.Source('Water-Surface',4, v=3))
    sources[-1].addOpsMode('Basic-Tmt',[-4,.85,.95,1],[.98,0,0,0])
    sources[-1].setLCABase(0,0,[0,1.22,0,0,.30]) #Cost from B. of Rec. WaTER model, assumed 1% loss
    sources[-1].addOpsMode('Adv-Tmt',[-4,.85,.95,1],[.98,0,0,0])
    sources[-1].setLCABase(0,1,[1.34,0,0,.39],1) #10% higher than baic
    sources[-1].addOpsMode('Non-Drinking',[-4,.5,.8,1],[.98,0,0,0])
    sources[-1].setLCABase(0,2,[.1684,0,0,.01],1) #EPRI for IW
    sources[-1].addConstMode('WW Plant',4,80) 
    sources[-1].setLCA(1,0,[ #Assumed same as WWTP
                [-4,26915,38771,39892], #Simapro range for different classes
                [3.69e5,0,0,0],
                [391,0,0,0],
                [2.07e-6,0,0,0],
                [50,0,0,0]])
    sources[-1].addConstMode('Non-Drinking',2,10)
    sources[-1].setLCABase(1,0,[3880,3.69e4,39,0,5]) #Assumed 10% of full plant
    sources[-1].addFuelMode('Surface')
    sources[-1].setLCABase(2,0,[0,.116,0,2e-8,0])
    
    sources.append(copy.deepcopy(sources[-1]))    
    sources[-1].name='Water-Ground'
    sources[-1].variable = 2
    sources[-1].Modes[2][0].name ='Ground'
    sources[-1].setLCABase(2,'Ground',[.3996],1)
    
    sources.append(copy.deepcopy(sources[-2]))   #skipping groundater to avoid default flag  
    sources[-1].name='Water-Import'
    sources[-1].variable = 1
    sources[-1].Modes[2][0].name ='Import'
    sources[-1].setLCABase(2,'Import',[.05],2) #4000 kWh/af - CAP values
    sources[-1].setLCA(2,'Import',[-4,8.76,11.67,14.6],1)
    sources[-1].setLCA(2,'Import',[-3,.243,.405,0],4) #Shannon 2007 via Voinov
    
    sources.append(copy.deepcopy(sources[-1]))    
    sources[-1].name='Water-Desal'
    sources[-1].Modes[2][0].name ='Desal'
    sources[-1].setLCABase(2,'Desal',[3.89],0)
    sources[-1].setLCA(2,'Desal',[
                [-4,10.4,12.,15.9],
                [-3,.1,.3,0], #arbitrary, interesting assumpion here - fits better for impaired but renewable sources in AZ
                [2e-7,0,0,0],
                [-4,.486,.583,.648]],1)
    

    
    
    
    #######################################
    # End of Water Built-ins
    #
    # Start of Wastewater Built-ins
    #######################################
    
    sources.append(dc.Source('WW-Trickling',5))
    sources[-1].addOpsMode('Plant',[-4,.75,.85,.95],[.98,0,0,0]) #boiler or furnace, Ries
    sources[-1].setLCA(0,0,[
                [-4,.95,1.05,1.11], #FIXME Source??
                [-4,0.64,0.81,1.72]]) #EPRI
    sources[-1].setLCABase(0,0,[1e-2,0,.11],2) #assumed 1% evaporation/solids loss
    sources[-1].addFuelMode('Default')
    sources[-1].addConstMode('WW Plant',4,80) #Mincap in m^3/hr (~.5MGD)
    sources[-1].setLCA(1,0,[
                [-4,26915,38771,39892],
                [3.69e5,0,0,0],
                [391,0,0,0],
                [2.07e-6,0,0,0],
                [50,0,0,0]])
    
    
    
    sources.append(copy.deepcopy(sources[-1]))
    sources[-1].name = 'WW-Aerated'
    sources[-1].setLCA(0,0,[-4,.979,1,2.13],1) ##epri
    sources[-1].setLCABase(0,0,[.5],4) #Cost data averaged from PA utilities
    sources[-2].setLCABase(1,0,[100],4)
    
    sources.append(copy.deepcopy(sources[-1]))
    sources[-1].name = 'WW-Adv-NoDeN'
    sources[-1].setLCA(0,0,[
                [-4,1.844,2.094,2.251],
                [-4,1.13,1.23,2.47]]) ##epri
    sources[-1].setLCABase(0,0,[1.14],4) #Cost data averaged from PA utilities
    sources[-1].setLCABase(1,0,[150],4)
    
    sources.append(copy.deepcopy(sources[-1]))
    sources[-1].name = 'WW-Adv-DeN'
    sources[-1].setLCA(0,0,[-4,1.48,1.52,2.81],1) ##epri
    sources[-1].setLCABase(0,0,[1.5],4) #Cost data averaged from PA utilities
    sources[-1].setLCABase(1,0,[210],4)
    
    return sources
    
    
def addSource(sources,name,classFlag,refEff=.97,v=1):
    sources.append(dc.Source(name,classFlag,refEff,v))
    sources[-1].addOpsMode('Default',[1,0,0,0],[1,0,0,0])
    sources[-1].addConstMode('Default',1,1)
    sources[-1].addFuelMode('Default')
    
if __name__=='__main__':
    sources = main()     
    for n in sources:
        print n.name
        for stages in n.Modes:
            for m in stages:
                print m.name
        print ''
        