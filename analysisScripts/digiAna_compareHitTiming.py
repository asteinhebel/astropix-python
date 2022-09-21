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
	#Real times recorded in s
	t_start = min(ana['Time'].iloc[0],digi['Time'].iloc[0], digi['RealTime_col'].iloc[0])
	ana['Time_scale']=[t-t_start for t in ana['Time']]
	digi['Time_scale']=[t-t_start for t in digi['Time']]
	return ana, digi

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]
    
def find_coincidence(searchArray, val, window=0.05):
	#find closest element in searchArray to val, returns value of closest element
	potential_match=find_nearest(searchArray, val)
	
	#Check whether potential match values are within the window of coincidence
	#if the index of the potential match from the search array is within the defined window of the test value, return array index of the match. If match is not in the window, return None
	deltaT = abs(val-potential_match) if abs(val-potential_match)<window else np.NaN
	matched_i = searchArray.index[searchArray.tolist().index(potential_match)] if abs(val-potential_match)<window else np.NaN
	
	return matched_i, deltaT
	
def find_pairs(bigArr, smallArr, smallStr, w, optname=""):
	#With each element of random array, see if there is an element of the longer array within the window (w)	
	pairs = np.array([find_coincidence(bigArr, j, window=w) for j in smallArr])
	matched_i = pairs[:,0] #element of bigArr that found a match in smallArr
	deltaT = pairs[:,1]
	unmatched = np.count_nonzero(np.isnan(matched_i)) #number of unmatched events\
	logging.debug(f"{unmatched} / {len(smallArr)} {smallStr} hits ({unmatched/len(smallArr)*100:.3f}%) are unmatched in {optname} DIST with window = {w:.3f}")

	return pairs, unmatched
	
def make_hist(x, arrays, labels, titles):
	plt.clf()
	plt.hist(arrays[0],x,label=labels[0])
	plt.hist(arrays[1],x,alpha=0.6,label=labels[1])
	plt.legend(loc='best')
	plt.title(titles[0])
	plt.xlabel(titles[1])
	plt.ylabel(titles[2])
	plt.show()
	
def optimize_window(moreHits, lessHits, moreStr, lessStr, showPlot):
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

#################################################################
# main
#################################################################

def main(args):

	#make into DFs
	digiDF = ddh.getDF_singlePix(digiIn) #removes bad events and returns DF
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
	

	"""
	###################################
	#Plots
	###################################

	#Plot ToT/analog ToT proxy - histogram
	xtot=np.arange(100)
	make_hist(xtot, [anaDF['ToT'],digiDF['ToT']], ['analog','digitalRow'], ['All Hits', 'ToT [us]', 'Counts'])

	#Plot real hit time wrt earliest recorded hit - scatter
	plt.clf()
	plt.scatter(anaDF['Time_scale'],anaDF['ToT'])
	plt.scatter(digiDF['Time_scale'],digiDF['ToT'])
	#plt.show()

	#Plot real hit time wrt earliest recorded hit - histogram
	xtime=np.arange(0, max(anaDF['Time_scale'].iloc[-1],digiDF['Time_scale'].iloc[-1]), 100)#100s increment
	make_hist(xtime, [anaDF['Time_scale'],digiDF['Time_scale']], ['analog','digital'], ['Unmatched Hits', 'Time of trigger (from first recording) [s]', 'Counts'])


	#plot ToT, real time of unmatched hits
	make_hist(xtot, [moreDF['ToT'][nomatch_m],lessDF['ToT'][nomatch_l]], [moreStr,lessStr], ['Unmatched Hits (digital row)', 'ToT [us]', 'Counts'])
	make_hist(xtime, [moreDF['Time_scale'][nomatch_m],lessDF['Time_scale'][nomatch_l]], [moreStr,lessStr], ['Unmatched Hits', 'Time of trigger (from first recording) [s]', 'Counts'])
	"""
	
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
	parser.add_argument
	args = parser.parse_args()
	
	
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
	"""
	
	#60min Ba133, 100ms latency, optimized DACs, pixel 00, -130V bias, vprec60
	digiIn = "../source/chip602_130V_ba133/optimizedDACs_60min_pixr0c0_20220831-150146.csv"
	anaIn = "../../astropixOut_tmp/v2/083122_amp1/chip602_130V_barium133_60min.h5py"
	nm = "optimizedDACs_ba133"

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
	
	
	## remove possibility for duplicate matches in moreHits - only match each event in moreHits with a single events in lessHits max