#!/usr/bin/python

import argparse
import scipy
import h5py
import numpy as np
import scipy.integrate
import scipy.interpolate
import json
import sxs
from scipy.optimize import fmin

""" Given extrapolated waveforms for the psi4 and delta psi4, 
    compute BackgroundPsi4 and DeltaPsi4 """

def CutTimes(time, data, TLow, TUp): 
  """ Cut time and data to be between 
      TLow and TUp  """
  TLowIndex = np.where(time >= TLow)[0][0]
  TUpIndex = np.where(time <= TUp)[0][-1]
  time = time[TLowIndex:TUpIndex]
  data = data[TLowIndex:TUpIndex]
  return time, data

def GetPeakTimeMode(time, data): 
  """ Grab the peak time of some data """
  t_peak = time[np.argmax(np.absolute(data))]
  return t_peak

def SubtractPeakTimeMode(time, data): 
  """ Subtract the peak time of some data """
  t_peak = GetPeakTimeMode(time, data)
  return time - t_peak

def InterpolateTimes(time, data, time_dest):
    """ Interpolates time, data onto new time axis
        time_dest """
    ## build the interpolant only in the region where we need it
    ## time, data = CutTimes(time, data, min(time_dest), max(time_dest))
    interpolant = scipy.interpolate.CubicSpline(time, data)
    return interpolant(time_dest)

def DeltaPsi4Factor(hPsi4, B = 0.1):
    """ Given DeltaPsi4 

        B is the scaling factor in the simulation, used
        in order to make the metric perturbation size 
        comparable to the metric for the PDE solving and 
        numerical noise

        The EDGB coupling constant SqrtAlpha scaling goes as

        h^{(2)}_{ab} = (SqrtAlpha/GM)^4 Delta g_{ab} 
    """

    ## Also need to divide by B^2 (since it's at order l^4)
    hPsi4 = hPsi4 / B**2
    return hPsi4

def ReadExtrapolatedMode(p, piece, mode = [2,2]):
  """ Given a file of extrapolated modes, read in the (mode)
      at a given order """
  piece_dict = {"Psi4" : "/rMPsi4_Asymptotic_GeometricUnits.h5", \
          "DeltaPsi4" : "/rMDeltaPsi4_Asymptotic_GeometricUnits.h5"}
  try:
    file = p + piece_dict[piece]
  except: file = p + piece
  l = mode[0]
  m = mode[1]
  f = h5py.File(file, 'r')['Extrapolated_N2.dir']
  print(f.keys())
  data = f['Y_l' + str(l) + '_m'  + str(m) + '.dat']
  time, re, im = data[:,0], data[:,1], data[:,2]
  result = re + 1j*im
  ## Put in the factor if it's DeltaPsi4
  if piece == "DeltaPsi4":
    result = DeltaPsi4Factor(result)
  return time, result

def ComputeEDGBPsi4(p, mode):
  """ Given a path p to the extrapolated DeltaPsi4, 
      compute the modification to the gravitational wave psi4. 
      Return the time and modified Psi4 """

  ## Grab the background psi4
  time, psi4 = ReadExtrapolatedMode(p, "Psi4", mode)

  print("Grabbing delta psi4 for " + str(mode) + "\n")
  ## Grab delta psi4
  delta_time, delta_psi4 = ReadExtrapolatedMode(p, "DeltaPsi4", mode)

  ## Pad the delta psi4 array to be the length of the simulation
  delta_start_time = delta_time[0]

  ## Cut the time array
  time_before = time[np.where(time < delta_start_time)]
  time_after  = time[np.where(time >= delta_start_time)]

  ## Make an array of zeroes for the time before
  delta_psi4_pad = np.zeros(len(time_before))

  ## Now add in the cut array to the delta array
  delta_time = np.concatenate((time_before, delta_time))
  delta_psi4 = np.concatenate((delta_psi4_pad, delta_psi4))

  ## Now working with the padded array
  ## Interpolate onto the perturbed time axis
  delta_psi4 = InterpolateTimes(delta_time, delta_psi4, time)

  return time, psi4, delta_psi4
  
def OutputEDGBPsi4(p, only22):
  """ Given a path p to the extrapolated hPsi4, 
      compute the modification to the gravitational wave psi4,
      Return time, psi4, and delta psi4 """

  ## Dump the result to a file
  OutFile1 = p + 'BackgroundPsi4.h5'
  OutFile2 = p + 'DeltaPsi4.h5'

  fOut1 = h5py.File(OutFile1, 'w')
  fOut2 = h5py.File(OutFile2, 'w')
    
  grp1 = fOut1.create_group("Extrapolated_N2.dir")
  grp2 = fOut2.create_group("Extrapolated_N2.dir")
    
  l_arr = range(2, 9) if not only22 else [2]

  for l in l_arr:
    print("Computing for l =", l)
    for m in range(-l, l+1) if not only22 else [2, -2]:

      mode = (l, m)

      ## Compute psi4 and delta psi4 for this mode
      time, psi4, delta_psi4 = ComputeEDGBPsi4(p, mode)

      dataset1 = grp1.create_dataset("Y_l"+str(l)+"_m"+str(m)+".dat", \
        (len(time),3), dtype='f')
      dataset2 = grp2.create_dataset("Y_l"+str(l)+"_m"+str(m)+".dat", \
        (len(time),3), dtype='f')
      dataset1[:,0] = time
      dataset1[:,1] = np.real(psi4)
      dataset1[:,2] = np.imag(psi4)

      dataset2[:,0] = time
      dataset2[:,1] = np.real(delta_psi4)
      dataset2[:,2] = np.imag(delta_psi4)

  return time, psi4, delta_psi4

def main():
  p = argparse.ArgumentParser(description="Generate EDGB waveform from given EDGB simulation")
  p.add_argument("--waveform_dir", required=True, \
    help="Directory containing extrapolated, snipped simulation waveforms.")
  p.add_argument('--only22', help='Only output the 22 mode', \
    dest='only22', action='store_true')
  p.set_defaults(only22=False)
  args = p.parse_args()

  data_dir = str(args.waveform_dir) + '/'

  print("\n Working in directory " + data_dir + "\n")

  ## produce DeltaPsi4.h5 and BackgroundPsi4.h5 files
  print("\n Computing and outputting delta psi4 \n")
  OutputEDGBPsi4(data_dir, args.only22)

if __name__ == "__main__":
  main()
