This repository includes the scripts that you need to generate and analyze your own Einstein-dilaton Gauss-Bonnet gravity waveforms given a value of the EdGB coupling parameter `sqrt_alpha`. 

### Generating waveforms 

In order to do this, you must have a directory `[Waveform_dir]` which contains both `BackgroundPsi4.h5` (our "Background Psi4") and `DeltaPsi4.h5` (our "Delta Psi4")(you can contact me to get these for a given binary black hole configuration). These will then be combined to give you the EdGB-modified waveform as (see Eq. 13 in https://arxiv.org/pdf/2001.03571.pdf)

`BackgroundPsi4 + sqrt_alpha^4 DeltaPsi4`

In order to do this, use `Generate_EDGB_Psi4.py` as 

`python3 Generate_EDGB_Psi4.py --dir [Waveform_dir] --sqrt_alpha [sqrt_alpha]` 

(you can also see more options with 
`python3 Generate_EDGB_Psi4.py -h`)

This will give you a file like `EDGB_Psi4_**.h5` in `[Waveform_dir]` where `**` represents the value of `sqrt_alpha`, as a string (so `sqrt_alpha = 0.01` will give `EDGB_Psi4_0p01.h5`). This is your EdGB-modified waveform that you can now analyze! 

### Analyzing and plotting waveforms

To analyze and plot the resulting waveforms, see the notebook

`AnalyzeEDGBWaveforms.ipynb`

