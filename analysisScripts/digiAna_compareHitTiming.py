import pandas as pd
import numpy as np
import h5py
import matplotlib.pyplot as plt
import os,sys
import logging
import argparse

import digitalDataHelpers as ddh
import analogDataHelpers as adh
from scipy.optimize import curve_fit

#################################################################
# helper functions
#################################################################
def add_scaled_time(ana,digi):
	"""Add series to analog and digital dataframes scaling the timing variable from 
			time since first epoch to time since first trigger
	Return: analog and digital dictionaries storing data, with scaled time array added in"""
	#Real times recorded in s
	t_start = min(ana['Time'].iloc[0],digi['Time'].iloc[0], digi['RealTime_col'].iloc[0])
	ana['Time_scale']=[t-t_start for t in ana['Time']]
	digi['Time_scale']=[t-t_start for t in digi['Time']]
	return ana, digi

def find_nearest(array, value):
	"""Find closest element in array to an input value
	Return: value of array element that is closest to the input value"""
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]
    
def find_coincidence(searchArray, val, window=0.05):
	"""For a given value, find whether there is an entry in an input array that is within the given distance
	Return: index of value from array that is closest to the given value, 
			difference between given value and array element that is closest to it (to which it is matched)"""
	#find closest element in searchArray to val, returns value of closest element
	potential_match=find_nearest(searchArray, val)
	
	#Check whether potential match values are within the window of coincidence
	#if the index of the potential match from the search array is within the defined window of the test value, return array index of the match. If match is not in the window, return None
	deltaT = abs(val-potential_match) if abs(val-potential_match)<window else np.NaN
	matched_i = searchArray.index[searchArray.tolist().index(potential_match)] if abs(val-potential_match)<window else np.NaN
	
	return matched_i, deltaT
	
def find_pairs(bigArr, smallArr, smallStr, w, optname=""):
	""" Given two arrays of any size, find whether elements from smaller array are contained within larger array
	Return: 2d array containing indices of larger array that match an element of the smaller array and the difference of the matched pairs
			Number of values from larger array that do not have a match in the smaller array"""
	#With each element of random array, see if there is an element of the longer array within the window (w)	
	pairs = np.array([find_coincidence(bigArr, j, window=w) for j in smallArr])
	matched_i = pairs[:,0] #element of bigArr that found a match in smallArr
	deltaT = pairs[:,1]
	unmatched = np.count_nonzero(np.isnan(matched_i)) #number of unmatched events
	logging.debug(f"{unmatched} / {len(smallArr)} {smallStr} hits ({unmatched/len(smallArr)*100:.3f}%) are unmatched in {optname} DIST with window = {w:.3f}")

	return pairs, unmatched
	
def optimize_window(moreHits, lessHits, moreStr, lessStr, showPlot):
	"""Optimize the size of the timing window to use when identifying coincident digital and analog triggers
			Compare time difference between matched elements of smaller dataset (between analog and digital) to a random data set
			Compare time difference between matched elements of smaller dataset to larger dataset
			Identify whether random data set or larger data set is a closer match to smaller dataset
			Find optimal window from where the better fitting curve of deltaT vs window size flattens out 
	Return: optimal value to use as comparison window"""
	logging.info("Optimizing the time window for matching")
	
	#Initialize random distribution for comparison - same length as longer array
	randHits = pd.Series(np.random.uniform(0,max(moreHits),len(moreHits)))
	plt.hist(randHits,np.arange(0,max(moreHits),0.5))
	plt.xlabel('Random time values [s]')
	if showPlot: plt.show()
	plt.clf()
	logging.debug(f"random: length={len(randHits)}\n{randHits}")
	
	#Calculate rates
	lessRate = len(lessHits) / lessHits.iloc[-1]
	moreRate = len(moreHits) / moreHits.iloc[-1]

	#Optimize window by comparing to random distribution
	wind=[0.005*i for i in range(1,25)]

	randProp = []
	measProp = []
	for w in wind:
		pairs_rand, unmatched_rand = find_pairs(randHits, lessHits, lessStr, w, optname="RANDOM")
		randProp.append((len(lessHits)-unmatched_rand)) #stores number of matched hits at each window
		deltaT_rand = pairs_rand[:,1]
	for w in wind:
		pairs, unmatched = find_pairs(moreHits, lessHits, lessStr, w, optname=lessStr)
		measProp.append((len(lessHits)-unmatched) ) #stores number of matched hits at each window
		nomatch_m = list(set(np.arange(len(moreHits))) - set(pairs[:,0])) #elements in moreHits without a match
		nomatch_l = [i for i, val in enumerate(pairs[:,0]) if val == None]#elements in lessHits without a match
		logging.debug(f"{len(nomatch_m)} / {len(moreHits)} {moreStr} hits ({len(nomatch_m)/len(moreHits)*100:.3f}%) are unmatched in {lessStr}")
		deltaT = pairs[:,1]
		
	#Plot deltaT values between lessHits array and closest match in moreHits or randHits array
	xbins = np.arange(0, 0.12, 0.12/25) #25 bins
	hist_rand = plt.hist(deltaT_rand, xbins, alpha=0.4, density=True, label=f'{lessStr} in random')
	hist = plt.hist(deltaT, xbins, facecolor='r', alpha=0.4, density=True, label=f'{lessStr} in {moreStr}')
	plt.xlabel(f'Time between {lessStr} hit and paired {moreStr}/random hit [s]')
	plt.ylabel('Normalized Counts')
	plt.legend(loc='best')
	plt.savefig(f"{saveDir}{nm}_matchingDeltaT.png")
	logging.info(f"Saving {saveDir}{nm}_matchingDeltaT.png")
	if showPlot: plt.show()

	plt.clf()
	measPerc=[i/len(lessHits)*100. for i in measProp]
	randPerc=[i/len(lessHits)*100. for i in randProp]
	plt.scatter(wind,measPerc,label="meas", s=75)
	plt.scatter(wind,randPerc,label="rand", alpha=0.7)
	plt.legend(loc="best")
	plt.ylabel(f"% of {lessStr} hits with a {moreStr}/random match")
	plt.xlabel("window [s]")
	plt.savefig(f"{saveDir}{nm}_timingWindowOpt.png")
	logging.info(f"Saving {saveDir}{nm}_timingWindowOpt.png")
	if showPlot: plt.show()
	
	logging.info(f"Leftover {moreStr} events = {len(moreHits)-max(measProp)} ({(len(moreHits)-max(measProp))/len(moreHits)*100:.2f})%")

	#Find optimal window value - matching of measured data is maximal (where curve flattens out)
	grad = np.gradient(measPerc) #shows gradient between each point - use to find which points aren't increasing much anymore
	optIndex = np.argmax(grad<0.5) +1 # Go one index higher just to be safe
	optVal = wind[optIndex]
	logging.debug(f"Optimal window value: {optVal:.3f} s")

	return optVal
	

def make_2hist(x, arrays, labels, titles, sve:str='histogram.png'):
	"""Plot two histograms on same axes"""
	plt.clf()
	hist = plt.hist(arrays[0],x,label=labels[0])
	plt.hist(arrays[1],x,alpha=0.6,label=labels[1])
	plt.legend(loc='best')
	plt.title(titles[0])
	plt.xlabel(titles[1])
	plt.ylabel(titles[2])
	plt.savefig(sve)
	logging.info(f"Saving {sve}")
	if args.showPlots: plt.show()

#################################################################
# main
#################################################################

def main(args):

	###########################
	# STEP ONE - FIND TIME-CORRELATED HITS IN ANALOG AND DIGITAL
	# If this step is already done, then the output csv of matched hits must be input as an argument with -i and code skips to step two
	# Consider hardcoded (in init) analog and digital hit files and pair hits based on timing coincidence
	## If best window for coincidence is not known, run with -w to optimize. Default = 0.07
	# Outputs plots (if run with -p) and csv of matched digital and analog hits with hit time, deltaT, and ToT
	
	#If no input csv of matched hits, then create one
	if args.inputF is None:
		#make into DFs
		digiDF = ddh.getDF_singlePix(digiIn, args.pixel) #removes bad events and returns DF
		#Row and column 'RealTime' values agree by definition
		digiDF.rename(columns={"ToT(us)_row": "ToT"},inplace=True)
		digiDF.rename(columns={"RealTime_row": "Time"},inplace=True)

		anaDF = adh.getDF(anaIn)
		anaDF.rename(columns={"AnalogToT": "ToT"},inplace=True)

		logging.info(f"{len(anaDF)} analog hits, {len(digiDF)} digital paired hits")

		#Add column for scaled timing relative to whatever was the first measurement
		anaDF, digiDF = add_scaled_time(anaDF, digiDF)

		#Calculate rates
		anaRate = len(anaDF) / (anaDF['Time_scale'].iloc[-1])
		digiRate = len(digiDF) / (digiDF['Time_scale'].iloc[-1])
		logging.info(f"Analog hit rate = {anaRate:.3f}; digital hit rate = {digiRate:.3f}")

		#identify whether anlaog or digital has less hits 
		if len(anaDF)<=len(digiDF):
			lessHits = anaDF['Time_scale']
			lessStr = "analog"
			lessDF = anaDF
			moreHits = digiDF['Time_scale']
			moreStr = "digital"
			moreDF = digiDF
		else:
			lessHits = digiDF['Time_scale']
			lessStr = "digital"
			lessDF = digiDF
			moreHits = anaDF['Time_scale']
			moreStr = "analog"
			moreDF = anaDF
		logging.info(f"{moreStr} array is longer than {lessStr} array")
	
		logging.debug(f"analog: length={len(anaDF['Time_scale'])}\n{anaDF['Time_scale']}")
		logging.debug(f"digital: length={len(digiDF['Time_scale'])}\n{digiDF['Time_scale']}")
	
		#Find or define optimal window size
		if args.optimizeWindow:
			w = optimize_window(moreHits, lessHits, moreStr, lessStr, args.showPlots)
		else:
			w = 0.07 #default optimal window
		logging.info(f"Optimized window size is {w}")
	
		#Isolate paired events for storage in a csv
		pairs, unmatched = find_pairs(moreHits, lessHits, lessStr, w, optname=lessStr)
		matched_i = pairs[:,0] #stores index of moreHits that found a match in lessHits, matching lessHits element indicated by location in array (len(matched_i)==len(lessHits)
		deltaT = pairs[:,1]
		
		#Remove duplicate matches - keep only pair with the smallest deltaT and eliminate other pairs that share matches
		uniques, counts = np.unique(matched_i, return_counts=True) #uniques stores unique index values found in  matched_i, counts returns how many times the corresponding entry of uniques occurs in matched_i
		dupes = uniques[counts>1] #array of duplicated index values
		logging.info(f"{len(dupes)} elements of {moreStr} array have multiple matches - retain only pair with smallest deltaT")
		for d in dupes:
			dupe_i = np.where(matched_i==d) #position in array of duplicated matching index
			keep_i = np.where(deltaT==min(deltaT[dupe_i]))[0] #get position in array of element to keep (smallest deltaT)
			dupe_i = np.delete(dupe_i, np.where(dupe_i==keep_i))
			#change elements of matched_i/deltaT that have duplicated array and are not the pair chosen to keep to NaN
			np.put(matched_i, dupe_i, np.NaN)
			np.put(deltaT, dupe_i, np.NaN)
	
		#Create dataframe and populate with arrays without NaNs
		df=pd.DataFrame(deltaT[~np.isnan(deltaT)], dtype=float, columns=['deltaT'])
		less_i = np.argwhere(~np.isnan(matched_i)).flatten().astype(int)
		more_i = matched_i[~np.isnan(matched_i)].astype(int)
		df[f'{lessStr}_i'] = less_i
		df[f'{moreStr}_i'] = more_i
	
		lessTime=np.array(lessDF['Time'])
		moreTime=np.array(moreDF['Time'])
		lessTot=np.array(lessDF['ToT']).round(2)
		moreTot=np.array(moreDF['ToT']).round(2)
		df[f'{lessStr}_time'] = lessTime[less_i]
		df[f'{moreStr}_time'] = moreTime[more_i]
		df[f'{lessStr}_ToT'] = lessTot[less_i]
		df[f'{moreStr}_ToT'] = moreTot[more_i]
	
		#Save dataframe
		df.to_csv(f'{saveDir}{nm}_matched.csv')  
	
	#Provided input csv of matched files so use that to create plots	
	else:
		logging.info(f"Opening file {args.inputF}")
		df = pd.read_csv(args.inputF)


	###########################
	# STEP TWO - MAKE PLOTS COMPARING COINCIDENT HIT MEASUREMENTS

	ana_time = np.array(df['analog_time'])	
	digi_time = np.array(df['digital_time'])
	ana_ToT = np.array(df['analog_ToT'])	
	digi_ToT = np.array(df['digital_ToT'])
	absdeltaT = np.array(df['deltaT'])
	deltaT = np.add(digi_time, -1*ana_time)
	logging.debug("Input dataframe received and data read off")
	
	#Plot ToT/analog ToT proxy - histogram
	xtot=np.arange(42)
	xtot2=np.arange(0,42,0.5)
	outname = f"{saveDir}{nm}_hist_pairs_ToT.png"
	make_2hist(xtot, [ana_ToT,digi_ToT], ['analog','digitalRow'], ['All Hits', 'ToT [us]', 'Counts'], sve=outname)
	
	#Plot real hit time wrt earliest recorded hit - scatter
	plt.clf()
	plt.scatter(ana_time, ana_ToT, label='analog')
	plt.scatter(digi_time, digi_ToT, label='digital')
	plt.legend(loc='best')
	plt.xlabel("Trigger time [s from epoch]")
	plt.ylabel("ToT [us]")
	plt.savefig(f"{saveDir}{nm}_scatter_pairs_timeToT.png")
	logging.info(f"Saving {saveDir}{nm}_scatter_pairs_timeToT.png")
	if args.showPlots: plt.show()
	
	#Plot deltaT - histogram
	plt.clf()
	xtime=np.arange(min(deltaT), max(deltaT), 0.001)
	plt.hist(deltaT, xtime)
	plt.title('Time difference of matching pair')
	plt.xlabel('Time difference (digital - analog) [s]')
	plt.ylabel('Counts')
	plt.savefig(f"{saveDir}{nm}_hist_pairs_deltaT.png")
	logging.info(f"Saving {saveDir}{nm}_hist_pairs_deltaT.png")
	if args.showPlots: plt.show()

	#Plot analog vs digital ToT for pairs - scatter
	plt.clf()
	plt.scatter(ana_ToT, digi_ToT, s=2)
	plt.xlabel("Analog ToT proxy [us]")
	plt.ylabel("Digital ToT [us]")
	plt.savefig(f"{saveDir}{nm}_scatter_pairs_compToT.png")
	logging.info(f"Saving {saveDir}{nm}_scatter_pairs_compToT.png")
	if args.showPlots: plt.show()
	
	#Plot analog vs digital ToT for pairs - 2d hist
	plt.clf()
	plt.hist2d(ana_ToT, digi_ToT, bins=[xtot2, xtot2])
	plt.xlabel("Analog ToT proxy [us]")
	plt.ylabel("Digital ToT [us]")
	plt.savefig(f"{saveDir}{nm}_hist2d_pairs_compToT.png")
	logging.info(f"Saving {saveDir}{nm}_hist2d_pairs_compToT.png")
	if args.showPlots: plt.show()
	
	#Plot deltaToT - histogram
	deltaToT = np.add(digi_ToT, -1.*ana_ToT)
	xdtot=np.arange(0, max(deltaToT), 0.5)
	plt.clf()
	plt.hist(deltaToT, xdtot) 
	plt.title('ToT difference (digital-analog) of matching pair')
	plt.xlabel('Digital - analog ToT [us]')
	plt.ylabel('Counts')
	plt.savefig(f"{saveDir}{nm}_hist_pairs_deltaToT.png")
	logging.info(f"Saving {saveDir}{nm}_hist_pairs_deltaToT.png")
	if args.showPlots: plt.show()
	
	#Bin deltaToT in deltaT bins of 0.01s - stacked histogram
	deltaTBins=[]
	labelList=[]
	for i in range(-6,7):
		deltaTBins.append(deltaToT[(0.01*i<deltaT) & (deltaT<0.01*(i+1))])
		#plt.hist(deltaToT[(0.01*i<deltaT) & (deltaT<0.01*(i+1))], xdtot, label=f"{0.01*i} - {0.01*(i+1)} s deltaT", stacked=True) #subsample every 5th element of xtime
		labelList.append(f"{0.01*i} - {0.01*(i+1)} s deltaT")

	plt.hist(deltaTBins, xdtot, stacked=True)
	plt.title('ToT difference (digital-analog) binned by deltaT')
	plt.xlabel('Digital - analog ToT [us]')
	plt.ylabel('Counts')
	plt.legend(labelList,loc='best')
	plt.savefig(f"{saveDir}{nm}_hist_pairs_deltaToTBinned.png")
	logging.info(f"Saving {saveDir}{nm}_hist_pairs_deltaToTBinned.png")
	if args.showPlots: plt.show()
	
	#Plot totRatio - histogram
	totRatio = np.divide(digi_ToT, ana_ToT)
	xtotr=np.arange(0, max(totRatio), 0.1)
	plt.clf()
	plt.hist(totRatio, xtotr) 
	plt.title('ToT ratio (digital/analog) of matching pair')
	plt.xlabel('Digital/analog ToT')
	plt.ylabel('Counts')
	plt.savefig(f"{saveDir}{nm}_hist_pairs_ToTratio.png")
	logging.info(f"Saving {saveDir}{nm}_hist_pairs_ToTratio.png")
	if args.showPlots: plt.show()
	
	#Bin totRatio in deltaT bins of 0.01s - stacked histogram
	totRatioBins=[]
	for i in range(-6,7):
		totRatioBins.append(totRatio[(0.01*i<deltaT) & (deltaT<0.01*(i+1))])

	plt.hist(totRatioBins, xtotr, stacked=True)
	plt.title('ToT ratio (digital/analog) binned by deltaT')
	plt.xlabel('Digital/analog ToT')
	plt.ylabel('Counts')
	plt.legend(labelList,loc='best')
	plt.savefig(f"{saveDir}{nm}_hist_pairs_ToTratioBinned.png")
	logging.info(f"Saving {saveDir}{nm}_hist_pairs_ToTratioBinned.png")
	if args.showPlots: plt.show()
	
	#Plot deltaT vs ToT ratio - 2d hist
	plt.clf()
	plt.hist2d(deltaT, totRatio, bins=[xtime, xtotr])
	plt.xlabel("Time difference (digital-analog)[s]")
	plt.ylabel("Digital/analog ToT")
	plt.savefig(f"{saveDir}{nm}_hist2d_pairs_deltaTVStotratio.png")
	logging.info(f"Saving {saveDir}{nm}_hist2d_pairs_deltaTVStotratio.png")
	if args.showPlots: plt.show()
	
	
#################################################################
# call main
#################################################################
if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(description='Plot Digital Data')
	parser.add_argument('-d', '--debug', action='store_true', default=False, required=False, 
		help='Display debug printouts. Default: False')
	parser.add_argument('-w', '--optimizeWindow', action='store_true', default=False, required=False, 
		help='Calculate and plot window optimization compared to random distribution. Default: False')
	parser.add_argument('-p', '--showPlots', action='store_true', default=False, required=False, 
		help='Display plots to terminal. Saves all plots always. Default: False')	
	parser.add_argument('-i', '--inputF', default=None, required=False,
        help='Input .csv containing paired digital/analog hits (from previously running this code). If argument provided, matching and csv creation not redone. Default: None')
	parser.add_argument('-x','--pixel', action='store', type=int, nargs=2, default = None,
		help='Active pixel in digital data. Enter as two ints: row col. Default: 0 0')
		
	parser.add_argument
	args = parser.parse_args()
	
	#Set default pixel
	if args.pixel is None:
		args.pixel=[0,0]
	else:
		args.pixel=[args.pixel[0],args.pixel[1]]
	
	
	"""
	#2min 0.3V injection, 100ms latency, optimized DACs for short pulse, pixel 00, -60V bias
	digiIn = "../logInj/dacScan/pixelr0c0/optimized/vprec_60_vnfoll2_4_vnfb_3_20220823-114012.csv"
	anaIn = "../logInj/dacScan/pixelr0c0/optimized/short_chip602_vprec60_vnfoll24_vnfb3_0.3Vinj_2min.h5py"
	nm = "optimizedDACs_0.3Vinj"
	"""
	"""
	#2min 0.3V injection, 100ms latency, default DACs, pixel 00, -60V bias, vprec60
	#digital latency ~ 100ms
	#analog latency ~ 200-500ms (2021 11 30)
	digiIn = "../logInj/dacScan/pixelr0c0/vprec_test/vprec_60_vnfoll2_1_vnfb_1_20220823-113731.csv"
	anaIn = "../logInj/dacScan/pixelr0c0/vprec_test/short_chip602_vprec60_vnfoll21_vnfb1_0.3Vinj_2min.h5py"
	nm = "defaultDACs_0.3Vinj"
	
	#60min Ba133, 100ms latency, optimized DACs, pixel 00, -130V bias, vprec60
	digiIn = "../source/chip602_130V_ba133/optimizedDACs_60min_pixr0c0_20220831-150146.csv"
	anaIn = "../../astropixOut_tmp/v2/083122_amp1/chip602_130V_barium133_60min.h5py"
	nm = "optimizedDACs_ba133"
	"""
	#30min Ba133, 100ms latency, optimized DACs, pixel 00, -130V bias, vprec60, 5ns clock in decoder
	digiIn = "../source/chip602_130V_ba133/timingTest/r0c0_30min_20221019-142430.csv"
	anaIn = "../../astropixOut_tmp/v2/101922_amp1/chip602_130V_r0c0_barium133_30min.h5py"
	nm = "updatedClock_ba133"
	
	"""
	#30min Ba133, 100ms latency, optimized DACs, pixel r0c5, -130V bias, vprec60, 5ns clock in decoder
	digiIn = "../source/chip602_130V_ba133/timingTest/r0c5_30min_20221019-145731.csv"
	anaIn = "../../astropixOut_tmp/v2/101922_amp1/chip602_130V_r0c5_barium133_30min.h5py"
	nm = "updatedClock_r0c5_ba133"
	"""
	saveDir = "plotsOut/hitTiming/"
	
	#Setup logger
	loglev = logging.DEBUG if args.debug else logging.INFO
	logstr = "_debug" if args.debug else ""
	logging.getLogger('matplotlib.font_manager').disabled = True
	logging.captureWarnings(True)
	#handlers allows for terminal printout and file writing at the same time
	logging.basicConfig(format='%(levelname)s:%(message)s',level=loglev,
		handlers=[logging.FileHandler(f"{saveDir}{nm}{logstr}.log",mode='w'),logging.StreamHandler()])


	main(args)
	