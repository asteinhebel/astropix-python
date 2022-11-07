import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
import os,sys, glob
import argparse

import digitalDataHelpers as ddh

#################################################################
# helper functions
#################################################################


#################################################################
# main
#################################################################

def main(args):

	threshold=[100]
	mapArr=[]
	
	#Get data from txt files and store in 35x35 arrays - one array for each threshold value
	os.chdir(args.inputDir)	
	for i,t in enumerate(threshold):
		counts = np.full([35, 35], np.nan)
		for f in sorted(glob.glob(f"count*{t}mVThresh*.txt")): #get all txt files in datadir in alphabetic order ('sorted' alphabatizes)
			parts=f.split('_')
			cStr = [p for p in parts if "col" in p]
			colVal = cStr[0][3:] #eliminate 'col'
			countVals = np.loadtxt(f,skiprows=1,usecols=1)
			#insert np.nan into array pulled from file if there are missing pixels 
			## should be 35 entries for 35 pixels - if no data, holds np.nan
			counts[:,int(colVal)] = countVals
		mapArr.append(np.flip(counts,0)) #flip array to match array pixel numbering
		
		#Plot counts on array if argument given when script ran
		if args.masks: 
			mapFig=ddh.arrayVis(mapArr[i], barTitle=f'Counts with {t}mV threshold')
			if args.savePlot:
				saveName = f"{t}mV_map"
				print(f"Saving {saveDir}{saveName}.png")
				plt.savefig(f"{saveDir}{saveName}.png")
				plt.clf()
			else:
				plt.show()
			

		#Create S-curve plot
		for c in range(35):
			for r in range(35):
				curvePts=[m[r][c] for m in mapArr]
				plt.plot(threshold,curvePts, marker='o', label=f"r{r} c{c}")
				#INTERPOLATE BETWEEN POINTS FOR SMOOTH CURVE
				#CAN ONLY DO WITH AT LEAST 4 DATA POINTS = AT LEAST 4 THRESHOLD VALUES
				"""
				X_Y_Spline = make_interp_spline(threshold, curvePts)
				# Returns evenly spaced numbers over a specified interval.
				X_ = np.linspace(threshold[0], threshold[-1], 50)
				Y_ = X_Y_Spline(X_)
				plt.plot(X_, Y_)
				"""
		plt.xlabel("Digital threshold [mV]")
		plt.ylabel("Interrupt counts in 10s")
		#Fit curves to Sigmoid
		
		if args.savePlot:
			saveName = f"Scurve"
			print(f"Saving {saveDir}{saveName}.png")
			plt.savefig(f"{saveDir}{saveName}.png")
			plt.clf()
		else:
			plt.show()
			
		
	
#################################################################
# call main
#################################################################
if __name__ == "__main__":

	saveDir = os.getcwd()+"/plotsOut/thresholdScan/" #hardcode location of dir for saving output plots
	dirPath = os.getcwd()[:-15] #go one directory above the current one where only scripts are held

	parser = argparse.ArgumentParser(description='Plot array data comparing default and optimized comparator DACs')
	parser.add_argument('-i', '--inputDir', default='../thresholdScan602/', required=False,  
        help='Directory containing data files, from main git repo space. Can provide one or two directories - if two, send default first.')
	parser.add_argument('-m', '--masks', action='store_true', default=False, required=False, 
		help='Create figures of full array with good vs noisy pixels (previously called masks). Default: False')
	parser.add_argument('-s', '--savePlot', action='store_true', default=False, required=False, 
		help='Save all plots (no display) to plotsOut/dacOptimization/arrayScan. Default: None (only displays, does not save)')

	parser.add_argument
	args = parser.parse_args()
	
 	
	main(args)