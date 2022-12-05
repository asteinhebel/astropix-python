import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import pchip_interpolate
from scipy.optimize import curve_fit
import os,sys, glob, re
import argparse
from collections import defaultdict

import digitalDataHelpers as ddh

#################################################################
# helper functions
#################################################################    
def Gauss(x, A, mu, sigma):
    return A*np.exp(-(x-mu)**2/(2.0*sigma**2))
    
def fitGauss_pix(data,title,c,r,nmbBins=50):
	#remove entries of 0 from array
	data=data[data != 0]
	#remove first element of array - leftover from previous injection energy
	data=data[1:]
	
	hist=plt.hist(data, nmbBins)
	ydata=hist[0]
	binCenters=hist[1]+((hist[1][1]-hist[1][0])/2)
	binCenters=binCenters[:-1]
	muGuess = binCenters[np.argmax(ydata)]
	p0=[10,muGuess,muGuess/2] #amp, mu, sig
	try:
		popt, pcov = curve_fit(Gauss, xdata=binCenters, ydata=ydata, p0=p0, absolute_sigma=True)
	except RuntimeError: #fit does not converge
		popt = arrayStats(data)
	
	#Calculate R^2))
	r2=calcR2(ydata, Gauss(binCenters,*popt))
	
	#Plot fit
	xspace = np.linspace(0, max(binCenters),100)
	plt.plot(xspace, Gauss(xspace, *popt)) 	
	plt.plot([], [], ' ', label=f"Amp={popt[0]:.2f}, $\mu$={popt[1]:.3f}, $\sigma$={popt[2]:.3f}")
	plt.plot([], [], ' ', label=f"R$^2$={r2:.3f}")
	plt.legend(loc='best')
	
	
	plt.xlabel("Digital ToT [us]")
	plt.ylabel("Counts")
	plt.title(title)
	
	if args.savePlot:
		saveName = f"tot_hist_chip{chip}_col{c}_row{r}"
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.clf()
	else:
		plt.show()
	
	#return mean and sigma
	return popt[1],abs(popt[2]),r2
	
def fitGauss_array(data, rangeMax, namestr, extraname, fit, bins):

	hist=plt.hist(data.flatten(), range=[0,rangeMax], bins=bins, density=True)
	ydata=hist[0]
	binCenters=hist[1]+((hist[1][1]-hist[1][0])/2)
	binCenters=binCenters[:-1]
	
	if fit:
		muGuess = binCenters[np.argmax(ydata)]
		p0=[10,muGuess,muGuess/2] #amp, mu, sig
		try:
			popt, pcov = curve_fit(Gauss, xdata=binCenters, ydata=ydata, p0=p0, absolute_sigma=True)
		except RuntimeError: #fit does not converge
			popt = arrayStats(data)
		
		#Calculate R^2))
		r2=calcR2(ydata, Gauss(binCenters,*popt))
	
		#Plot fit
		xspace = np.linspace(0, max(binCenters),100)
		plt.plot(xspace, Gauss(xspace, *popt)) 	
		plt.plot([], [], ' ', label=f"Amp={popt[0]:.2f}, $\mu$={popt[1]:.3f}, $\sigma$={popt[2]:.3f}")
		plt.plot([], [], ' ', label=f"R$^2$={r2:.3f}")
		plt.legend(loc='best')
	
	#Create plot
	plt.xlabel(namestr)
	plt.ylabel("Counts")
	plt.tight_layout()
	if args.savePlot:
		saveName = f"{namestr}_hist_chip{str(chip)}{extraname}"
		print(f"Saving {saveDir}{saveName}.png")
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.clf()
	else:
		plt.show()	
	
def calcR2(y, y_fit):
	# residual sum of squares
	ss_res = np.sum((y - y_fit) ** 2)

	# total sum of squares
	ss_tot = np.sum((y - np.mean(y)) ** 2)

	# r-squared
	r2 = 1 - (ss_res / ss_tot)
	
	return r2
	
def arrayStats(data):
	mean=np.mean(data)
	var=np.var(data)
	
	return[0, mean, var]

def makePlots(data, rangeMax, title, namestr, extraname, fit=True, bins=40):
	
	plt.clf()
	mapFigMean=ddh.arrayVis(data, barRange=[0.,rangeMax], barTitle=title, invert=True)
	if args.savePlot:
		saveName = f"{namestr}_map_chip{str(chip)}{extraname}"
		print(f"Saving {saveDir}{saveName}.png")
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.clf()
	else:
		plt.show()
	plt.clf()
	
	fitGauss_array(data, rangeMax, namestr, extraname, fit, bins)
	
def makeCleanPlots(data, r2, r2min, rangeMax, title, namestr, extraname, fit=True, bins=40):

	namestr+=f"_{str(r2min)}r2"
	
	plt.clf()
	#Create r2 mask
	r2mask = np.reshape((r2>r2min),(35,35))
	data=data*r2mask
	data[data == 0] = np.nan
	print(f"{len(r2[r2<r2min]):.2f} pixels ({len(r2[r2<r2min])/1225*100.:.2f}%) did not pass r2 requiremnet")
	mapFigMean=ddh.arrayVis(data, barRange=[0.,rangeMax], barTitle=title, invert=True)
	
	if args.savePlot:
		saveName = f"{namestr}_map_chip{str(chip)}{extraname}"
		print(f"Saving {saveDir}{saveName}.png")
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.clf()
	else:
		plt.show()
	plt.clf()
	
	fitGauss_array(data, rangeMax, namestr, extraname, fit, bins)
	
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
		mean,sig,r2 = fitGauss_pix(df['ToT(us)_row'],f"row{rVal},col{cVal}",cVal,rVal)
		totArr[cVal][rVal] = mean
		sigArr[cVal][rVal] = sig
		r2Arr[cVal][rVal] = r2
		
	#print(f"52 pixels ({52/1225*100:.2f}%) could not be fit")
		
	#Make plots - array map and histogram
	makePlots(r2Arr, 1., "goodness of fit R$^2$", "r2", extraname, fit=False)
	if args.cleanData is not None:
		makeCleanPlots(totArr, r2Arr, float(args.cleanData), 21., "mean ToT [us]", "totMean", extraname)
		makeCleanPlots(sigArr, r2Arr, float(args.cleanData), 1.5, "ToT sigma [us]", "totSig", extraname, bins=80)
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
		help='Disregard plotting pixels that should be masked. Input a csv file of row/col values of masked pixels. Default: None')
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