import pandas as pd
import numpy as np
import h5py
import matplotlib.pyplot as plt
import os,sys
import argparse

import digitalDataHelpers as ddh
import analogDataHelpers as adh
from scipy.optimize import curve_fit

#################################################################
# helper functions
#################################################################

	
#################################################################
# main
#################################################################

def main():
	
	#plot average trace at given injection
	smooth=1
	avePlots1,xincr1 = adh.get_average_traces(dataDir+in1, smoothing=smooth)
	pltpts1 = len(avePlots1[2])
	traceTime1 = 10000*xincr1*1e6
	time_us1 = np.arange(0, traceTime1, traceTime1/pltpts1)
	plt.plot(time_us1, avePlots1[2], label=label1)

	avePlots2,xincr2 = adh.get_average_traces(dataDir+in2, smoothing=smooth)
	xratio = int(xincr2 / xincr1)
	time_us2 = time_us1[0::xratio]
	#Nominally 2000 baseline points before pulse
	startPt = int(2000 - (2000. / xratio))
	#Save as many points as there are in the smoothed time axis
	stopPt = int(startPt + (10000 / xratio))
	plt.plot(time_us2, avePlots2[2][startPt:stopPt], label=label2)

	plt.xlabel("Time [us]")
	plt.ylabel("Pulse [V]")
	plt.legend(loc="best")
	
	if savePlts:
		saveName = f"comparePulseShape_{label1}_{label2}_0.3Vinj"
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.clf()
	else:
		plt.show()	
	

#################################################################
# call main
#################################################################
if __name__ == "__main__":

	saveDir = os.getcwd()+"/plotsOut/newChipInjectionScans/" #hardcode location of dir for saving output plots - automatically saves
	dataDir = "/Users/asteinhe/AstroPixData/astropixOut_tmp/v2/111622_amp1/"
	
	in1 = 'chip602_injScan_10s_combined_0.3Vinj_1.8min.h5py'
	label1="chip602"
	in2 = 'chip604_injScan_10s_combined_0.3Vinj_1.9min.h5py'
	label2="chip604"
	
	savePlts=False
    
	main()
