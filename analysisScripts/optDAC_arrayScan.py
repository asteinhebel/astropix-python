import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os,sys, glob
import argparse

import digitalDataHelpers as ddh

#################################################################
# helper functions
#################################################################

def getRowCol(f):

	r,c = -1, -1
	
	parts=f.split('_')
	rStr = [p for p in parts if "row" in p]
	cStr = [p for p in parts if "col" in p]
	r = rStr[0][3:] #eliminate 'row'
	c = cStr[0][3:] #eliminate 'col'
	
	return r,c
	
def Gauss(x, A, mu, sigma):
    return A*np.exp(-(x-mu)**2/(2.0*sigma**2))
    
def fitHist(data,label,nmbBins):
	hist=plt.hist(data, nmbBins, range=[0,20.48], alpha=0.3, label=label) 
		#20.48 = max ToT value now with updated decoder clock tiem of 5ns
	ydata=hist[0]
	binCenters=hist[1]+((hist[1][1]-hist[1][0])/2)
	binCenters=binCenters[:-1]
	muGuess = binCenters[np.argmax(ydata)] #bin with most entries most likely to be near peak of distribution
	p0=[ydata.max(),muGuess,muGuess/2] #amp, mu, sig
	try:
		popt, pcov = curve_fit(Gauss, xdata=binCenters, ydata=ydata, p0=p0, absolute_sigma=True)
	except RuntimeError: #fit won't converge, close to zero but allows for division
		popt = [1e-32, 1e-32, 1e-32]
	
	return hist, popt
	
def getToTVals(dataDF):

	#Skip consideration of empty data frames (no matching row/col hits)
	if dataDF.empty:
		return -1,-1,-1,-1

	binSize=0.25 #0.25us bins
	nmbBins=int(40.96/2/binSize)
	
	hist_r, (amp_r, mean_r, std_r) = fitHist(dataDF['ToT(us)_row'],"row", nmbBins)
	hist_c, (amp_c, mean_c, std_c) = fitHist(dataDF['ToT(us)_col'],"col", nmbBins)
	
	#return fit parameters and abs. value of sigma
	return mean_r, mean_c, np.abs(std_r), np.abs(std_c)
	
def makePlots(dataIn,title,fname, invert:bool=False):

	dataHist=dataIn[~np.isnan(dataIn)]#remove NaNs to simplify histogram calculation
	#identify if plot should be on 0-100 or 0-20.5 scale from title
	if 'mean' or 'FWHM' in title:
		rnge=[0,21] #don't show empty datasets or outliers
	elif '%' in title:
		rnge=[0,100]
	elif 'Row/Col' in title:
		rnge=[0,2] #don't show empty datasets or outliers
	elif 'std' in title:
		rnge=[0,10] #don't show empty datasets or outliers
	else:
		rnge=[dataHist.min(),dataHist.max()]

	#Make array map
	mapFig=ddh.arrayVis(dataIn, barRange=rnge, barTitle=title, invert=True)
	if args.savePlot:
		titleSave=title.replace(" ", "")
		saveName = f"{fname}_map_{titleSave}"
		print(f"Saving {saveDir}{saveName}.png")
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.clf()
	else:
		plt.show()
	
	#make histogram of flattened dataIn#
	plt.hist(dataHist, range=rnge, bins=100, density=True)
	plt.xlabel(title)
	plt.tight_layout()
	if args.savePlot:
		titleSave=title.replace(" ", "")
		saveName = f"{fname}_hist_{titleSave}"
		print(f"Saving {saveDir}{saveName}.png")
		plt.savefig(f"{saveDir}{saveName}.png")
	else:
		plt.show()	
	
	
def histCompare(data1, data2, title, labels=None, leadName=None):

	data1Hist=data1[~np.isnan(data1)]#remove NaNs to simplify histogram calculation
	data2Hist=data2[~np.isnan(data2)]#remove NaNs to simplify histogram calculation
	plt.clf()
	
	#identify if plot should be on 0-100 scale from title
	if 'FWHM' in title:
		rnge=[0,20]
	elif '%' in title:
		rnge=[0,100]
	else:
		totmin = min(data1Hist.min(), data2Hist.min())
		totmax = max(data1Hist.max(), data2Hist.max())
		rnge=[totmin, totmax]
	hist1=plt.hist(data1Hist, range=rnge, bins=100, density=True, alpha=0.5, label=labels[0])
	hist2=plt.hist(data2Hist, range=rnge, bins=100, density=True, alpha=0.5,label=labels[1])
	plt.xlabel(title)
	plt.legend(loc='best')
	plt.tight_layout()
	if args.savePlot:
		titleSave=title.replace(" ", "")
		fname = leadName+"_" if leadName is not None else ""
		saveName = f"{fname}histComp_{titleSave}"
		print(f"Saving {saveDir}{saveName}.png")
		plt.savefig(f"{saveDir}{saveName}.png")
	else:
		plt.show()	


#################################################################
# main
#################################################################

def main(args):

	#Define whether default and/or optimized DAC data sets should be used
	boolDef, boolOpt = True, True
	dir2 = 1 if len(args.inputDir)>1 else 0
	fileDict = {"default": args.inputDir[0], "optimized": args.inputDir[dir2]}
	if args.plotDef and args.plotOpt:
		pass
	elif args.plotDef:
		boolOpt = False
		fileDict = {"default": args.inputDir[0]}
	elif args.plotOpt:
		boolDef = False
		fileDict = {"optimized": args.inputDir[0]}

	#dictionaries of data to compare default and optimized settings on same plot
	dict_bulkDF={}
	
	#Get data files for default OR optimized DACs, create plots for the bulk properties individually
	for item in fileDict.items():
		#identify files in input directory
		fname = item[0]
		inputDir = item[1]
		os.chdir(dirPath+inputDir)
		files = glob.glob(os.path.join('./', f'*{fname}*.csv'))
	
		#End execution if no files
		if len(files)==0:
			print("No files detected")
			return

		#DF to keep track of general properties of each file
		bulkDF = pd.DataFrame(files)
		lengthOrig=[]
		lengthMatch=[]
		lenR, lenC = [],[]
		row, col = [],[]
		tottrigs = []
		tot_std_r, tot_std_c = [],[]
		tot_mean_r, tot_mean_c = [],[]
		tot_ratio = []
	
		#DF dictionary to keep individual data from each run
		dfDict={}
		
		#Hard coded time of data run for rate calculation
		global tottime 
		tottime = 15 if "15s" in files[0] else 60 
	
		#Extract data from input files - store bulk properties in bulkDF and individual DFs in dfDict dictionary
		print("Getting data from all input files")
		for f in files:
			r,c = getRowCol(f) #find activated pixel
			dfIn, origLen, origR, origC, trigs = ddh.getDF_singlePix_extraVars(f, [r,c]) #get info about the full data run ("bulk") and dataframe with info about every trigger from that pixel
			dfDict[f'r{r}c{c}'] = dfIn
			mean_r, mean_c, std_r, std_c = getToTVals(dfIn) #get ToT distribution values
			row.append(r)
			col.append(c)
			lengthOrig.append(origLen)
			lengthMatch.append(len(dfIn)*2)
			lenR.append(origR)
			lenC.append(origC)
			tottrigs.append(trigs)
			tot_mean_r.append(mean_r)
			tot_mean_c.append(mean_c)
			tot_std_r.append(std_r)
			tot_std_c.append(std_c)

		#Fill DF of bulk properties
		bulkDF = bulkDF.join(pd.DataFrame({
			'row':row, 'col':col, 'origLength':lengthOrig, 
			'matchedLength':lengthMatch, 'origRows':lenR, 'origCols':lenC, 'origTrigs':tottrigs,
			'tot_mean_r':tot_mean_r, 'tot_mean_c':tot_mean_c,
			'tot_std_r':tot_std_r, 'tot_std_c':tot_std_c
		}))
	
		#Make 35x35 arrays containing the data from the DF
		origLengthArr = np.full([35, 35], np.nan)
		matchLengthArr = np.full([35, 35], np.nan)
		origCLengthArr = np.full([35, 35], np.nan)
		origTrigsArr = np.full([35, 35], np.nan)
		tot_mean_rArr = np.full([35, 35], np.nan)
		tot_mean_cArr = np.full([35, 35], np.nan)
		tot_std_rArr = np.full([35, 35], np.nan)
		tot_std_cArr = np.full([35, 35], np.nan)
		for index, row in bulkDF.iterrows():
			origLengthArr[int(row['row']),int(row['col'])]=int(row['origLength'])
			matchLengthArr[int(row['row']),int(row['col'])]=int(row['matchedLength'])
			origCLengthArr[int(row['row']),int(row['col'])]=int(row['origCols'])
			origTrigsArr[int(row['row']),int(row['col'])]=int(row['origTrigs'])
			tot_mean_rArr[int(row['row']),int(row['col'])]=float(row['tot_mean_r'])
			tot_mean_cArr[int(row['row']),int(row['col'])]=float(row['tot_mean_c'])
			tot_std_rArr[int(row['row']),int(row['col'])]=float(row['tot_std_r'])
			tot_std_cArr[int(row['row']),int(row['col'])]=float(row['tot_std_c'])
			
		#Convert pixels with no matched hits from ToT values of -1 to NaN so they are not plotted
		tot_mean_rArr[tot_mean_rArr<0] = np.NaN
		tot_mean_cArr[tot_mean_cArr<0] = np.NaN
		tot_std_rArr[tot_std_rArr<0] = np.NaN
		tot_std_cArr[tot_std_cArr<0] = np.NaN

		#Construct useful arrays for plotting
		rc_ratio = tot_mean_rArr/tot_mean_cArr
		rc_ratio[rc_ratio>20] = np.nan # If fit did not converge, ratio returns 1e32. Do not plot this value, set these pixels to NaN
		rc_ratio[rc_ratio<1e-5] = np.nan # If fit did not converge, ratio returns 1e32. Do not plot this value, set these pixels to NaN
		enres_c = 2.355 * tot_std_cArr / tot_mean_cArr *100
		enres_r = 2.355 * tot_std_rArr / tot_mean_rArr *100
		enres_c[enres_c>20] = np.nan # If fit did not converge, ratio returns 1e32. Do not plot this value, set these pixels to NaN
		enres_r[enres_r>20] = np.nan # If fit did not converge, ratio returns 1e32. Do not plot this value, set these pixels to NaN


		#Make plots of bulk properties
		makePlots(origLengthArr,"Original Number of Hits",fname,invert=True)
		makePlots(matchLengthArr,"Matched Number of Hits",fname,invert=True)
		makePlots(origLengthArr-matchLengthArr,"Unmatched Number of Hits",fname,invert=True)
		makePlots(origTrigsArr/tottime,"Hit Rate [Hz]",fname,invert=True)
		makePlots(matchLengthArr/origLengthArr*100.,"Matched % of Hits",fname,invert=True)
		makePlots(origCLengthArr/origLengthArr*100.,"% of Orig Hits from Columns",fname,invert=True)
		makePlots((origLengthArr-origCLengthArr)/origLengthArr*100.,"% of Orig Hits from Rows",fname,invert=True)
		makePlots(tot_mean_rArr,"Row ToT mean",fname,invert=True)
		makePlots(tot_mean_cArr,"Col ToT mean",fname,invert=True)
		makePlots(tot_std_rArr,"Row ToT std",fname,invert=True)
		makePlots(tot_std_cArr,"Col ToT std",fname,invert=True)
		makePlots(rc_ratio,"RowCol ToT mean",fname,invert=True) 
		makePlots(enres_c,"Col energy resolution FWHM [%]",fname,invert=True) 
		makePlots(enres_r,"Row energy resolution FWHM [%]",fname,invert=True) 
		
		#Combined plots of bulk properties
		binCenters=np.arange(0.5,100,1)	
		legLabels=["Col hits", "Row hits"]
		#Raw percent of row and col hits
		histCompare(origCLengthArr/origLengthArr*100., (origLengthArr-origCLengthArr)/origLengthArr*100., "% of raw hits", labels=legLabels, leadName=fname)
		#ToT mean from row and col hits
		histCompare(tot_mean_cArr, tot_mean_rArr, "mean ToT [us]", labels=legLabels, leadName=fname)
		#ToT sigma from row and col hits
		histCompare(tot_std_cArr, tot_std_rArr, "std ToT [us]", labels=legLabels, leadName=fname)
		#energy resolution from row and col hits
		histCompare(enres_c, enres_r, "Energy resolution (FWHM) [%]", labels=legLabels, leadName=fname)

		#Add bulk DFs to dictionary for future potential use
		dict_bulkDF[fname] = bulkDF

	#Create plots comparing default and optimized settings on same axes
	if boolDef and boolOpt:
		print("Considering default vs optimized plots")
		ky=list(dict_bulkDF.keys())
		percMatching = [dict_bulkDF[k]['matchedLength']/dict_bulkDF[k]['origLength']*100 for k in ky]
		rate = [dict_bulkDF[k]['origTrigs']/tottime for k in ky]
		mean_ratio = np.array([dict_bulkDF[k]['tot_mean_r']/dict_bulkDF[k]['tot_mean_c'] for k in ky])
		mean_ratio[mean_ratio>20] = np.nan # If fit did not converge, ratio returns 1e32. Do not plot this value, set these pixels to NaN
		mean_ratio[mean_ratio<1e-5] = np.nan # If fit did not converge, ratio returns 1e32. Do not plot this value, set these pixels to NaN
		energyres_r = [2.355 * dict_bulkDF[k]['tot_std_r'] / dict_bulkDF[k]['tot_mean_r'] *100 for k in ky]
		energyres_c = [2.355 * dict_bulkDF[k]['tot_std_c'] / dict_bulkDF[k]['tot_mean_c'] *100 for k in ky]

		histCompare(percMatching[0], percMatching[1], "% Matching Hits", labels=ky)
		histCompare(rate[0], rate[1], "Raw rate [Hz]", labels=ky)
		histCompare(dict_bulkDF[ky[0]]['tot_mean_c'],dict_bulkDF[ky[1]]['tot_mean_c'], "Mean ToT col [us]", labels=ky)
		histCompare(dict_bulkDF[ky[0]]['tot_mean_r'],dict_bulkDF[ky[1]]['tot_mean_r'], "Mean ToT row [us]", labels=ky)
		histCompare(dict_bulkDF[ky[0]]['tot_std_c'],dict_bulkDF[ky[1]]['tot_std_c'], "std ToT col [us]", labels=ky)
		histCompare(dict_bulkDF[ky[0]]['tot_std_r'],dict_bulkDF[ky[1]]['tot_std_r'], "std ToT row [us]", labels=ky)
		histCompare(mean_ratio[0], mean_ratio[1], "ToT mean RowCol", labels=ky)
		histCompare(energyres_r[0], energyres_r[1], "Energy resolution FWHM row [%]", labels=ky)
		histCompare(energyres_c[0], energyres_c[1], "Energy resolution FWHM col [%]", labels=ky)

	
#################################################################
# call main
#################################################################
if __name__ == "__main__":

	saveDir = os.getcwd()+"/plotsOut/dacOptimization/arrayScan/cadmium/" #hardcode location of dir for saving output plots
	dirPath = os.getcwd()[:-15] #go one directory above the current one where only scripts are held

	parser = argparse.ArgumentParser(description='Plot array data comparing default and optimized comparator DACs')
	parser.add_argument('-i', '--inputDir', default='', required=True, nargs='+',  
        help='Directory containing data files, from main git repo space. Can provide one or two directories - if two, send default first.')
	parser.add_argument('-d', '--plotDef', action='store_true', default=False, required=False, 
        help='Consider default DACs ONLY. If no -o or -d, plot both. Default: False')
	parser.add_argument('-o', '--plotOpt', action='store_true', default=False, required=False, 
		help='Consider optimized DACs ONLY. If no -o or -d, plot both. Default: False')
	parser.add_argument('-s', '--savePlot', action='store_true', default=False, required=False, 
		help='Save all plots (no display) to plotsOut/dacOptimization/arrayScan. Default: None (only displays, does not save)')

	parser.add_argument
	args = parser.parse_args()
	
	if len(args.inputDir) > 2:
  	  sys.exit('Argument --inputDir takes one or two values')
 	
	main(args)