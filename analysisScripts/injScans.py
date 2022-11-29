import pandas as pd
import numpy as np
import h5py
import matplotlib.pyplot as plt
import os,sys,glob
import argparse

import digitalDataHelpers as ddh
import analogDataHelpers as adh
from scipy.optimize import curve_fit

#################################################################
# helper functions
#################################################################

def separateRuns (time,arr):
	#identify each different setting in run
	#if more than 1s between triggers, then it's a new setting
	diffArr=np.diff(time)
	indexArray=np.where(diffArr>1)
	indexArray=np.insert(indexArray,0,0)
	
	arr = np.array(arr)
	allRuns = [arr[indexArray[i]:indexArray[i+1]] for i in range(len(indexArray)-1)]
	
	return allRuns
	
def Gauss(x, A, mu, sigma):
    return A*np.exp(-(x-mu)**2/(2.0*sigma**2))
    
def fitGauss(data,title,nmbBins=50, analog=False):
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
	
	if analog:
		plt.xlabel("Analog proxy ToT [us]")
		nme="analog"
	else:
		plt.xlabel("Digital ToT [us]")
		nme="digital"
	plt.ylabel("Counts")
	plt.title(f"{title:.1f}V injection, chip {c}")
	
	if savePlts:
		saveName = f"totHist_chip{c}_{title:.1f}Vinj_{nme}"
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.clf()
	else:
		plt.show()
	
	#return mean and sigma
	return popt[1],popt[2]
	
	
def arrayStats(data):
	mean=np.mean(data)
	var=np.var(data)
	
	return[0, mean, var]
	
def pltInjScan(tot, injections, totErr, title, analog=False):

	if len(tot)!=len(injections):
		injections=injections[0:len(tot)]

	plt.errorbar(injections, tot, yerr=totErr, marker="o", linestyle='')
	plt.title(f"{title} - Chip {c}")
	plt.xlabel("Injection voltage [V]")	
	if analog:
		plt.ylabel("Analog proxy ToT [us]")
		nme="analog"
	else:
		plt.ylabel("Digital ToT [us]")
		nme="digital"
	
	if savePlts:
		saveName = f"injScan_chip{c}_{nme}"
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.clf()
	else:
		plt.show()
	
	return
	
def compareInjScans(totA, totD, injections, errA, errD):

	if len(totA)!=len(injections):
		injectionsA=injections[0:len(totA)]

	plt.clf()
	plt.errorbar(injections, totD, yerr=errD, marker="o", linestyle='', label="Digital")
	plt.errorbar(injectionsA, totA, yerr=errA, marker="o", linestyle='', label="Analog")
	plt.legend(loc='best')
	plt.title(f"Chip {c}")
	plt.xlabel("Injection voltage [V]")
	plt.ylabel("ToT [us]")
	
	if savePlts:
		saveName = f"compareInjScan_chip{c}"
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.clf()
	else:
		plt.show()
	
	return

	
#################################################################
# main
#################################################################

def main(chip):

	#DF dictionary to keep individual data from each run
	dfDict={}
	injs=[] #not numerical - defined as files are pulled in. So order of digital data matches, but will not match analog data in combined analog data file

	#get analog data
	time = 1.8 if chip==602 else 1.9
	anaDF = adh.getDF(adataDir+'chip'+str(chip)+f'_injScan_10s_combined_0.3Vinj_{time}min.h5py')
	anaDF.rename(columns={"AnalogToT": "ToT"},inplace=True)
	dfDict['analog'] = anaDF
	
	#get digital data and injection energies
	files = glob.glob(os.path.join(ddataDir, f'*{chip}*.csv'))
	#End execution if no files
	if len(files)==0:
		print("No files detected")
		return
	for f in files:
		injV = f.split('_')[5][0]
		#Check whether 10 or 100
		if len(f.split('_')[5])==9:
			injV = 10.
		injs.append(round(float(injV)*0.1, 2))
		digiDF = ddh.getDF_singlePix(f)
		dfDict[f'digital_{0.1*float(injV):.1f}'] = digiDF

	
	#Analog injection plot
	analogRuns = separateRuns(dfDict['analog']['Time'],dfDict['analog']['ToT'])
	analogMeans = []
	analogSigs = []
	print("Create analog plots")
	for i,injV in enumerate(analogRuns):
		mean,sig = fitGauss(injV, (i+1)*0.1, analog=True)
		analogMeans.append(mean)
		analogSigs.append(sig)
		
	#AnalogMeans is implicitly sorted in order of increasing injection voltage
	#injs is defined as files are read in, so not necessarily sorted
	#Sort injs when plotting for data points to match up appropriately
	pltInjScan(analogMeans, sorted(injs), analogSigs,"Analog", analog=True)	
	
	#Digital injection plot
	digitalMeans = []
	digitalSigs = []
	print("Create digital plots")
	for df in dfDict:
		if df=='analog': #consider digital data only
			continue
		mean,sig = fitGauss(dfDict[df]['ToT(us)_row'], float(df.split('_')[1]))
		digitalMeans.append(mean)
		digitalSigs.append(sig)
	pltInjScan(sorted(digitalMeans), sorted(injs), sorted(digitalSigs),"Digital (row)")	
		
	#Compare scans
	compareInjScans(analogMeans, sorted(digitalMeans), sorted(injs), analogSigs, sorted(digitalSigs))
	
#################################################################
# call main
#################################################################
if __name__ == "__main__":

	saveDir = os.getcwd()+"/plotsOut/newChipInjectionScans/" #hardcode location of dir for saving output plots - automatically saves
	ddataDir = "/Users/asteinhe/AstroPixData/digital/logInj/injectionScans_10s_chip602_chip604_chip401/"
	adataDir = "/Users/asteinhe/AstroPixData/astropixOut_tmp/v2/111622_amp1/"

	savePlts = True

	chip = [602, 604, 401]
	#chip = [602]
	for c in chip:
		print(f"Running Chip {c}")
		main(c)