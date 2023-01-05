import pandas as pd
import numpy as np
import h5py
import matplotlib.pyplot as plt
import os,sys,glob
import argparse

import digitalDataHelpers as ddh
import analogDataHelpers as adh
import calcHelpers as clch
import plotHelpers as plth

#################################################################
# helper functions
#################################################################

def separateRuns (time,arr):
	"""Identify each different setting in long analog run. 
	If more than 1s between triggers, then it's a new setting. 
	Use array of timing to determine when new settings occur
	Return: 2d list containing the data points (not timing) for each different setting"""

	indexArray=adh.new_i(time)
	
	arr = np.array(arr)
	allRuns = [arr[indexArray[i]:indexArray[i+1]] for i in range(len(indexArray)-1)]
	
	return allRuns
    
def fitSaveGauss(data,title,nmbBins=50, analog=False, compare=False):
	"""Clean data and fit to a Gaussian. Plot histogram and associated Gaussian
	Return: mean and sigma parameters of Gaussian fit"""

	#remove entries of 0 from array
	data=data[data != 0]
	#remove first element of array - leftover from previous injection energy
	data=data[1:]
	(amp,mean,sig), hist = clch.fitGauss(data, nmbBins, returnHist=True)

	#label plots
	if analog:
		if analogPulseHeight:
			plt.xlabel("Analog pulse height [V]")
			nme="analog_peak"
		else:
			plt.xlabel("Analog proxy ToT [us]")
			nme="analog_ToT"
	else:
		plt.xlabel("Digital ToT [us]")
		nme="digital"
	plt.ylabel("Counts")
	plt.title(f"{title:.1f}V injection, chip {c}")
	
	
	if savePlts and not compare:
		saveName = f"totHist_chip{c}_{title:.1f}Vinj_{nme}"
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.clf()
	elif compare:
		pass
	else:
		plt.show()
	
	#return mean and sigma
	return mean,sig
	
	
def pltInjScan(tot, injections, totErr, title, analog=False):
	"""Plot the ToT (digital or analog) or analog pulse height as a function of injection V"""

	if len(tot)!=len(injections):
		injections=injections[0:len(tot)]
		print(len(tot))

	plt.errorbar(injections, tot, yerr=totErr, marker="o", linestyle='')
	plt.title(f"{title} - Chip {c}")
	plt.xlabel("Injection voltage [V]")	
	if analog:
		if analogPulseHeight:
			plt.ylabel("Analog pulse height [V]")
			nme="analog_peak"
		else:
			plt.ylabel("Analog proxy ToT [us]")
			nme="analog_ToT"
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
	"""Plot the digital and analog ToT as a function of injection V on the same plot for comparison"""

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
	
def compareAnalogInjScans(anaP, anaT, injections, errP, errT):
	"""Compare the analog pulse height and ToT proxy from the injection scan of one pixel"""

	if len(anaP)!=len(injections):
		injections=injections[0:len(anaP)]

	fig, ax1 = plt.subplots()	
	plt.title(f"Chip {c}")
	ax1.set_xlabel('Injection voltage [V]')
	ax1.set_ylabel('Peak height [V]')
	ax1.errorbar(injections, anaP, yerr=errP, marker="o", linestyle='', color='black')
 
 	#twin axes on right side
	ax2 = ax1.twinx()
	color = 'blue'
	ax2.set_ylabel('Analog ToT [us]', color = color)
	ax2.errorbar(injections, anaT, yerr=errT, marker="o", linestyle='', color=color)
	ax2.tick_params(axis ='y', labelcolor = color)
	
	if savePlts:
		saveName = f"compareAnalogInjScan_chip{c}"
		plt.savefig(f"{saveDir}{saveName}.png")
	else:
		plt.show()
		
	plt.clf()
	plt.plot(injections,np.array(anaT)/np.array(anaP), marker="o")
	plt.xlabel("Injection voltage [V]")
	plt.ylabel("Ratio ToT/peakHeight [us/V]")
	plt.title(f"Chip {c}")
	if savePlts:
		saveName = f"compareAnalogRatio_chip{c}"
		plt.savefig(f"{saveDir}{saveName}.png")
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
	if analogIn:
		time = 1.8 if chip==602 else 1.9
		anaDF = adh.getDF(adataDir+'chip'+str(chip)+f'_injScan_10s_combined_0.3Vinj_{time}min.h5py')
		anaDF.rename(columns={"AnalogToT": "ToT"},inplace=True)
		dfDict['analog'] = anaDF
	
	#get digital data and injection energies
	files = glob.glob(os.path.join(ddataDir, f'chip{chip}*.csv'))
	lenddir = len(ddataDir)
	#End execution if no files
	if len(files)==0:
		print("No files detected")
		return
	for f in files:
		f_nopath = f[lenddir:]
		#find part of file name containing 'inj' which indicates the injection voltage
		parts = f.split('_')
		injStr = [p for p in parts if "mVinj" in p]
		injV = injStr[0][:4] #eliminate 'inj', take first 3 places
		#Check whether 2 or 3 digit number
		if injV[-1]=="m":
			injV = injV[:-1]
		injs.append(round(float(injV)*0.001, 2))
		digiDF = ddh.getDF_singlePix(f)
		dfDict[f'digital_{0.001*float(injV):.1f}'] = digiDF
	
	#Analog injection plot
	if analogIn:
		if analogPulseHeight:
			analogRuns = adh.spliced_analog_data(dfDict['analog']['Peaks'], dfDict['analog']['Time'])
		else:
			analogRuns = adh.spliced_analog_data(dfDict['analog']['ToT'], dfDict['analog']['Time'])
		analogMeans = []
		analogSigs = []
		print("Create analog plots")
		for i,injV in enumerate(analogRuns):
			mean,sig = fitSaveGauss(injV, (i+1)*0.1, analog=True)
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
		mean,sig = fitSaveGauss(dfDict[df]['ToT(us)_row'], float(df.split('_')[1]))
		digitalMeans.append(mean)
		digitalSigs.append(sig)
	#Sort means/sigmas with respect to injs
	digitalMeans_sorted = [x for _,x in sorted(zip(injs,digitalMeans))]
	digitalSigs_sorted = [x for _,x in sorted(zip(injs,digitalSigs))]
	pltInjScan(digitalMeans_sorted, sorted(injs), digitalSigs_sorted,"Digital (row)")
		
	#Compare scans
	if analogIn and analogPulseHeight: #compare analog pulse vs analog ToT	
		#analogToTRuns = separateRuns(dfDict['analog']['Time'],dfDict['analog']['ToT'])
		analogToTRuns = adh.spliced_analog_data(dfDict['analog']['ToT'],dfDict['analog']['Time'])
		analogToTMeans = []
		analogToTSigs = []
		for i,injV in enumerate(analogToTRuns):
			mean,sig = fitSaveGauss(injV,(i+1)*0.001, analog=True, compare=True)
			analogToTMeans.append(mean)
			analogToTSigs.append(sig)
		print("Comparing analog data")
		compareAnalogInjScans(analogMeans, analogToTMeans, sorted(injs), analogSigs, analogToTSigs)
	elif analogIn: #compare analog and digital ToT
		print("Comparing analog and digital data")
		compareInjScans(analogMeans, digitalMeans_sorted, sorted(injs), analogSigs, digitalSigs_sorted)
	else:
		print("Only considered digital data - nothing to compare to")

	
#################################################################
# call main
#################################################################
if __name__ == "__main__":
	"""FOR INJECTION SCAN OVER ONE SINGLE PIXEL"""

	"""
	#new vs old low res v2 chips
	saveDir = os.getcwd()+"/plotsOut/newChipInjectionScans/" #hardcode location of dir for saving output plots - automatically saves
	ddataDir = "/Users/asteinhe/AstroPixData/digital/logInj/injectionScans_10s_chip602_chip604_chip401/"
	adataDir = "/Users/asteinhe/AstroPixData/astropixOut_tmp/v2/111622_amp1/"
	chip = [602, 604, 401]
	"""
	
	#post-irradiation June HI chips
	saveDir = os.getcwd()+"/plotsOut/lbnlIrradiated/" #hardcode location of dir for saving output plots - automatically saves
	ddataDir = "/Users/asteinhe/AstroPixData/digital/logInj/lbnl_HIbeam_prepAndPost/"
	adataDir = "/Users/asteinhe/AstroPixData/astropixOut_tmp/v2/111622_amp1/"
	chip = [601, 603]
	
	"""
	#high-res chips
	saveDir = os.getcwd()+"/plotsOut/newChipInjectionScans/HR3/dishidr0/" #hardcode location of dir for saving output plots - automatically saves
	ddataDir = "/Users/asteinhe/AstroPixData/digital/logInj/injectionScan_chipHR3/"
	adataDir = "/Users/asteinhe/AstroPixData/astropixOut_tmp/v2/111622_amp1/"
	chip = ['HR3']
	"""

	savePlts = False
	analogIn = True
	analogPulseHeight = False #if False, consider analog proxy ToT

	for c in chip:
		print(f"Running Chip {c}")
		main(c)