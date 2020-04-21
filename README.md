**Using and Generating Beyond-GR waveforms**


**(1) If you want to generate your own EDGB waveform with a 
desired coupling constant sqrt(alpha) [lengthscale], simply do**

`python3 Generate_EDGB_Strain.py --sqrt_alpha [value of EDGB coupling constant]`

(also see python3 Generate_EDGB_Strain.py -h for help)

Note that this takes a while because a spline interpolant must be
built for each mode.

This will generate a directory

`Waveforms/EDGB_*` with both the SXS format and LVC format waveforms. 

Note that all of the dependencies, such as romspline, can be 
installed with pip3

----------------------------------------------

**(2) If you want to generate your own frames files with a desired
value of the EDGB coupling constant and SNR, run**

`./create_frame_file_from_NR_data.sh [sqrt_alpaha] [SNR]`

where the command-line arguments are the desired EDGB 
coupling constant and the desired SNR.

Note that the LVC format waveforms for the desired sqrt_alpha must
already exist in Waveforms/EDGB_* (see (1) for instructions 
on how to generate this)

Note that you will need to source a version of pycbc in 
order to do this. 

