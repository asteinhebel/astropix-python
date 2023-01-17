import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import pchip_interpolate
from scipy.optimize import curve_fit
import os,sys, glob, re
import argparse
from collections import defaultdict

import digitalDataHelpers as ddh
import analogDataHelpers as adh
import calcHelpers as clch
import plotHelpers as plth

#################################################################
# helper functions
#################################################################   

	
	
#################################################################
# main
#################################################################

def main(args):

	df0 = pd.read_csv(args.inputCSVs[0])
	df0 = df0.replace(np.nan, 0.).to_numpy() #replace NaNs with zero and convert to numpy
	df0_flat = df0[:,1:].flatten() #do not include first column of indices
	df0_name = args.inputCSVs[0].split('/')[-1][:-4]
		
	df1 = pd.read_csv(args.inputCSVs[1])
	df1 = df1.replace(np.nan, 0.).to_numpy() #replace NaNs with zero and convert to numpy
	df1_flat = df1[:,1:].flatten() #do not include first column of indices
	df1_name = args.inputCSVs[1].split('/')[-1][:-4]
	
	#calculate correlation - error from  https://psyarxiv.com/uts98/	
	r, r_err = clch.calcCorrCoeff(df0_flat,df1_flat)
	
	#save or display plots
	plt.scatter(df0_flat,df1_flat)
	plt.plot([], [], ' ', label=f"r={r:.2f} +\- {r_err:.2f}")
	plt.legend(loc='best')
	plt.xlabel(df0_name)
	plt.ylabel(df1_name)
	if args.savePlot:
		plt.savefig(f"{saveDir}correlate_{df0_name}__{df1_name}.png")
		plt.close()
		plt.clf()
	else:
		plt.show()



#################################################################
# call main
#################################################################
if __name__ == "__main__":

	saveDir = os.getcwd()+"/plotsOut/pixelScan_Am241/chip604/" #hardcode location of dir for saving output plots
	dirPath = os.getcwd()[:-15] #go one directory above the current one where only scripts are held

	parser = argparse.ArgumentParser(description='Correlate data stored in CSV files from full array maps')
	parser.add_argument('-i', '--inputCSVs', action='store', default=[f'{saveDir}r2_map_chip604.csv',f'{dirPath}analysisScripts/plotsOut/thresholdScan/chip604/idealThresholds.csv'], type=str, nargs=2, 
    	help =  'Input CSV data files to correlate - each file should contain 35x35 array with value stored for each pixel. Default: [chip604_r2, chip604_idealThresholds]')
	parser.add_argument('-s', '--savePlot', action='store_true', default=False, required=False, 
		help='Save all plots (no display) to saveDir. Default: None (only displays, does not save)')	

	parser.add_argument
	args = parser.parse_args()
	
 	
	main(args)