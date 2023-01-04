import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import pchip_interpolate
from scipy.optimize import curve_fit
import os,sys, glob
import argparse
from collections import defaultdict

import plotHelpers as plth

#################################################################
# helper functions
#################################################################    
    
def get_deadPix(arr, sve):
	"""Identify pixels that measure 0 counts for every tested threshold value. Plot map of number of hits in each pixel
	Return: list of dead pixels as coordinate pairs"""
	
	maxThresholdsTested = len(arr)
	
	#Identify pixels with 0 counts for each threshold 
	#Check against all other thresholds by totaling for how many thresholds each pixel reads 0 counts
	totArr=np.full([35, 35], 0.)
	for a in arr:
		a = np.array(a)
		totArr += (a==0)*1.
		
	#A pixel is dead (returned 0 counts) if the additive value in totArr equals the total number of tested thresholds
	#Plot
	mapFig=plth.arrayVis(totArr==maxThresholdsTested, barTitle=f'Dead pixels')
	if sve:
		saveName = f"deadPixels"
		print(f"Saving {saveDir}{saveName}.png")
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.clf()
	else:
		plt.show()
		
	#invert rows to fit array origin, identify indices of pixels that are dead
	dpix = np.argwhere(np.flip(totArr,0)==maxThresholdsTested)
	return(dpix)
	
def get_noisyPix(arr, sve):
	"""Identify pixels that are noisy - have more counts than allowed noiseCount value
	Return: list of noisy pixels as coordinate pairs
			maximum allowed noise counts"""

	#invert rows to fit array origin
	arr=np.flip(np.array(arr),0)
	
	#Identify which/how many pixels are noisy, where "noise" is counts>noiseCount
	npix = np.argwhere(arr>args.noiseThresh)
	return npix
	
def get_optThreshold(plots, x, sve):
	"""Identify optimal threshold for each pixel
			Identify what threshold is necessary for each pixel individually to be above allowed noise count
			Scan across threshold values and find % of pixels with optimal threshold below the given threshold
			Plot array map of optimal threshold values
			Plot % of pixels with passing (lower) threshold vs threshold 
			Calculate minimum threshold with given percent of the array passing
	Return: Minimum threshold with given percent of array passing """

	goodPix = int((35*35) * args.percOn / 100.) #number of pixels that should remain good (counts>noiseCount)
	#Identify what threshold value is necessary for each pixel to be above noiseCount
	idealThresh = np.full([35, 35], np.nan)
	for r,row in enumerate(plots):
		for c,cols in enumerate(row):
			ind = np.argwhere(cols>args.noiseThresh)
			try:
				idealThresh[r][c] = x[max(ind)]
			except ValueError: #if dead pixel, insert zero
				idealThresh[r][c] = 0.
		
	passingpix = [len(np.where(idealThresh<=xpts)[0]) for xpts in x] #number of pixels that have an ideal threshold less than or equal to the chosen value
	passingpixperc = [p/35/35*100 for p in passingpix]
	optThreshInd = min(np.argwhere(np.array(passingpix)>=goodPix)) #smallest value where the optimal threshold for at least `perc` percent of pixels 

	mapFig=plth.arrayVis(idealThresh, barTitle=f'Ideal Threshold [mV]')
	if sve:
		saveName = f"idealThreshold_{args.noiseThresh}noise"
		print(f"Saving {saveDir}{saveName}.png")
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.clf()
	else:
		plt.show()	
	plt.plot(x,passingpixperc, marker='o')
	plt.xlabel("Threshold [mV]")
	plt.ylabel("% of active pixels")		
	plt.tight_layout() #reduce margin space	
	if sve:
		saveName = f"percActivePixelsVsThreshold_{args.noiseThresh}noise"
		print(f"Saving {saveDir}{saveName}.png")
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.clf()
	else:
		plt.show()	
			
	return(x[optThreshInd])
	

#################################################################
# main
#################################################################

def main(args):

	dataDirs = [f"{i}mV/" for i in threshold]
	mapArr=[]
	
	#Get data from txt files and store in 35x35 arrays - one array for each threshold value
	os.chdir(args.inputDir)	
	for i,t in enumerate(threshold):
		counts = np.full([35, 35], np.nan)
		for f in sorted(glob.glob(f"{dataDirs[i]}/count*{t}mVThresh*.txt")): #get all txt files in datadir in alphabetic order ('sorted' alphabatizes)
			parts=f.split('_')
			cStr = [p for p in parts if "col" in p]
			colVal = cStr[0][3:] #eliminate 'col'
			countVals = np.loadtxt(f,skiprows=1,usecols=1)
			#insert np.nan into array pulled from file if there are missing pixels 
			## should be 35 entries for 35 pixels - if no data, holds np.nan
			counts[:,int(colVal)] = countVals
		mapArr.append(np.flip(counts,0)) #flip array to match array pixel numberings
	
		#Plot counts on array if argument given when script ran
		if args.masks: 
			p = (35.*35.)-np.count_nonzero(counts)
			print(f"{p} pixels ({p/1225*100:.2f}%)  have count = 0")
			#pp = sum(counts[counts==0.])
			pp = np.count_nonzero(counts == 10)
			print(f"{pp} pixels ({pp/1225*100:.2f}%)  have count = 10")
			mapFig=plth.arrayVis(mapArr[i], barTitle=f'Counts with {t}mV threshold')
			if args.savePlot:
				saveName = f"{t}mV_map"
				print(f"Saving {saveDir}{saveName}.png")
				plt.savefig(f"{saveDir}{saveName}.png")
				plt.clf()
			else:
				plt.show()

	#Create S-curve plot
	xpts=50
	plots=np.empty([35,35,xpts])
	xspace=np.linspace(threshold[0],threshold[-1], 150)

	for c in range(35):
		for r in range(35):
			curvePts = [m[r][c] for m in mapArr]
			#INTERPOLATE BETWEEN POINTS FOR SMOOTH CURVE
			#PCHIP (Piecewise Cubic Hermite Interpolating Polynomial) INTERPOLATION - not twice differentiable like spline
			interp_x = np.linspace(threshold[0], threshold[-1], xpts)
			interp_y = pchip_interpolate(threshold,curvePts, interp_x)
			plots[r][c]=interp_y
			plt.plot(interp_x, interp_y, linewidth=0.5)
			
	plt.xlabel("Digital threshold [mV]")
	plt.ylabel("Interrupt counts in 10s")
	plt.tight_layout() #reduce margin space	
	
	if args.savePlot:
		saveName = f"Scurve"
		print(f"Saving {saveDir}{saveName}.png")
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.clf()
	else:
		plt.show()
		
	#Estimate dead pixels
	dpix = get_deadPix(mapArr, args.savePlot)
	print(f"{len(dpix)} dead pixels (0 hits at all thresholds)")
	if args.saveCSV:
		deadDF = pd.DataFrame(dpix, columns = ['Rows', 'Cols'])
		print(f"Saving {saveDir}deadPixels.csv")
		deadDF.to_csv(f"{saveDir}deadPixels.csv")
		
	#Estimate noisy pixels with highest threshold scan
	npix = get_noisyPix(mapArr[-1], args.savePlot) #get all pixels with more counts than args.noiseThresh from highest threshold scan
	print(f"{len(npix)} noisy pixels (counts> {args.noiseThresh})")
	if args.saveCSV:
		noisyDF = pd.DataFrame(npix, columns = ['Rows', 'Cols'])
		noisyDF = noisyDF.append(deadDF,ignore_index=True)
		print(f"Saving {saveDir}noisyPixels_{threshold[-1]}mV_above{args.noiseThresh}.csv")
		noisyDF.to_csv(f"{saveDir}noisyPixels_{threshold[-1]}mV_above{args.noiseThresh}.csv")
		
	#Calculate some interesting/relevant values
	plots=np.array(plots)
	#get_optThreshold(plots,threshold)#returns ideal threshold value for `perc` percent of pixels to be above `noiseCounts` noise level
	opt=get_optThreshold(plots,interp_x,args.savePlot)
	print(f"For {args.percOn}% of the array to be active, a threshold of at least {opt[0]:.1f} mV must be set")
	
#################################################################
# call main
#################################################################
if __name__ == "__main__":

	saveDir = os.getcwd()+"/plotsOut/thresholdScan/HR3/" #hardcode location of dir for saving output plots
	dirPath = os.getcwd()[:-15] #go one directory above the current one where only scripts are held
	threshold = [25, 50, 75, 100,110, 120, 130, 140, 150, 160, 200]
	#threshold = [20, 70, 100, 120, 150, 200]
	#threshold = [10, 25, 50, 75, 100, 150, 200]


	parser = argparse.ArgumentParser(description='Plot array data comparing default and optimized comparator DACs')
	parser.add_argument('-i', '--inputDir', default='../thresholdScan604/', required=False,  
        help='Directory containing repos of data files, from main git repo space.')
	parser.add_argument('-m', '--masks', action='store_true', default=False, required=False, 
		help='Create figures of full array with good vs noisy pixels (previously called masks). Default: False')
	parser.add_argument('-s', '--savePlot', action='store_true', default=False, required=False, 
		help='Save all plots (no display) to plotsOut/dacOptimization/arrayScan. Default: None (only displays, does not save)')
	parser.add_argument('-c', '--saveCSV', action='store_true', default=False, required=False, 
		help='Save CSV of dead/noisy pixel maps to plotsOut/dacOptimization/arrayScan. Default: False')
	parser.add_argument('-n', '--noiseThresh', default=0, required=False, type=float, 
        help='Noise threshold - pixels with more than this considered noisy. Default: 0')
	parser.add_argument('-p', '--percOn', default=50, required=False,  type=float,
        help='Percent of pixels you want activated in the array - will tell minimum threshold. Default: 50')

	parser.add_argument
	args = parser.parse_args()
	
 	
	main(args)