#!/usr/bin/python

import sys
sys.path.insert(1, 'catalog_tools')
from convert_sxs_to_lvc import *
import argparse
import scipy
import h5py
import numpy as np
import os

def ReadExtrapolatedMode(p, piece, mode, order=2, sqrt_alpha=None):
  """ Given a file of extrapolated modes, read in the (mode)
      at a given order """
  sqrt_alpha = name = str(sqrt_alpha).replace('.', 'p')
  piece_dict = {"DeltaStrain" : "/DeltaStrain.h5", \
          "BackgroundStrain" : "/BackgroundStrain.h5", \
          "EDGBModified" : "/EDGB_" + sqrt_alpha + "/rhOverM_Asymptotic_GeometricUnits_EDGB_sqrt_alpha_" + sqrt_alpha + ".h5", \
                  "hRWZ" : "/rhOverM_Asymptotic_GeometricUnits.h5"}
  file = p + piece_dict[piece]
  print(file)
  l = mode[0]
  m = mode[1]
  f = h5py.File(file, 'r')
  data = f['Extrapolated_N'+str(order)+'.dir']['Y_l' + str(l) + '_m'  + str(m) + '.dat']
  time, re, im = data[:,0], data[:,1], data[:,2]
  result = re + 1j*im
  return time, result

def ComputeEDGBModifiedStrain(p, mode, l):
  """ Given a value of the EDGB coupling constant l, a path 
      p to the extrapolated hPsi4 compute the modified gravitational wave strain """

  ## Read in the background
  time, strain = ReadExtrapolatedMode(p, "BackgroundStrain", mode)
  delta_time, delta_strain = ReadExtrapolatedMode(p, "DeltaStrain", mode)

  ## Now add the strain and delta strain together
  ## with the correct value of l
  total = strain + l**4 * delta_strain

  return time, total


def OutputEDGBModifiedStrain(p, sqrt_alpha, only22):
    """ Generate an h5 file with the modified strain for a 
        given value of sqrt_alpha """

    ## For naming the file, replace . with p because otherwise
    ## the .h5 file can't be read by catalog scripts
    name = str(sqrt_alpha).replace('.', 'p')
    
    ## Make the output directory
    os.mkdir(p + 'EDGB_' + name)
    
    OutFile = p + 'EDGB_' + name + '/rhOverM_Asymptotic_GeometricUnits_EDGB_sqrt_alpha_' + name + '.h5'
    fOut = h5py.File(OutFile, 'w')
    
    grp = fOut.create_group("Extrapolated_N2.dir")
    
    l_arr = range(2, 9) if not only22 else [2]

    for l in l_arr:
      print("Computing for l = ", l)
      for m in range(-l, l+1) if not only22 else [2, -2]:

        mode = (l, m)

        ## Compute for the given mode
        time, total = ComputeEDGBModifiedStrain(p, mode, sqrt_alpha)

        dataset = grp.create_dataset("Y_l"+str(l)+"_m"+str(m)+".dat", \
        (len(time),3), dtype='f')

        dataset[:,0] = time
        dataset[:,1] = np.real(total)
        dataset[:,2] = np.imag(total)

    fOut.close()
    print("Wrote waveforms to file", OutFile)

def GetModesFromString(modes):
    """ Method to get output modes from a given string, used to specify
        the modes to the LVC file generation """
    if modes == 'all':
        modes = [[l,m] for l in range(2,9) for m in range(-l,l+1)]
    elif modes == '22only':
        modes = [[2, 2], [2, -2]]
    return modes

def GenerateStrainFiles(sqrt_alpha, only22 = False):
    """ Generates the sxs format waveform and LVC format waveform for a given
        beyond-GR simulation with coupling parameter sqrt_alpha. 
        
        The file BeyondGRAnalysis/Waveforms/BackgroundStrain.h5 contains the strain
        of the GR background, h_GR. 
        
        Meanwhile the file BeyondGRAnalysis/Waveforms/DeltaStrain.h5 contains the 
        leading-order modification to the beyond-GR strain, delta_h. 
        
        We first generate the sxs format total beyond-GR waveform for these
        using 
        
        h = h_GR + sqrt_alpha^4 * delta_h. 
        
        Then we convert the resulting waveform into the LVC format, from 
        which we can then generate frames files
        
        only22 is a boolean specifying if we should only output the 22 mode, 
        which can be useful for testing purposes
        
        """
    ## Since sqrt_alpha has a decimal point and *.h5 readers cannot
    ## handle this decimal point, we will replace the decimal point 
    ## with the character p, ie
    ## 0.1 will become 0p1
    sqrt_alpha_string = str(sqrt_alpha).replace('.', 'p')

    ## Call to generate total waveform in sxs format
    OutputEDGBModifiedStrain("Waveforms/", sqrt_alpha, only22)

    ## Vars needed for the sxs to lvc conversion script. 
    ## values like resolution and sxs_metadata and sxs_resolutions
    ## don't really matter, but we need to specify them
    sxs_data = "Waveforms" ## input directory
    resolution = 0
    sxs_metadata = "catalog_tools/Metadata/sxs_catalog.json"
    sxs_resolutions = "catalog_tools/Metadata/sxs_catalog_resolutions.json"
    modes = GetModesFromString("22only" if only22 else "all") ## modes to output
    out_path = "Waveforms/EDGB_" + sqrt_alpha_string ## output directory
    in_file = "EDGB_" + sqrt_alpha_string + "/rhOverM_Asymptotic_GeometricUnits_EDGB_sqrt_alpha_" + sqrt_alpha_string + ".h5"
    out_file = "Waveforms/EDGB_" + sqrt_alpha_string + "/EDGB_sqrt_alpha_" + sqrt_alpha_string + ".h5"

    ## convert the simulation into sxs format
    convert_simulation(sxs_data, resolution, sxs_metadata, sxs_resolutions, modes, out_path, \
                  in_name = in_file, out_name = out_file)
    print("Output LVC format waveform to", out_file)
    
def main():
  p = argparse.ArgumentParser(description="Generate EDGB waveform for a given coupling parameter value")
  p.add_argument("--sqrt_alpha", required=True, type=float,\
    help="Value of EDGB coupling constant")
  #p.add_argument("--waveform_dir", required=True, \
  #help="Directory containing extrapolated, snipped simulation waveforms.")
  p.add_argument('--only22', help='Only output the 22 mode', \
    dest='only22', action='store_true')
  p.set_defaults(only22=False)
  args = p.parse_args()

  GenerateStrainFiles(args.sqrt_alpha, args.only22)

if __name__ == "__main__":
  main()