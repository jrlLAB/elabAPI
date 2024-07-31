import pandas as pd
import numpy as np
import os
import elab
import time
import matplotlib.pyplot as plt
import shutil

## Setup the main folder
parent_folder = '.'


new_folder_name = 'phosphoric acid titration'

## Make data folder
path = os.path.join(parent_folder, new_folder_name)
os.mkdir(path)
folder = str(path)

## Define any experimental info in string

expt_info = 'Example titration of 0.1 M phosphoric acid with 1M NaOH.'

## Copy this script upon running to the output folder
copied_script_name = time.strftime("%Y-%m-%d_%H%M") + '_' + os.path.basename(__file__)
shutil.copy(__file__, folder + os.sep + copied_script_name) 

## Start a timer for the experiment
start_time = time.time()

## Initiate the different instruments at their respective COM ports
valve = elab.SV07('COM8')
pump = elab.SY08('COM11')
pH = elab.pH_arduino('COM9')
temp = elab.HS7('COM7')

## Set pump speed to a reasonable value
pump.set_speed(600)

## Load the ports.csv file
lab = elab.bundle([valve,pump,temp,pH])
lab.load_ports('ports_titration.csv')

## Rest to waste command initializes the pump and valve to a starting position
lab.reset_to_waste()

################################################################################

## define initial volume before titration
init_vol = 4

## define titration volume
titrant_vol = 0.1

## Do an initial cleaning step
lab.clean_cell(10)

## Calibrate the pH meter
lab.calibrate_pH([4,7,10])
print('pH calibrated')

## Clean the cell prior to starting experiments
lab.clean_cell(10)

## Initialize the data frame
df = []

## 3 trials of the titration
for n in range(4):
    print(f'Expt #{n+1}')


    ## Dispense 4 mL of 0.1M Phosphoric Acid
    mix = [lab.mix_component('phosphoric_acid',init_vol)]
    lab.mix_prime(mix)
    lab.mix_dispense(mix)

    ## Measure pH
    soln_pH = lab.pH.measure(delay=120,average=10)
    print(f'0 mL NaOH -- {soln_pH:.2f}')

    ## Append the experimental info to the dataframe
    df.append({'expt' : n+1, 'base_vol' : 0,
        'point' : 0, 'temp' : temp.query_temp(),
        'pH' : soln_pH, 'time' : time.time() - start_time})
    
    ## Save the dataframe
    pd.DataFrame(df).to_csv(f'{folder}/expt_record.csv')

    ## 100 100 uL titrations of 1 M NaOH
    for x in range(150):

        ## Define total amount of base dispensed
        base_vol = titrant_vol*(x+1)
        print(f'{base_vol:.2f} mL NaOH -- {soln_pH:.2f}')
        ## Dispensing
        mix = [lab.mix_component('naoh',titrant_vol)]
        lab.mix_dispense(mix)

        ## Measure pH
        soln_pH = lab.pH.measure(delay=30,average=10)

        ## Append the experimental info to the dataframe
        df.append({'expt' : n+1, 'base_vol' : base_vol,
         'point' : (x+1), 'temp' : temp.query_temp(),
         'pH' : soln_pH, 'time' : time.time() - start_time})
        
        ## Save the dataframe
        pd.DataFrame(df).to_csv(f'{folder}/expt_record.csv')

    ## Clean cell
    lab.clean_cell(20)

## Dispense pH 7 buffer to protect the pH meter
lab.dispense('pH7', 5)
##############################################################################

## Close our COM ports when the experiment is done
[x.close() for x in [valve,pump,temp,pH]]

## Get final timer for the experiment
end_time = time.time()-start_time

## Write experimental info and time to a text file
with open(f'{folder}/info.txt', 'w') as f:
    f.writelines(f'{expt_info}\n')
    f.writelines(f'Total time: {end_time} s')


