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
	t_start = min(ana['Time'].iloc[0],digi['RealTime_row'].iloc[0], digi['RealTime_col'].iloc[0])
	ana['Time_scale']=[t-t_start for t in ana['Time']]
	digi['Time_scale']=[t-t_start for t in digi['RealTime_row']]
	return ana, digi

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]
    
def find_coincidence(searchArray, val, window=0.05):
	#find closest element in searchArray to val
	potential_match=find_nearest(searchArray, val)
	
	#Check whether potential match values are within the window of coincidence
	#if the index of the potential match from the search array is within the defined window of the test value, return array index of the match. If match is not in the window, return None
	matched_i = searchArray.index[searchArray.tolist().index(potential_match)] if abs(val-potential_match)<window else None
	
	return matched_i
	
def make_hist(x, arrays, labels, titles):
	plt.clf()
	plt.hist(arrays[0],x,label=labels[0])
	plt.hist(arrays[1],x,alpha=0.6,label=labels[1])
	plt.legend(loc='best')
	plt.title(titles[0])
	plt.xlabel(titles[1])
	plt.ylabel(titles[2])
	plt.show()


#################################################################
# main
#################################################################

def main():

	#make into DFs
	digiDF = ddh.getDF_singlePix(digiIn) #removes bad events and returns DF
	#Row and column 'RealTime' values agree by definition
	digiDF.rename(columns={"ToT(us)_row": "ToT"},inplace=True)

	anaDF = adh.getDF(anaIn)
	anaDF.rename(columns={"AnalogToT": "ToT"},inplace=True)

	logging.info(f"{len(anaDF)} analog hits, {len(digiDF)} digital paired hits")

	#Add column for scaled timing relative to whatever was the first measurement
	anaDF, digiDF = add_scaled_time(anaDF, digiDF)

	#Calculate rates
	anaRate = len(anaDF) / (anaDF['Time_scale'].iloc[-1])
	digiRate = len(digiDF) / (digiDF['Time_scale'].iloc[-1])
	logging.info(f"Analog hit rate = {anaRate:.3f}; digital hit rate = {digiRate:.3f}")

	#################
	##TESTING
	#anaDF = anaDF[:5]
	#digiDF = digiDF[:6]
	#################

	#identify whether anlaog or digital has less hits 
	if len(anaDF)<=len(digiDF):
		lessHits = anaDF['Time_scale']
		less_str = "analog"
		lessDF = anaDF
		moreHits = digiDF['Time_scale']
		more_str = "digital"
		moreDF = digiDF
	else:
		lessHits = digiDF['Time_scale']
		less_str = "digital"
		lessDF = digiDF
		moreHits = anaDF['Time_scale']
		more_str = "analog"
		moreDF = anaDF
	logging.info(f"{more_str} array is longer than {less_str} array")
	
	randHits = pd.Series(np.random.uniform(0,max(lessHits),len(lessHits)))
	plt.hist(randHits,np.arange(0,max(lessHits),0.5))
	plt.xlabel('Random ToT values [us]')
	#plt.show()
	plt.clf()
	
	logging.debug(f"analog: length={len(anaDF['Time_scale'])}\n{anaDF['Time_scale']}")
	logging.debug(f"digital: length={len(digiDF['Time_scale'])}\n{digiDF['Time_scale']}")
	logging.debug(f"random: length={len(randHits)}\n{randHits}")

	#Optimize window by comparing to random distribution
	wind=[0.025*i for i in range(25)]
	randProp=[]
	for w in wind:
		#With each element of random array, see if there is an element of the longer array within the window (w)	
		matched_i_rand =  [find_coincidence(randHits, j, window=w) for j in lessHits]
		unmatched_rand = matched_i_rand.count(None)
		logging.debug(f"{unmatched_rand} / {len(lessHits)} {less_str} hits ({unmatched_rand/len(lessHits)*100:.3f}%) are unmatched in RANDOM DIST with window={w:.2f}")
		logging.debug(f"Matched entries / (window * hit rate) = {len(lessHits)-unmatched_rand} / ( {w:.2f} * {anaRate:.3f} ) = {(len(lessHits)-unmatched_rand) / ( w * anaRate ) :.3f}")
		#randProp.append((len(lessHits)-unmatched_rand) / ( w * anaRate ) )
		randProp.append((len(lessHits)-unmatched_rand)) #stores number of matched hits at each window

	measProp=[]
	for w in wind:
		#With each element of smaller array, see if there is an element of the longer array within the window (w)	
		matched_i = [find_coincidence(moreHits, j, window=w) for j in lessHits] #array of same length as lessHits - index of matched_i matches with index of lessHits that is paired with the held index of moreHits

		#### NEED TO HANDLE DUPLICATIONS - MULTIPLE ELEMENTS MATCHED TO SAME

		#With the digital 0.713s readout gap, potential coincidence could be claimed up to 0.7s...
		nomatch_m = list(set(np.arange(len(moreHits))) - set(matched_i)) #elements in moreHits without a match
		nomatch_l = [i for i, val in enumerate(matched_i) if val == None]#elements in lessHits without a match
		logging.debug(f"{matched_i.count(None)} / {len(lessHits)} {less_str} hits ({matched_i.count(None)/len(lessHits)*100:.3f}%) are unmatched in {more_str}")
		logging.debug(f"{len(nomatch_m)} / {len(moreHits)} {more_str} hits ({len(nomatch_m)/len(moreHits)*100:.3f}%) are unmatched in {less_str}")
		#measProp.append((len(lessHits)-matched_i.count(None)) / ( w * anaRate ) )
		measProp.append((len(lessHits)-matched_i.count(None)) ) #stores number of matched hits at each window

	measPerc=[i/len(lessHits)*100. for i in measProp]
	randPerc=[i/len(randHits)*100. for i in randProp]
	plt.scatter(wind,measPerc,label="meas", s=75)
	plt.scatter(wind,randPerc,label="rand", alpha=0.7)
	plt.legend(loc="best")
	plt.ylabel(f"% of {less_str}/random hits with a {more_str} match")
	plt.xlabel("window [s]")
	plt.savefig(f"{saveDir}{nm}_timingWindowOpt.png")
	logging.info(f"Saving {saveDir}{nm}_timingWindowOpt.png")
	plt.show()
	
	logging.info(f"Leftover {more_str} events = {len(moreHits)-max(measProp)} ({(len(moreHits)-max(measProp))/len(moreHits)*100:.2f})%")

	#Optimized window value = 0.15s - still get 100% of short array matched but only ~60% of random array so outperforming just a random matching

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
	make_hist(xtot, [moreDF['ToT'][nomatch_m],lessDF['ToT'][nomatch_l]], [more_str,less_str], ['Unmatched Hits (digital row)', 'ToT [us]', 'Counts'])
	make_hist(xtime, [moreDF['Time_scale'][nomatch_m],lessDF['Time_scale'][nomatch_l]], [more_str,less_str], ['Unmatched Hits', 'Time of trigger (from first recording) [s]', 'Counts'])
	"""
	
#################################################################
# call main
#################################################################
if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(description='Plot Digital Data')
	parser.add_argument('-d', '--debug', action='store_true', default=False, required=False, help='Display debug printouts. Default: False')
	parser.add_argument
	args = parser.parse_args()

	#Hardcode one run - 180min Co with pixel 00, 700ms latency
	#digiIn = "../source/chip602_cobalt57_180min_pix00_120mV_analogPaired_beamDigital_20220707-140016.csv"
	#anaIn = "../../astropixOut_tmp/v2/070722_amp1/chip602_100mV_digitalPaired_cobalt57_180min.h5py"
	
	#2min 0.3V injection, 100ms latency, optimized DACs for short pulse, pixel 00, -60V bias
	#digiIn = "../logInj/dacScan/pixelr0c0/optimized/vprec_60_vnfoll2_4_vnfb_3_20220823-114012.csv"
	#anaIn = "../logInj/dacScan/pixelr0c0/optimized/short_chip602_vprec60_vnfoll24_vnfb3_0.3Vinj_2min.h5py"
	#nm = "optimizedDACs_0.3Vinj"
	
	#2min 0.3V injection, 100ms latency, default DACs, pixel 00, -60V bias, vprec60
	digiIn = "../logInj/dacScan/pixelr0c0/vprec_test/vprec_60_vnfoll2_1_vnfb_1_20220823-113731.csv"
	anaIn = "../logInj/dacScan/pixelr0c0/vprec_test/short_chip602_vprec60_vnfoll21_vnfb1_0.3Vinj_2min.h5py"
	nm = "defaultDACs_0.3Vinj"

	saveDir = "plotsOut/hitTiming/"
	
	#Setup logger
	loglev = logging.DEBUG if args.debug else logging.INFO
	logstr = "_debug" if args.debug else ""
	logging.getLogger('matplotlib.font_manager').disabled = True
	logging.captureWarnings(True)
	#handlers allows for terminal printout and file writing at the same time
	logging.basicConfig(format='%(levelname)s:%(message)s',level=loglev,
		handlers=[logging.FileHandler(f"{saveDir}{nm}{logstr}.log"),logging.StreamHandler()])

	main()
	
	

	## window opt choice - move all code away there
	## remove possibility for duplicate matches in moreHits - only match each event in moreHits with a single events in lessHits max