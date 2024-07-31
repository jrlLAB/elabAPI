import pandas as pd
import hardpotato as hp
import numpy as np
import os
import elab
import time
import matplotlib.pyplot as plt
import shutil

print('test!')
## Setup the main folder
parent_folder = '.'

## Setup up paths for the HP library to use
pstat_path = './example script/chi760e.exe'
new_folder_name = 'tempo titration'
model = "chi760e"

## Make data folder
path = os.path.join(parent_folder, new_folder_name)
os.mkdir(path)
folder = str(path)

## Define any experimental info in string

expt_info = 'pH dependance of TEMPO oxidation kinetics w/ different alcohols. Added a pretreatment step to enchance TEMPOH PCET kinetics'

## Copy this script upon running to the output folder
copied_script_name = time.strftime("%Y-%m-%d_%H%M") + '_' + os.path.basename(__file__)
shutil.copy(__file__, folder + os.sep + copied_script_name) 

## Start a timer for the experiment
start_time = time.time()

## Initiate the different instruments at their respective COM ports
valve = elab.SV07('COM8')
pump = elab.SY08('COM11')
pH = elab.pH_arduino('COM9')

## Set pump speed to a reasonable value
pump.set_speed(600)

## Load the ports.csv file
lab = elab.bundle([valve,pump,pH])
lab.load_ports('ports.csv')

## Rest to waste command initializes the pump and valve to a starting position
lab.reset_to_waste()

################################################################################



## Define a function for the CV experiment to be called later
def cv_expt(filename,sr,folder,model,sens):
    Ei = 0  # V, initial potential
    Eh = 1  # V, higher potential
    El = 0  # V, higher potential
    fileName_CV = filename
    print(f"Running {filename}")
    cv = hp.potentiostat.CV(
        Eini=Ei,
        Ev1=Eh,
        Ev2=El,
        Efin=Ei,
        sr=sr,
        sens=sens,
        dE=0.001,
        nSweeps=2,
        fileName=fileName_CV,
        resistance=8
    )
    cv.run()
    data = hp.load_data.CV(f"{fileName_CV}.txt", folder, model)
    return data

###########################################################################

## Define post dispense function, that also executes the CV function

def expt(scanrates,sub_conc,start_time,sub_folder,model,df,lab,counter,substrate,base_vol,init_sens):
    ## Measure pH before running all scanrates
    soln_pH = lab.pH.measure(delay=60,average=10)
    ## Now we iterate through all scanrates that correspond to the concentration we chose
    for scanrate in scanrates:
        ## write filename
        filename = f'CV{counter}'
        ## Run the CV experiment function
        data = cv_expt(filename=filename, sr=scanrate, folder=sub_folder, model=model, sens=init_sens)
        ## Append the experimental info to the dataframe
        df.append({'cat_conc' : 0.0015, 'sub_conc' : sub_conc, 'scanrate' : scanrate, 'base_vol' : base_vol,
         'filename' : f'{filename}.txt', 'pH' : soln_pH, 'time' : time.time() - start_time})
        ## Save the dataframe
        pd.DataFrame(df).to_csv(f'{sub_folder}/{substrate}_expt_record.csv')
        ## Bubble air to stir, and give a bit of time to let any convection settle
        lab.bubble(air_volume=2)
        time.sleep(10)
        counter += 1
    return df, counter

###############################################################################

## Define possible parameters for scanrate
scanrates = [1,0.5,0.1,0.05]

## define initial substrate concentration, 0.3 M
sub_conc_init = 0.3

## define initial volume before titration
init_vol = 5

## define titration volume
titrant_vol = 0.6

## Define initial sensitivity
init_sens = 1e-4

## List of substrates
substrates = ['ethanol' , 'glycerol' , 'isopropanol' , 'trifluoroethanol' , 'acetaldehyde' , 'glycol']

## Do an initial cleaning step
lab.clean_cell(10)

## Calibrate the pH meter
lab.calibrate_pH([4,7,10])

## Clean the cell prior to starting experiments
lab.clean_cell(10)

for substrate in substrates:

    ## Setup an empty df to store expt data as it is performed, per substrate
    df = []

    ## Start a counter for the filenames
    counter = 0

    ## Make subfolder for substrate
    path = os.path.join(folder, substrate)
    os.mkdir(path)
    sub_folder = str(path)

    ## Setup pstat in folder
    hp.potentiostat.Setup(model, pstat_path, sub_folder) 

    lab.dispense('naoh',5)
    hp.potentiostat.CA(Estep=1.5, dt=0.1, ttot=30, sens=1e-3, fileName=f'base_{substrate}').run()
    lab.clean_cell(10)
    lab.clean_cell(10)

    ## Dispense 5 mL of 1/4 TEMPO, 3/4 buffer
    mix = [lab.mix_component('tempo',init_vol*(1/3)),lab.mix_component('buffer',init_vol*(2/3))]
    lab.mix_prime(mix)
    lab.mix_dispense(mix)
    lab.bubble(air_volume=5)

    ## Run CV expt
    df, counter = expt(scanrates,0,start_time,sub_folder,model,df,lab,counter,substrate,0,init_sens)

    ## Clean cell
    lab.clean_cell(10)

    # Dispense 5 mL of 1/4 TEMPO, 1/2 alcohol, 1/4 buffer
    mix = [lab.mix_component('tempo',init_vol*(1/3)),lab.mix_component(substrate,init_vol*(1/3)),lab.mix_component('buffer',init_vol*(1/3))]
    lab.mix_prime(mix)
    lab.mix_dispense(mix)
    lab.bubble(air_volume=5)

    ## Run CV expt
    df, counter  = expt(scanrates,sub_conc_init*(1/3),start_time,sub_folder,model,df,lab,counter,substrate,0,init_sens)


    ## 25 400 uL titrations of 1/3 TEMPO, 1/3 alcohol, 1/3 NaOH
    for x in range(25):

        ## Dispensing
        mix = [lab.mix_component('tempo',titrant_vol*(1/3)),lab.mix_component(substrate,titrant_vol*(1/3)),lab.mix_component('naoh',titrant_vol*(1/3))]
        lab.mix_dispense(mix)
        lab.bubble(air_volume=5)

        ## Calculating substrate conc
        base_vol = titrant_vol*(1/3)*(x+1)

        ## Run CV expt
        df, counter = expt(scanrates,sub_conc_init*(1/3),start_time,sub_folder,model,df,lab,counter,substrate,base_vol,init_sens)

    ## Clean cell
    lab.clean_cell(20)
    # Clean cell
    lab.clean_cell(10)

## Dispense pH 7 buffer to protect the pH meter
lab.dispense('pH7', 5)
##############################################################################

## Close our COM ports when the experiment is done
[x.close() for x in [valve,pump,pH]]

## Get final timer for the experiment
end_time = time.time()-start_time

## Write experimental info and time to a text file
with open(f'{folder}/info.txt', 'w') as f:
    f.writelines(f'{expt_info}\n')
    f.writelines(f'Total time: {end_time} s')


