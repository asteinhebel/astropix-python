import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import argparse

import digitalDataHelpers as ddh
import calcHelpers as clch

#################################################################
# helper functions
#################################################################   
def makeMask(arr, cutName, cut):

	if 'r2' in cutName:
		#bad pixels have value less than cut
		mask = np.reshape((arr<cut),(35,35))
	else:
		#bad pixels have values leq 0 or greater than cut
		mask1 = np.reshape((arr>cut),(35,35))
		mask2 = np.reshape((0>=arr), (35,35))
		mask = mask1+mask2
		
	return mask

def boolVis2(arrIn, label1, arrIn2, label2, barTitle:str=None):
	"""Visualize array by plotting boolean 35x35 matrix and filling 'True' pixels, overlay two arrays to visualize where arrays overlap
	Return: none"""
	#expecting 35x35 array for arrIn

	if 'idealThreshold' not in label1:
		arrIn = np.flip(arrIn,0)
	if 'idealThreshold' not in label2:
		arrIn2 = np.flip(arrIn2,0)

	fig = plt.figure()
	ax = fig.add_subplot(111)
	ax.imshow(arrIn, cmap='Reds', alpha=0.5, label=label1)
	ax.imshow(arrIn2, cmap='Greys', alpha=0.5, label=label2)
	
	ylabels=[34-2*i for i in range(18)]
	ax.set_xticks([2*i for i in range(18)])
	ax.set_yticks([2*i for i in range(18)])
	ax.set_yticklabels(ylabels)
	ax.tick_params(axis="x", bottom=True, top=True, labelbottom=True, labeltop=True)
	plt.title(f'Pink = {label1} ({np.sum(arrIn)} bad pixels) \n Grey = {label2} ({np.sum(arrIn2)} bad pixels) \n {np.sum(arrIn*arrIn2)} shared pixels')
	plt.tight_layout() #reduce margin space	
	
	if args.savePlot:
		plt.savefig(f"{saveDir}correlate_map_{label1}__{label2}.png")
		plt.close()
		plt.clf()
	else:
		plt.show()
		
#################################################################
# main
#################################################################

def main(args):

	df0 = pd.read_csv(args.inputCSVs[0])
	df0 = df0.replace(np.nan, 0.).to_numpy()[:,1:] #replace NaNs with zero and convert to numpy, do not include first column of indices
	df0_flat = df0.flatten()
	df0_name = args.inputCSVs[0].split('/')[-1][:-4]
		
	df1 = pd.read_csv(args.inputCSVs[1])
	df1 = df1.replace(np.nan, 0.).to_numpy()[:,1:] #replace NaNs with zero, convert to numpy, do not include first column of indices
	df1_flat = df1.flatten() #do not include first column of indices
	df1_name = args.inputCSVs[1].split('/')[-1][:-4]
	
	#calculate correlation - error from  https://psyarxiv.com/uts98/	
	r, r_err = clch.calcCorrCoeff(df0_flat,df1_flat)
	
	#save or display plots
	plt.scatter(df0_flat,df1_flat, s=2)
	plt.plot([], [], ' ', label=f"r={r:.2f} +\- {r_err:.2f}")
	plt.legend(loc='best')
	plt.xlabel(df0_name)
	plt.ylabel(df1_name)
	if args.savePlot:
		plt.savefig(f"{saveDir}correlate_{df0_name}__{df1_name}.png")
		plt.close()
		plt.clf()
	else:
		plt.show()
		
	#save or display maps of 'bad' pixels
	if args.mapCorr:
		thresh={'r2':0.6, 'totSig':2, 'totMean':7, 'idealThresholds':150}
		
		key0 = [ky for ky in thresh.keys() if(ky in df0_name)][0]
		mask0 = makeMask(df0, key0, thresh[key0])
		
		key1 = [ky for ky in thresh.keys() if(ky in df1_name)][0]
		mask1 = makeMask(df1, key1, thresh[key1])
	
		mapFigMean=boolVis2(mask0, key0, mask1, key1)


#################################################################
# call main
#################################################################
if __name__ == "__main__":

	saveDir = os.getcwd()+"/plotsOut/pixelScan_Am241/chipHR3/" #hardcode location of dir for saving output plots
	dirPath = os.getcwd()[:-15] #go one directory above the current one where only scripts are held

	parser = argparse.ArgumentParser(description='Correlate data stored in CSV files from full array maps')
	parser.add_argument('-i', '--inputCSVs', action='store', default=[f'{saveDir}r2_map_chip604.csv',f'{dirPath}analysisScripts/plotsOut/thresholdScan/chip604/idealThresholds.csv'], type=str, nargs=2, 
    	help =  'Input CSV data files to correlate - each file should contain 35x35 array with value stored for each pixel. Default: [chip604_r2, chip604_idealThresholds]')
	parser.add_argument('-s', '--savePlot', action='store_true', default=False, required=False, 
		help='Save all plots (no display) to saveDir. Default: None (only displays, does not save)')	
	parser.add_argument('-m', '--mapCorr', action='store_true', default=False, required=False, 
		help='Save/display map of "bad pixels" per hardcoded metrics based on each variable. Default: False (does not plot)')	
		
	parser.add_argument
	args = parser.parse_args()
	
 	
	main(args)