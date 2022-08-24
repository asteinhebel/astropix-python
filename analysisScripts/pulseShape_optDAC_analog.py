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

def new_dac_i (arr):
	#identify each different setting in run
	#if more than 1s between triggers, then it's a new setting
	diffArr=np.diff(arr)
	indexArray=np.where(diffArr>1)
	indexArray=np.insert(indexArray,0,0)
	return indexArray

def get_average_traces( filename ):

	f = h5py.File(filename, 'r')
	traces = f['run1'] #baseline subtracted already
	time = f['run1_trigTime']
	mean=[]

	newDac=new_dac_i(time)
	for i in range(1,len(newDac)):
		#smooth curve
		mean.append(np.mean(traces[newDac[i-1]:newDac[i]], axis = 0)[0::50])
		
	#Remove sections that do not have recorded traces (ie when number of recorded traces was exceeded during data taking but pulse heights were still recorded)
	mean=np.array(mean)
	noNan=np.array([~np.isnan(i[0]) for i in mean])
	
	return mean[noNan]
	
def makeTitle(pixDir, txtin, ext='.png'):
	if len(args.title)>0:
		filestr=args.title+"_"
	else:
		filestr=""
	
	fname=f'{dataDir}{pixDir}/{filestr}{txtin}{ext}'
	return fname
	
def get_baseline_plt(filename, labels, pixDir):

	f = h5py.File(filename, 'r')
	time = f['run1_trigTime']
	baseline = f['run1']
	baseline=baseline[:,0:2000]
	
	#VARIANCE - find mean, calculate each value's difference from mean, add in quadrature, divide by total number of entries
	###calculated using every value
	#STD - sqrt(variance)
	#Expect mean of baseline at 0 (baseline subtracted)
	varArr=[np.var(trace, ddof=1) for trace in baseline] 
	rmsArr=[np.std(trace, ddof=1) for trace in baseline] 
	xVar=np.linspace(0,max(varArr),50)
	xRms=np.linspace(0,max(rmsArr),50)

	#sort by DAC config
	newDac=new_dac_i(time)
	for i in range(1,len(newDac)):
		hist,binEdges=np.histogram(varArr[newDac[i-1]:newDac[i]], bins=xVar)
		plt.hist(varArr[newDac[i-1]:newDac[i]], bins=xVar, alpha=0.4, label=labels[i-1])

	plt.xlabel('Std Dev of DC baseline')
	plt.ylabel('Counts')
	plt.title(args.title)
	plt.legend(loc='best')
	plot=plt.gcf() #get current figure - saves fig in case savePlt==True
	plt.show() #creates new figure for display
	plot.savefig(makeTitle(pixDir,'stdBaselineHist'))

	for i in range(1,len(newDac)):
		hist,binEdges=np.histogram(rmsArr[newDac[i-1]:newDac[i]], bins=xRms)
		plt.hist(rmsArr[newDac[i-1]:newDac[i]], bins=xRms, alpha=0.4, label=labels[i-1])

	plt.xlabel('Variance of DC baseline')
	plt.ylabel('Counts')
	plt.title(args.title)
	plt.legend(loc='best')
	plot=plt.gcf() #get current figure - saves fig in case savePlt==True
	plt.show() #creates new figure for display
	plot.savefig(makeTitle(pixDir,'varBaselineHist'))
	
#################################################################
# main
#################################################################

def main(args):

	#get analog data
	pixDir = args.inputAnalog[:9]
	anaDF = adh.getDF(dataDir+args.inputAnalog)
	anaDF.rename(columns={"AnalogToT": "ToT"},inplace=True)

	#Add column for scaled timing relative to whatever was the first measurement
	anaDF['Time_scale']=[t-anaDF['Time'].iloc[0] for t in anaDF['Time']]

	#Calculate rates
	anaRate = len(anaDF) / (anaDF['Time_scale'].iloc[-1])
	print(f"Analog hit rate = {anaRate:.3f} Hz")
	
	
	#plot average trace at each DAC setting
	labels=[i for i in range(1,10)]
	#labels=[1+i*8 for i in range(8)]
	avePlots=get_average_traces(dataDir+args.inputAnalog)
	for i,p in enumerate(avePlots):
		plt.plot(p, label=str(labels[i]))
	plt.xlabel("Time [us]")
	plt.ylabel("Pulse [V]")
	plt.legend(loc="best")
	plt.title(args.title)
	plot=plt.gcf() #get current figure - saves fig in case savePlt==True
	plt.show() #creates new figure for display
	plot.savefig(makeTitle(pixDir,'aveAnalogTraces'))
	
	if args.noise:
		#histograms of noise on DC baseline for each DAC setting
		get_baseline_plt(dataDir+args.inputAnalog,labels, pixDir)
		
		#NEED TO QUANTIFY BETTER

#################################################################
# call main
#################################################################
if __name__ == "__main__":

	dataDir = "/Users/asteinhe/AstroPixData/digital/logInj/dacScan/"
	
	parser = argparse.ArgumentParser(description='Plot Digital Data')
	parser.add_argument('-a', '--inputAnalog', default='', required=True,
        help='Input analog file (one run over multiple DAC values)')
	parser.add_argument('-t', '--title', default='', required=False,
        help='Title to display on graph')
	parser.add_argument('-p', '--pixel', action='store', default=[0,0], type=int, nargs=2,
        help =  'Digital pixel that was enabled in data collection - only return digital data from hits from thsi pixel. Default: (0,0)')
	parser.add_argument('-n', '--noise', action='store_true', default=False, required=False, 
        help='Plot histograms of STD/variance of DC baseline of analog. Default: False')
        
	parser.add_argument
	args = parser.parse_args()
    
	main(args)
