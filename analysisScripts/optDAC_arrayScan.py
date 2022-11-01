import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
	hist=plt.hist(data, nmbBins, alpha=0.3, label=label)
	ydata=hist[0]
	binCenters=hist[1]+((hist[1][1]-hist[1][0])/2)
	binCenters=binCenters[:-1]
	muGuess = np.mean(np.array(ydata))
	p0=[200,muGuess,muGuess/2] #amp, mu, sig
	popt, pcov = curve_fit(Gauss, xdata=binCenters, ydata=ydata, p0=p0, absolute_sigma=True)
	return hist, popt
	
def makePlots(dataIn,title,fname, invert:bool=False):

	#Make array map
	mapFig=ddh.arrayVis(dataIn, barTitle=title, invert=True)
	if args.savePlot:
		titleSave=title.replace(" ", "")
		saveName = f"{fname}_map_{titleSave}"
		print(f"Saving {saveDir}{saveName}.png")
		mapFig.savefig(f"{saveDir}{saveName}.png")
		mapFig.clf()
	else:
		mapFig.show()
	
	#<make histogram of dataIn>#
	dataHist=dataIn[~np.isnan(dataIn)]#remove NaNs to simplify histogram calculation
	hist=plt.hist(dataHist, bins=100, density=True)
	plt.xlabel(title)
	if args.savePlot:
		titleSave=title.replace(" ", "")
		saveName = f"{fname}_hist_{titleSave}"
		print(f"Saving {saveDir}{saveName}.png")
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.clf()
	else:
		plt.show()	
	
	return hist

#################################################################
# main
#################################################################

def main(args):

	boolDef, boolOpt = True, True
	if args.plotDef and args.plotOpt:
		pass
	elif args.plotDef:
		boolOpt = False
		fname = "default"
	elif args.plotOpt:
		boolDef = False
		fname = "optimized"
		
	print(args.savePlot)
	
	#identify files in input directory
	os.chdir(args.inputDir)
	files = glob.glob(os.path.join('./', f'*{fname}*.csv'))
	
	#files=files[:5]
	
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
	
	#DF dictionary to keep individual data from each run
	dfDict={}
	
	#Extract data from input files - store bulk properties in bulkDF and individual DFs in dfDict dictionary
	print("Getting data from all input files")
	for f in files:
		r,c = getRowCol(f)
		dfIn, origLen, origR, origC = ddh.getDF_singlePix_extraVars(f, [r,c])
		dfDict[f'r{r}c{c}'] = dfIn
		row.append(r)
		col.append(c)
		lengthOrig.append(origLen)
		lengthMatch.append(len(dfIn)*2)
		lenR.append(origR)
		lenC.append(origC)

	#Fill DF of bulk properties
	bulkDF = bulkDF.join(pd.DataFrame({
		'row':row, 'col':col, 'origLength':lengthOrig, 
		'matchedLength':lengthMatch, 'origRows':lenR, 'origCols':lenC
	}))
	
	origLengthArr = np.full([35, 35], np.nan)
	matchLengthArr = np.full([35, 35], np.nan)
	origCLengthArr = np.full([35, 35], np.nan)
	for index, row in bulkDF.iterrows():
		origLengthArr[int(row['row']),int(row['col'])]=int(row['origLength'])
		matchLengthArr[int(row['row']),int(row['col'])]=int(row['matchedLength'])
		origCLengthArr[int(row['row']),int(row['col'])]=int(row['origCols'])
	
	#Make plots of bulk properties
	h=makePlots(origLengthArr,"Original Number of Hits",fname,invert=True)
	h=makePlots(matchLengthArr,"Matched Number of Hits",fname,invert=True)
	h=makePlots(origLengthArr-matchLengthArr,"Unmatched Number of Hits",fname,invert=True)
	hist_match = makePlots(matchLengthArr/origLengthArr*100.,"Matched % of Hits",fname,invert=True)
	hist_origC = makePlots(origCLengthArr/origLengthArr*100.,"% of Orig Hits from Columns",fname,invert=True)
	hist_origR = makePlots((origLengthArr-origCLengthArr)/origLengthArr*100.,"% of Orig Hits from Rows",fname,invert=True)
	
	#Combined plots of bulk properties
	binCenters=np.arange(0.5,100,1)
	plt.bar(binCenters,hist_origC[0],label="Original Col hits")
	plt.bar(binCenters,hist_origR[0],label="Original Row hits",alpha=0.6)
	plt.legend(loc='best')
	plt.xlabel("% of raw hits")
	plt.ylabel('counts (normalized)')
	if args.savePlot:
		titleSave="%ofOrigHitsColRow"
		saveName = f"{fname}_hist_{titleSave}"
		print(f"Saving {saveDir}{saveName}.png")
		plt.savefig(f"{saveDir}{saveName}.png")
		plt.clf()
	else:
		plt.show()
	
	
	
#################################################################
# call main
#################################################################
if __name__ == "__main__":

	saveDir = os.getcwd()+"/plotsOut/dacOptimization/arrayScan/injection/" #hardcode location of dir for saving output plots
	dirPath = os.getcwd()[:-15] #go one directory above the current one where only scripts are held

	parser = argparse.ArgumentParser(description='Plot array data comparing default and optimized comparator DACs')
	parser.add_argument('-i', '--inputDir', default='', required=True,
        help='Directory containing data files')
	parser.add_argument('-d', '--plotDef', action='store_true', default=False, required=False, 
        help='Consider default DACs ONLY. If no -o or -d, plot both. Default: False')
	parser.add_argument('-o', '--plotOpt', action='store_true', default=False, required=False, 
		help='Consider optimized DACs ONLY. If no -o or -d, plot both. Default: False')
	parser.add_argument('-s', '--savePlot', action='store_true', default=False, required=False, 
		help='Save all plots (no display) to plotsOut/dacOptimization/arrayScan. Default: None (only displays, does not save)')

	parser.add_argument
	args = parser.parse_args()
 	
	main(args)