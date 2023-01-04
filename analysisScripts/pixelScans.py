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

def fitSaveGauss(data,title,extraArgs,nmbBins=50, fit=True):
	"""Clean data and fit to a Gaussian. Plot (save, if applicable) histogram and associated Gaussian
		If extraArgs=[colNumb, rowNmb], considers data from one pixel (defines cleaning and naming)
		If extraArgs=[plotMaxRange, nmbBins, namingString, namingString2], considers data from full array (defines cleaning and naming)
	Return: mean and sigma parameters of Gaussian fit
			R2 goodness of fit"""

	if len(extraArgs)==2:
		pix=True
		c=extraArgs[0]
		r=extraArgs[1]
		pltRange=None
		normH=False		
		saveName = f"tot_hist_chip{chip}_col{c}_row{r}"
		#remove entries of 0 from array
		data=data[data != 0]
	else:
		pix=False
		pltRange=[0,extraArgs[0]]
		nmbBins=extraArgs[1]
		namestr=extraArgs[2]
		extraname=extraArgs[3]
		normH=True
		saveName = f"{namestr}_hist_chip{str(chip)}{extraname}"
		data=data.flatten()

	(amp,mean,sig), hist, r2 = clch.fitGauss(data, nmbBins, range_in=pltRange, normalizeHist=normH, returnHist=True, returnR2=True)

	if fit:
		#Plot fit
		xspace = np.linspace(0, max(hist[1]),100)
		plt.plot(xspace, clch.Gauss(xspace, amp,mean,sig)) 	
		plt.plot([], [], ' ', label=f"Amp={amp:.2f}, $\mu$={mean:.3f}, $\sigma$={sig:.3f}")
		plt.plot([], [], ' ', label=f"R$^2$={r2:.3f}")
		plt.legend(loc='best')

	#label plots
	plt.xlabel("Digital ToT [us]")
	plt.ylabel("Counts")
	plt.title(title)

	#save or display plots
	if args.savePlot:
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.close()
		plt.clf()
	else:
		plt.show()
	
	return mean,abs(sig),r2	
	
	
def makePlots(data, rangeMax, title, namestr, extraname, fit=True, bins=40, r2cleaning=[0., None]):
	"""Plot full array information - matrix visualization and associated hist
			Optionally plot with limit on allowed R2 value"""
	
	#if r2 cleaning used, update naming and clean data set
	if r2cleaning[0]>0:
		r2min=r2cleaning[0]
		r2=r2cleaning[1]
		namestr+=f"_{str(r2min)}r2"
		r2mask = np.reshape((r2>r2min),(35,35))
		data=data*r2mask
		data[data == 0] = np.nan
		print(f"{len(r2[r2<r2min]):.2f} pixels ({len(r2[r2<r2min])/1225*100.:.2f}%) did not pass r2 requirement")
	
	plt.clf()
	mapFigMean=plth.arrayVis(data, barRange=[0.,rangeMax], barTitle=title, invert=True)
	if args.savePlot:
		saveName = f"{namestr}_map_chip{str(chip)}{extraname}"
		print(f"Saving {saveDir}{saveName}.png")
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.clf()
	else:
		plt.show()
	plt.clf()
	
	fitSaveGauss(data,title,[rangeMax,bins,namestr,extraname],fit=fit)	
	
	
#################################################################
# main
#################################################################

def main(args):

	totArr = np.full([35, 35], np.nan)
	sigArr = np.full([35, 35], np.nan)
	r2Arr = np.full([35, 35], np.nan)
	extraname = "_masked" if args.masks else ""

	#Get data from txt files and store in 35x35 arrays - one array for each threshold value
	os.chdir(args.inputDir)	
	for f in sorted(glob.glob(f"*.csv")): #get all txt files in datadir in alphabetic order ('sorted' alphabatizes)
		parts=f.split('_')
		cStr = [p for p in parts if "col" in p]
		cVal = int(cStr[0][3:]) #eliminate 'col'
		rStr = [p for p in parts if "row" in p]
		rVal = int(rStr[0][3:]) #eliminate 'row'
		#Get hits
		df = ddh.getDF_singlePix(f, pix=[rVal,cVal])
		#Fit distributions and get ToT mean/sigma
		mean,sig,r2 = fitSaveGauss(df['ToT(us)_row'],f"row{rVal},col{cVal}",[cVal,rVal])	

		totArr[cVal][rVal] = mean
		sigArr[cVal][rVal] = sig
		r2Arr[cVal][rVal] = r2
				
	#Make plots - array map and histogram
	makePlots(r2Arr, 1., "goodness of fit R$^2$", "r2", extraname, fit=False)
	if args.cleanData is not None:
		makePlots(totArr, 21., "mean ToT [us]", "totMean", extraname, r2cleaning=[float(args.cleanData),r2Arr])
		makePlots(sigArr, 1.5., "ToT sigma [us]", "totSig", extraname, bins=80, r2cleaning=[float(args.cleanData),r2Arr])

	else:
		makePlots(totArr, 21., "mean ToT [us]", "totMean", extraname)
		makePlots(sigArr, 10., "ToT sigma [us]", "totSig", extraname, bins=80)


#################################################################
# call main
#################################################################
if __name__ == "__main__":

	saveDir = os.getcwd()+"/plotsOut/pixelScan_0.3Vinjection/chip602/" #hardcode location of dir for saving output plots
	dirPath = os.getcwd()[:-15] #go one directory above the current one where only scripts are held

	parser = argparse.ArgumentParser(description='Plot array data comparing default and optimized comparator DACs')
	parser.add_argument('-i', '--inputDir', default='../logInj/chip602_pixelScan_0.3Vinj/', required=False,  
        help='Directory containing repos of data files, from main git repo space.')
	parser.add_argument('-m', '--masks', action='store_true', default=False, required=False, 
		help='WIP - Disregard plotting pixels that should be masked. Input a csv file of row/col values of masked pixels. Default: None')
	parser.add_argument('-s', '--savePlot', action='store_true', default=False, required=False, 
		help='Save all plots (no display) to plotsOut/dacOptimization/arrayScan. Default: None (only displays, does not save)')
	parser.add_argument('-c', '--cleanData', default=None, required=False, 
		help='Plot only bluk values that pass an R2 requirement. Give min r2 value as input here. Default: None')
		

	parser.add_argument
	args = parser.parse_args()
	
	#find chip number from file name
	strToSplit=args.inputDir.replace("/","_")
	parts=strToSplit.split('_')
	chipname = [p for p in parts if "chip" in p]
	chip=chipname[0][4:]
	
 	
	main(args)