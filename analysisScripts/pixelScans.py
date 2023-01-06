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
def find_nearest(array, value):
	"""Find closest element in array to an input value
	Return: value of array element that is closest to the input value"""
	array = np.asarray(array)
	idx = (np.abs(array - value)).argmin()+1
	return idx
    
def spliced_analog_hr(arr, time, window=1050):
	"""Splice high res analog data file into separate parts dependent on setting changes
			Define by time value where setting changes
	Return: 2d list containing the data points (not timing) for each different setting"""

	splice_val=np.array([window*i+time[0] for i in range(36)])
	splice_i=[find_nearest(time,s)+5 for s in splice_val] #try to get just the data run - cuts into the ideal 30s
	
	splice_end=[s+100 for s in splice_i]#try to get just the data run - cuts into the ideal 30s
	splice_end[0]=splice_i[0]+245 #longer wait
	splice_end=np.delete(splice_end,-1)
	splice_end[-1]=len(time)-1
	
	arr = np.array(arr)
	splice_arr = [arr[splice_i[i]:splice_end[i]] for i in range(len(splice_i)-1)] #keep dattime worth of seconds of data for each setting

	return splice_arr
	
def fitSaveGauss(data,title,extraArgs,nmbBins=50, fit=True):
	"""Clean data and fit to a Gaussian. Plot (save, if applicable) histogram and associated Gaussian
		If extraArgs=[colNumb, rowNmb], considers data from one pixel (defines cleaning and naming)
		If extraArgs=[plotMaxRange, nmbBins, namingString, namingString2], considers data from full array (defines cleaning and naming)
	Return: mean and sigma parameters of Gaussian fit
			R2 goodness of fit"""

	if len(extraArgs)==2:
		pix=True
		r=extraArgs[0]
		c=extraArgs[1]
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
		xspace = np.linspace(min(hist[1]), max(hist[1]),100)
		plt.plot(xspace, clch.Gauss(xspace, amp,mean,sig)) 	
		plt.plot([], [], ' ', label=f"Amp={amp:.2f}, $\mu$={mean:.3f}, $\sigma$={sig:.3f}")
		plt.plot([], [], ' ', label=f"R$^2$={r2:.3f}")
		plt.legend(loc='best')

	#label plots
	if not analog:
		plt.xlabel("Digital ToT [us]")
	elif args.peaksAnalog:
		plt.xlabel("Analog Pulse Height [V]")
		saveName+="_analogPeak"
	else:
		plt.xlabel("Analog ToT [us]")
		saveName+="_analogToT"
		
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
	
	mapFigMean=plth.arrayVis(data, barRange=[0.,rangeMax], barTitle=title, invert=True)
	if analog and args.peaksAnalog:
		extraname+="_analogPeak"
	elif analog:
		extraname+="_analogToT"
		
	if args.savePlot:
		saveName = f"{namestr}_map_chip{str(chip)}{extraname}"
		print(f"Saving {saveDir}{saveName}.png")
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.clf()
	else:
		plt.show()

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
	files_in = sorted(glob.glob(f"*.csv")) #look for csv
	
	#variables for plot saving/naming/labling
	rnge=21.
	lbel="totMean"
	ttle="mean ToT [us]"
	rnge_sig=10.
	lbel_sig="totSig"
	ttle_sig="ToT sigma [us]"
	if args.peaksAnalog:
		rnge=0.4
		lbel="peakMean"
		ttle="mean peak height[V]"
		rnge_sig=0.05
		lbel_sig="peakSig"
		ttle_sig="peak height sigma [V]"
	
	#digital data
	if len(files_in)>0: 
		for f in files_in: 
			#get all txt files in datadir in alphabetic order ('sorted' alphabatizes)
			parts=f.split('_')
			cStr = [p for p in parts if "col" in p]
			cVal = int(cStr[0][3:]) #eliminate 'col'
			rStr = [p for p in parts if "row" in p]
			rVal = int(rStr[0][3:]) #eliminate 'row'
			#Get hits
			df = ddh.getDF_singlePix(f, pix=[rVal,cVal])
			#Fit distributions and get ToT mean/sigma
			mean,sig,r2 = fitSaveGauss(df['ToT(us)_row'],f"row{rVal},col{cVal}",[rVal,cVal])	

			totArr[rVal][cVal] = mean
			sigArr[rVal][cVal] = sig
			r2Arr[rVal][cVal] = r2
	#no csv files - must be analog data
	else: 
		#get analog file and clean hits
		anaFile = glob.glob(f"*pixelScan*.h5py")
		anaDF = adh.getDF(anaFile[0])
		"""
		if args.peaksAnalog:
			analogData = adh.spliced_analog_data(anaDF['Peaks'], anaDF['Time'])
		else:
			analogData = adh.spliced_analog_data(anaDF['AnalogToT'], anaDF['Time'])
		"""
		dfseries = "Peaks" if args.peaksAnalog else "AnalogToT"
		if args.highresAnalog:
			analogData = spliced_analog_hr(anaDF[dfseries], anaDF['Time'])
		else:
			analogData = adh.spliced_analog_data(anaDF[dfseries], anaDF['Time'])
		#Fit distributions and get mean/sigma
		#all analog values from row 0
		rVal=0
		for cVal,dat in enumerate(analogData):
			mean,sig,r2 = fitSaveGauss(dat,f"row{rVal},col{cVal}",[rVal,cVal])
			totArr[rVal][cVal] = mean
			sigArr[rVal][cVal] = sig
			r2Arr[rVal][cVal] = r2
			
	#Make plots - array map and histogram
	makePlots(r2Arr, 1., "goodness of fit R$^2$", "r2", extraname, fit=False)
	if args.cleanData is not None:
		makePlots(totArr, rnge, ttle, lbel, extraname, r2cleaning=[float(args.cleanData),r2Arr])
		makePlots(sigArr, rnge_sig/15., ttle_sig, lbel_sig, extraname, bins=80, r2cleaning=[float(args.cleanData),r2Arr])
	else:
		makePlots(totArr, rnge, ttle, lbel, extraname)
		makePlots(sigArr, rnge_sig, ttle_sig, lbel_sig, extraname, bins=80)


#################################################################
# call main
#################################################################
if __name__ == "__main__":

	saveDir = os.getcwd()+"/plotsOut/pixelScan_0.3Vinjection/chipHR3/analog/" #hardcode location of dir for saving output plots
	dirPath = os.getcwd()[:-15] #go one directory above the current one where only scripts are held

	parser = argparse.ArgumentParser(description='Consider scans of every pixel in array - look at individual and bulk properties of digital data')
	parser.add_argument('-i', '--inputDir', default='../logInj/chip602_pixelScan_0.3Vinj/', required=False,  
        help='Directory containing repos of data files, from main git repo space.')
	parser.add_argument('-m', '--masks', action='store_true', default=False, required=False, 
		help='WIP - Disregard plotting pixels that should be masked. Input a csv file of row/col values of masked pixels. Default: None')
	parser.add_argument('-s', '--savePlot', action='store_true', default=False, required=False, 
		help='Save all plots (no display) to plotsOut/dacOptimization/arrayScan. Default: None (only displays, does not save)')
	parser.add_argument('-c', '--cleanData', default=None, required=False, 
		help='Plot only bulk values that pass an R2 requirement. Give min r2 value as input here. Default: None')
	parser.add_argument('-p', '--peaksAnalog', action='store_true', default=False, required=False, 
		help='If analog data provided, consider pulse height values. If False, consider analog ToT proxy. Default:False')
	parser.add_argument('-hr', '--highresAnalog', action='store_true', default=False, required=False, 
		help='File 120722_amp1/chipHR3_20V_pixelScan_0.3Vinj_row0_combined_0.3Vinj_720min.h5py was taken in conjunction with digital data and loops over every pixel by column. This option indicates that long periods of crosstalk should be avoided (when injection is not into row0) and requires conditions on subsequent data points ot identify new row0 pixels rather than a time difference. If False, separate analog data from pixels by looking for difference in triggers of 1.25s. Default:False')
	

	parser.add_argument
	args = parser.parse_args()
	
	#find chip number from file name
	analog=False
	strToSplit=args.inputDir.replace("/","_")
	parts=strToSplit.split('_')
	if 'v2' in parts: #input analog files - isolate which are relevant and get chip from file name
		analog=True
		f_in = glob.glob(f"{args.inputDir}/*pixelScan*.h5py")
		strToSplit=f_in[0].replace("/","_")
		parts=strToSplit.split('_')
		chipname = [p for p in parts if "chip" in p]
	else: #input digital files - one directory where all contained datasets are used, get chip from dir name
		chipname = [p for p in parts if "chip" in p]
	chip=chipname[0][4:]
 	
	main(args)