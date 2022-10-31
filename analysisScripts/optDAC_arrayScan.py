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
	
def makePlots(dataIn,title,save:bool=False, invert:bool=False):

	ddh.arrayVis(dataIn, barTitle = title, invert=True)
	
	#<make histogram of dataIn>#

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
#	makePlots(origLengthArr,"Original Number of Hits",invert=True)
#	makePlots(matchLengthArr,"Matched Number of Hits",invert=True)
#	makePlots(origLengthArr-matchLengthArr,"Unmatched Number of Hits",invert=True)
#	makePlots((origLengthArr-matchLengthArr)/origLengthArr*100.,"Matched % of Hits",invert=True)
	makePlots(origCLengthArr/origLengthArr*100.,"% of Orig Hits from Columns",invert=True)
	makePlots((origLengthArr-origCLengthArr)/origLengthArr*100.,"% of Orig Hits from Columns",invert=True)
	

#################################################################
# call main
#################################################################
if __name__ == "__main__":

	saveDir = os.getcwd()+"/plotsOut/dacOptimization/" #hardcode location of dir for saving output plots
	dirPath = os.getcwd()[:-15] #go one directory above the current one where only scripts are held

	parser = argparse.ArgumentParser(description='Plot array data comparing default and optimized comparator DACs')
	parser.add_argument('-i', '--inputDir', default='', required=True,
        help='Directory containing data files')
	parser.add_argument('-d', '--plotDef', action='store_true', default=False, required=False, 
        help='Consider default DACs ONLY. If no -o or -d, plot both. Default: False')
	parser.add_argument('-o', '--plotOpt', action='store_true', default=False, required=False, 
		help='Consider optimized DACs ONLY. If no -o or -d, plot both. Default: False')
	parser.add_argument('-s', '--savePlotName', action='store', default=None, required=False, 
		help='Save all plots (no display) with input name to plotsOut/dacOptimization. Default: None (only displays, does not save)')

	parser.add_argument
	args = parser.parse_args()
 	
	main(args)