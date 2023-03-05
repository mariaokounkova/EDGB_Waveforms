#!/usr/bin/python

import sys
import argparse
import scipy
import h5py
import numpy as np
import os

def ReadExtrapolatedMode(p, piece, mode):
  """ Given a file of extrapolated modes, read in the (mode)
      at a given order """
  piece_dict = {"Delta" : "DeltaPsi4.h5", \
          "Background" : "BackgroundPsi4.h5"}
  file = p + piece_dict[piece]
  l = mode[0]
  m = mode[1]
  f = h5py.File(file, 'r')
  data = f['Extrapolated_N2.dir']['Y_l' + str(l) + '_m'  + str(m) + '.dat']
  time, re, im = data[:,0], data[:,1], data[:,2]
  result = re + 1j*im
  return time, result

def ComputeEDGBPsi4(p, mode, sqrt_alpha):
  """ Combine the background and delta psi4"""

  ## Read in the background
  time, strain = ReadExtrapolatedMode(p, "Background", mode)
  delta_time, delta_strain = ReadExtrapolatedMode(p, "Delta", mode)

  ## Now add the strain and delta strain together
  ## with the correct value of sqrt_alpha
  total = strain + sqrt_alpha**4 * delta_strain

  return time, total

def OutputEDGBPsi4(p, sqrt_alpha):
    """ Generate an h5 file with the modified psi4 for a 
        given value of sqrt_alpha """

    ## For naming the file, replace . with p because otherwise
    ## the .h5 file can't be read by catalog scripts
    name = str(sqrt_alpha).replace('.', 'p')

    ## Make the output file
    OutFile = p + "/EDGB_Psi4_" + name + ".h5"
    fOut = h5py.File(OutFile, 'w')
    
    grp = fOut.create_group("Extrapolated_N2.dir")
    
    ## Compute for all of the modes
    print("Computing for all of the modes")
    l_arr = range(2, 9)

    for l in l_arr:
        print("Computing for l = ", l)

        for m in range(-l, l+1):
            mode = (l, m)
            print(mode)

            ## Compute for the given mode
            time, total = ComputeEDGBPsi4(p, mode, sqrt_alpha)

            dataset = grp.create_dataset("Y_l"+str(l)+"_m"+str(m)+".dat", \
            (len(time),3), dtype='f')

            dataset[:,0] = time
            dataset[:,1] = np.real(total)
            dataset[:,2] = np.imag(total)

    fOut.close()
    print("Wrote waveforms to file", OutFile)

def GenerateEDGBPsi4Files(p, sqrt_alpha):
    """ Generates the sxs format waveform for a given
        beyond-GR simulation with coupling parameter sqrt_alpha. 
        """

    ## Since sqrt_alpha has a decimal point and *.h5 readers cannot
    ## handle this decimal point, we will replace the decimal point 
    ## with the character p, ie
    ## 0.1 will become 0p1
    sqrt_alpha_string = str(sqrt_alpha).replace('.', 'p')

    ## Call to generate total waveform in sxs format
    OutputEDGBPsi4(p + "/", sqrt_alpha)
    
def main():
  p = argparse.ArgumentParser(description="Generate EDGB waveform for a given coupling parameter value")
  p.add_argument("--dir", required=True, \
    help="Directory containing the Background and Delta Psi4 files")
  p.add_argument("--sqrt_alpha", required=True, type=float,\
    help="Value of EDGB coupling constant")
  #p.add_argument('--only22', help='Only output the 22 mode', \
  #  dest='only22', action='store_true')
  #p.add_argument('--dropm0', help='Include all modes up to l = 8 except m = 0 modes', \
  #  dest='dropm0', action='store_true')
  #p.set_defaults(only22=False)
  #p.set_defaults(dropm0=False)
  args = p.parse_args()

  GenerateEDGBPsi4Files(args.dir, args.sqrt_alpha)

if __name__ == "__main__":
  main()
