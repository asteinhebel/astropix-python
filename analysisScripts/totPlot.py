import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os,sys
import argparse

import digitalDataHelpers as ddh
from scipy.optimize import curve_fit



#################################################################
# helper functions
#################################################################

def Gauss(x, A, mu, sigma):
    return A*np.exp(-(x-mu)**2/(2.0*sigma**2))
    
def fitHist(data,label,nmbBins):
	hist=plt.hist(data, nmbBins, alpha=0.3, label=label)
	ydata=hist[0]
	binCenters=hist[1]+((hist[1][1]-hist[1][0])/2)
	binCenters=binCenters[:-1]
	popt, pcov = curve_fit(Gauss, xdata=binCenters, ydata=ydata, bounds=(0,np.inf), maxfev=5000, absolute_sigma=True)
	return hist, popt

#################################################################
# main
#################################################################

def main(args):

	#get input files and labels out of input file
	try:
		with open(args.inputF) as f:
			lines = np.loadtxt(f, dtype='str')
			filesIn = lines[:,0]
			labels = lines [:,2] #also acts as keys for dictionary
	except FileNotFoundError:
		filesIn = [args.inputF]
		labels = [""]

	# dictionary to store all dataframes
	dfDict = {} 
	for i,f in enumerate(filesIn):
		if f[-3:] == "csv":
			dfDict[labels[i]] = ddh.getDF("csv/"+f)
		else: #is log and need to generate csv
			fi=ddh.reduceFile(dirPath+f)
			dfDict[labels[i]] = ddh.getDF(fi)	
			

	#plots involving ToT
	#plot and fit ToT for all input files
	nmbBins=int(40.96/args.binSize)
	
	mean=[]
	for key in dfDict.keys():
		hist, fit = fitHist(dfDict[key]['ToT(us)_row'].append(dfDict[key]['ToT(us)_col']),key+" "+args.legend, nmbBins)
		mean.append(fit[1])
		xspace=np.linspace(hist[1][0],hist[1][-1], len(hist[1])*10)
		if args.scanInj:
			plt.plot(xspace, Gauss(xspace, *fit))  
			plt.title(f"{key} V Injection")
			plt.xlabel('ToT (us)')
			plt.ylabel('counts')
			plt.show()	
	
	if args.basicPlots:
		for key in dfDict.keys():
			plt.clf()
			plt.plot( dfDict[key]["ToT(us)_row"], dfDict[key]['ToT(us)_col'], ".", alpha=0.5  )
			plt.title(key)
			plt.xlabel('row ToT duration [us]')
			plt.ylabel('column ToT duration [us]')
			x=np.arange(40.96)
			plt.plot(x, 'b')
			plt.show()
	
			plt.clf()
			plt.plot(dfDict[key]['ToT(us)_row']/dfDict[key]['ToT(us)_col'],"o")
			plt.title(key)
			plt.xlabel('Triggered point')
			plt.ylabel('Ratio row/col ToT')
			plt.axhline(y=1, color='r')
			plt.show()
			
			ratio=np.array(dfDict[key]['ToT(us)_row']/dfDict[key]['ToT(us)_col'])
			outliers=np.where((ratio<0.5)|(ratio>1.5))
			print(dfDict[key].loc[outliers])
	
			plt.clf()
			plt.hist(dfDict[key]['ToT(us)_row'].append(dfDict[key]['ToT(us)_col']),nmbBins,fc=(0,0,1,1), label="All")
			plt.hist(dfDict[key]['ToT(us)_row'],nmbBins,fc=(1,0,0,0.5),label="Row")
			plt.hist(dfDict[key]['ToT(us)_col'],nmbBins,fc=(0,1,0,0.5),label="Col")
			plt.xlabel('ToT (us)')
			plt.ylabel('Counts')
			plt.legend(loc="best")
			plt.show()	
	
	if args.scanInj:
		x=[0.2+(i*0.1) for i in range(len(dfDict.keys()))]
		plt.plot(x,mean,marker="o")
		plt.xlabel("Injected voltage [V]")
		plt.ylabel("Average ToT [us]")
		plt.show()
		
	if args.totOverlay:
		#plot overlaid ToT histograms
		plt.xlabel('ToT (us)')
		plt.ylabel('Counts')
		plt.legend(loc="best")
		plt.show()
		
	if args.timestmp:
		plt.clf()
		for key in dfDict.keys():
			plt.scatter(dfDict[key]['NEvent'],dfDict[key]['tStamp'],label=key+" "+args.legend)
		plt.xlabel('Event number')
		plt.ylabel('Timestamp')
		plt.legend(loc='best')
		plt.show()


if __name__ == "__main__":

	dirPath=os. getcwd()[:-15] #go one directory above the current one where only scripts are held

	parser = argparse.ArgumentParser(description='Plot Digital Data')
	parser.add_argument('-i', '--inputF', default='', required=True,
        help='Input .txt containing location of data files to compare AND a label for each file semicolon deliminated OR command line path to single file, separated by new lines')
	parser.add_argument('-s', '--scanInj', action='store_true', default=False, required=False, 
        help='Plot average ToT at each point along injection scan. Default: False')
	parser.add_argument('-t', '--timestmp', action='store_true', default=False, required=False, 
        help='Plot Overlaid plots of timestamp values. Default: False')
	parser.add_argument('-o', '--totOverlay', action='store_true', default=False, required=False, 
        help='Plot Overlaid plots ToT. Default: False')
	parser.add_argument('-p', '--basicPlots', action='store_true', default=False, required=False, 
        help='Plot ToT and row vs col hit plots for eaach input. Default: False')
	parser.add_argument('-b','--binSize', action='store', default = 1.0, type=float,
        help = 'Bin size for ToT plotting (in us). Default: 1us')
	parser.add_argument('-l', '--legend', default='', required=False,
        help='Additional input for legend (ex units)')

	parser.add_argument
	args = parser.parse_args()
    
	main(args)
    
    
	"""
	
	#filesIn=["chip1_2min_DisHiDr0_analogPaired_0.3_injection_20220609-130531.csv","chip1_2min_DisHiDr1_analogPaired_0.3_injection_20220609-131435.csv","chip1_2min_DisHiDr0_analogPaired_1.0_injection_20220609-130749.csv","chip1_2min_DisHiDr1_analogPaired_1.0_injection_20220609-131027.csv"]
	#labels=["0.3V, 0","0.3V, 1","1.0V, 0","1.0V, 1"]
	
	filesIn=["logInj/chip1_2min_DisHiDr0_clkDiv10_analogPaired_0.3_injection_20220609-140916.log","logInj/chip1_2min_DisHiDr0_clkDiv50_analogPaired_0.3_injection_20220609-140650.log","logInj/chip1_2min_DisHiDr0_clkDiv100_analogPaired_0.3_injection_20220609-135612.log","logInj/chip1_2min_DisHiDr0_clkDiv150_analogPaired_0.3_injection_20220609-134908.log","logInj/chip1_2min_DisHiDr0_clkDiv200_analogPaired_0.3_injection_20220609-134641.log","logInj/chip1_2min_DisHiDr0_analogPaired_0.3_injection_20220609-130531.log"]
	#filesIn=["logInj/chip1_2min_DisHiDr0_clkDiv10_analogPaired_1.0_injection_20220609-141134.log","logInj/chip1_2min_DisHiDr0_clkDiv50_analogPaired_1.0_injection_20220609-140433.log","logInj/chip1_2min_DisHiDr0_clkDiv100_analogPaired_1.0_injection_20220609-135353.log","logInj/chip1_2min_DisHiDr0_clkDiv150_analogPaired_1.0_injection_20220609-135126.log","logInj/chip1_2min_DisHiDr0_clkDiv200_analogPaired_1.0_injection_20220609-134420.log","logInj/chip1_2min_DisHiDr0_analogPaired_1.0_injection_20220609-130749.log"]
	#filesIn=["logInj/chip1_2min_DisHiDr1_clkDiv10_analogPaired_0.3_injection_20220609-131933.log","logInj/chip1_2min_DisHiDr1_clkDiv50_analogPaired_0.3_injection_20220609-133016.log","logInj/chip1_2min_DisHiDr1_clkDiv100_analogPaired_0.3_injection_20220609-132628.log","logInj/chip1_2min_DisHiDr1_clkDiv150_analogPaired_0.3_injection_20220609-133715.log","logInj/chip1_2min_DisHiDr1_clkDiv200_analogPaired_0.3_injection_20220609-133935.log","logInj/chip1_2min_DisHiDr1_analogPaired_0.3_injection_20220609-131435.log"]
	#filesIn=["logInj/chip1_2min_DisHiDr1_clkDiv10_analogPaired_1.0_injection_20220609-132150.log","logInj/chip1_2min_DisHiDr1_clkDiv50_analogPaired_1.0_injection_20220609-133242.log","logInj/chip1_2min_DisHiDr1_clkDiv100_analogPaired_1.0_injection_20220609-132410.log","logInj/chip1_2min_DisHiDr1_clkDiv150_analogPaired_1.0_injection_20220609-133458.log","logInj/chip1_2min_DisHiDr1_clkDiv200_analogPaired_1.0_injection_20220609-134153.log","logInj/chip1_2min_DisHiDr1_analogPaired_1.0_injection_20220609-131027.log"]
	labels=["10","50","100","150","200","255"]
	
	#filesIn=["source/chip602_Americium-241_90min_pix00_100mV_beamDigital_20220713-134207.csv"]
	
	#filesIn=["logInj/chip2_2min_analogPaired_0.2_injection_20220609-153604.log","logInj/chip2_2min_analogPaired_00_0.3_injection_20220609-102112.log","logInj/chip2_2min_analogPaired_0.4_injection_20220609-153348.log","logInj/chip2_2min_analogPaired_0.5_injection_20220609-153130.log","logInj/chip2_2min_analogPaired_00_0.6_injection_20220609-102327.log","logInj/chip2_2min_analogPaired_0.7_injection_20220609-152912.log","logInj/chip2_2min_analogPaired_0.8_injection_20220609-152656.log","logInj/chip2_2min_analogPaired_00_0.9_injection_20220609-102554.log","logInj/chip2_2min_analogPaired_1.0_injection_20220609-152435.log","logInj/chip2_2min_analogPaired_1.1_injection_20220609-152221.log","logInj/chip2_2min_analogPaired_00_1.2_injection_20220609-102829.log","logInj/chip2_2min_analogPaired_1.3_injection_20220609-152005.log","logInj/chip2_2min_analogPaired_1.4_injection_20220609-151746.log","logInj/chip2_2min_analogPaired_1.5_injection_20220609-151529.log"]
	#labels=["0.2","0.3","0.4","0.5","0.6","0.7","0.8","0.9","1.0","1.1","1.2","1.3","1.4","1.5"]
	
	"""
