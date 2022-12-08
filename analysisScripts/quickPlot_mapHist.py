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
	
def fitGauss_array(data, rangeMax, namestr, fit, bins):

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
		saveName = f"{namestr}_hist_chip{str(chip)}"
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
	
def getCounts(df, isData):
	countArr = np.full([35, 35], 0)
	for index,evt in df.iterrows():
		try:
			if isData:
				countArr[int(evt['Locatn_row'])][int(evt['Locatn_col'])]+=1
			else:
				countArr[evt['Rows']][evt['Cols']]+=1
		except IndexError: #bad decoding - data hit outside of array size
			print(f"BAD DECODING - identified hit at row {evt['Locatn_row']} col {evt['Locatn_col']}")
			

	return countArr

def makePlots(data, rangeMax, title, namestr, fit=True, bins=40):
	mapFigMean=ddh.arrayVis(data, barRange=[0.,rangeMax], barTitle=title, invert=True)
	if args.savePlot:
		saveName = f"{namestr}_map_chip{str(chip)}"
		print(f"Saving {saveDir}{saveName}.png")
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.clf()
	else:
		plt.show()
	plt.clf()
	
	#fitGauss_array(data, rangeMax, namestr, fit, bins)
	
	
#################################################################
# main
#################################################################

def main(args):

	totArr = np.full([35, 35], np.nan)
	sigArr = np.full([35, 35], np.nan)
	isData = False

	#Get hits
	#df = ddh.getDF_singlePix(i, pix=[rVal,cVal])
	df=pd.read_csv(args.inputF)
	#If inputting a data file and not a list of pixel locations, then get out only good hits
	if 'payload' in df.keys(): 
		df = ddh.getDF_fullArr(args.inputF)
		isData = True	

	
	#Get counts
	countArr = getCounts(df, isData)
	
	makePlots(countArr, countArr.max(), "Masked pixels", "masked")
	
	"""
	#Fit distributions and get ToT mean/sigma
	mean,sig,r2 = fitGauss_pix(df['ToT(us)_row'],f"row{rVal},col{cVal}",cVal,rVal)
	totArr[cVal][rVal] = mean
	sigArr[cVal][rVal] = sig
				
	#Make plots - array map and histogram
	makePlots(r2Arr, 1., "goodness of fit R$^2$", "r2", fit=False)
	makePlots(totArr, 21., "mean ToT [us]", "totMean")
	"""
	
	
#################################################################
# call main
#################################################################
if __name__ == "__main__":

	saveDir = os.getcwd()+"/plotsOut/thresholdScan/chip604/noise_150mV" #hardcode location of dir for saving output plots
	dirPath = os.getcwd()[:-15] #go one directory above the current one where only scripts are held

	parser = argparse.ArgumentParser(description='Plot array map of input data (counts) and histogram of ToT of hits')
	parser.add_argument('-i', '--inputF', default='../noise/chip604/chip604_150mV_masked_noise_1min_20221205-105021.csv', required=False,  
        help='Input data file, type csv')
	parser.add_argument('-p', '--plotHist', action='store_true', default=False, required=False, 
		help='Create a histogram of full array ToT_row values. Default: False')
	parser.add_argument('-s', '--savePlot', action='store_true', default=False, required=False, 
		help='Save all plots (no display) to plotsOut/dacOptimization/arrayScan. Default: None (only displays, does not save)')
		

	parser.add_argument
	args = parser.parse_args()
	
	#find chip number from file name
	strToSplit=args.inputF.replace("/","_")
	parts=strToSplit.split('_')
	chipname = [p for p in parts if "chip" in p]
	chip=chipname[0][4:]
	
 	
	main(args)