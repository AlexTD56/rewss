This software is provided as-is, with no guaranteed support or assistance in use. Questions may be directed to alexander.t.dale@gmail.com, but no guarantee of response is given. 

DataClasses.py holds the basic class data structures
SourceData.py uses the basic data structures to generate a list of Source objects and populate them with LCA data (embedded in the file)
ScenModelUS.py is the primary model code, which runs SourceData.main to generate the set of sources and data, reads in csv files to specify a scenario, and outputs a tuple of results. 
BatchScenUS.py is a wrapper for ScenModelUS that is used to run variations on a basic scenario. It also provides an example of embedding the model in other scripts.

All necessary csv files can be generated from a single Numbers spreadsheet, and the included BAU_PA.numbers is provided as an example, as well as BAU_PA.xls (BAU_PA.pdf is provided as a visual example for those that do not have Numbers installed). 

This software was developed using Spyder as an interactive frontend, which is available for free for both Windows and Macintosh platforms. 

Journal papers describing the model are in submission, and this work should be cited as (titles tentative pending review):

Dale, A. T.; Bilec, M. M., The Regional Energy and Water Supply Scenarios (REWSS) Model, Part I: Framework, Procedure, and Validation. Sustainable Energy Technology & Assessments (In Preparation) 2013.

Dale, A. T.; Bilec, M. M., The Regional Energy and Water Supply Scenarios (REWSS) Model, Part II: Case Studies in Pennsylvania and Arizona. Sustainable Energy Technology & Assessments (In Preparation) 2013.


Software © Alexander Dale 2013. This work is released under a Creative Commons Attribution-ShareAlike 3.0 Unported License. This means that you are free to edit, remix, and extend it, even for commercial purposes, so long as your provide attribution to the original author and, if you release your modifications, you do so only under the same or similar license.