# elab API

By Michael Pence, Gavin Hazen

## Install

In this folder run

``` python
pip install .
```

## Usage

### Setting up instruments
First import the library

``` python
import elab
```
Next initialize the instruments that will be used -- here we will use a SV07 switching valve and a SY08 pump, with arbitrary COM ports

``` python
valve = elab.SV07('COM1')
pump = elab.SY08('COM2')
```
If we want to implement multi-instrument operations, we have to bundle the instruments together into one 'lab' object
``` python
lab = elab.bundle([valve,pump])
```
### Defining solution pseudonyms
Many of the operations built into the api that use the switching valve rely on ports with specified pseudonyms, such as 'cell','waste','air', and 'flush'. Pseudonyms are typically loaded from a .csv file that contains pseudonyms for the port #, formatted as below. 

---
**port, title**

1, cell

2, waste

...

---

Which is loaded in using .load_ports()
``` python
lab.load_ports('ports.csv')
```
Additionally, one can name port pseudonyms by passing a dictionary to .load_ports()
``` python
lab.load_ports({'cell' : 1, 'waste' : 2})
```

### Running experimental operations

#### Cleaning the experimental cell

We can run operations after the instruments are initialized, bundled, and setup with the port pseudonyms. Lets clean our cell:

``` python
lab.clean_cell(10)
```
.clean_cell() takes a volume (in mL) as an input, and then cleans the experimental cell by removing that volume, and flushing with that volume in water. It requires a pump and switching valve to be connected in order to operate. It requires 'cell','waste','air', and 'flush' port pseudonyms.

#### Dispensing solution

If we want to dispense a solution of our choosing we would hook it up to the switching valve and give it an appropriate pseudonym. The following code would dispensing 3 mL of a redox active species, TEMPO.

``` python
lab.dispense('tempo',3)
```
One could imagine that dispensing more complex mixtures could make the code pretty messy, so instead we can use the mix_dispense() instead. Here we are mixing 1 mL of TEMPO with 4 mL of a  buffer solution. First lets define our components as a list of lab.mix_component() fxns:

``` python
mix = [lab.mix_component('tempo',1),lab.mix_component('buffer',4)]
```

We now dispense our mixture using 

``` python
lab.mix_dispense(mix)
```

