import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os,sys

import digitalDataHelpers as ddh
from scipy.optimize import curve_fit



#################################################################
# helper functions
#################################################################

def Gauss(x, A, mu, sigma):
    return A*np.exp(-(x-mu)**2/(2.0*sigma**2))

#################################################################
# main
#################################################################

if __name__ == "__main__":
	dirPath=os. getcwd()[:-15] #go one directory above the current one where only scripts are held
	
	# For NOISE: Use files of the style *_beamDigital_*.txt (*.log files are only bitstreams)
	fileIn="logInj/chip1_2min_DisHiDr0_analogPaired_1.0_injection_20220609-130749.log"
	
	"""
	readFile=ddh.reduceFile(dirPath+fileIn)
	df=ddh.getDF(readFile)
	
	plt.plot( df["ToT(us)_row"], df['ToT(us)_col'], ".", alpha=0.5  )
	plt.xlabel('row ToT duration [us]')
	plt.ylabel('column ToT duration [us]')
	x=np.arange(40)
	plt.plot(x, 'b')
	plt.show()
	plt.clf()
    
	plt.plot(df['ToT(us)_row']/df['ToT(us)_col'],"o")
	plt.xlabel('Triggered point')
	plt.ylabel('Ratio row/col ToT')
	plt.axhline(y=1, color='r')
	plt.show()
	plt.clf()
	ratio=np.array(df['ToT(us)_row']/df['ToT(us)_col'])
	outliers=np.where((ratio<0.5)|(ratio>1.5))
	print(df.loc[outliers])
    
	plt.hist(df['ToT(us)_row'].append(df['ToT(us)_col']),40,fc=(0,0,1,1), label="All")
	plt.hist(df['ToT(us)_row'],40,fc=(1,0,0,0.5),label="Row")
	plt.hist(df['ToT(us)_col'],40,fc=(0,1,0,0.5),label="Col")
	plt.xlabel('ToT (us)')
	plt.ylabel('Counts')
	plt.legend(loc="best")
	plt.show()
	"""
	
	inj=False
	timestmp=True
	#filesIn=["chip1_2min_DisHiDr0_analogPaired_0.3_injection_20220609-130531.csv","chip1_2min_DisHiDr1_analogPaired_0.3_injection_20220609-131435.csv","chip1_2min_DisHiDr0_analogPaired_1.0_injection_20220609-130749.csv","chip1_2min_DisHiDr1_analogPaired_1.0_injection_20220609-131027.csv"]
	#labels=["0.3V, 0","0.3V, 1","1.0V, 0","1.0V, 1"]
	
	filesIn=["logInj/chip1_2min_DisHiDr0_clkDiv10_analogPaired_0.3_injection_20220609-140916.log","logInj/chip1_2min_DisHiDr0_clkDiv50_analogPaired_0.3_injection_20220609-140650.log","logInj/chip1_2min_DisHiDr0_clkDiv100_analogPaired_0.3_injection_20220609-135612.log","logInj/chip1_2min_DisHiDr0_clkDiv150_analogPaired_0.3_injection_20220609-134908.log","logInj/chip1_2min_DisHiDr0_clkDiv200_analogPaired_0.3_injection_20220609-134641.log","logInj/chip1_2min_DisHiDr0_analogPaired_0.3_injection_20220609-130531.log"]
	#filesIn=["logInj/chip1_2min_DisHiDr0_clkDiv10_analogPaired_1.0_injection_20220609-141134.log","logInj/chip1_2min_DisHiDr0_clkDiv50_analogPaired_1.0_injection_20220609-140433.log","logInj/chip1_2min_DisHiDr0_clkDiv100_analogPaired_1.0_injection_20220609-135353.log","logInj/chip1_2min_DisHiDr0_clkDiv150_analogPaired_1.0_injection_20220609-135126.log","logInj/chip1_2min_DisHiDr0_clkDiv200_analogPaired_1.0_injection_20220609-134420.log","logInj/chip1_2min_DisHiDr0_analogPaired_1.0_injection_20220609-130749.log"]
	#filesIn=["logInj/chip1_2min_DisHiDr1_clkDiv10_analogPaired_0.3_injection_20220609-131933.log","logInj/chip1_2min_DisHiDr1_clkDiv50_analogPaired_0.3_injection_20220609-133016.log","logInj/chip1_2min_DisHiDr1_clkDiv100_analogPaired_0.3_injection_20220609-132628.log","logInj/chip1_2min_DisHiDr1_clkDiv150_analogPaired_0.3_injection_20220609-133715.log","logInj/chip1_2min_DisHiDr1_clkDiv200_analogPaired_0.3_injection_20220609-133935.log","logInj/chip1_2min_DisHiDr1_analogPaired_0.3_injection_20220609-131435.log"]
	#filesIn=["logInj/chip1_2min_DisHiDr1_clkDiv10_analogPaired_1.0_injection_20220609-132150.log","logInj/chip1_2min_DisHiDr1_clkDiv50_analogPaired_1.0_injection_20220609-133242.log","logInj/chip1_2min_DisHiDr1_clkDiv100_analogPaired_1.0_injection_20220609-132410.log","logInj/chip1_2min_DisHiDr1_clkDiv150_analogPaired_1.0_injection_20220609-133458.log","logInj/chip1_2min_DisHiDr1_clkDiv200_analogPaired_1.0_injection_20220609-134153.log","logInj/chip1_2min_DisHiDr1_analogPaired_1.0_injection_20220609-131027.log"]
	labels=["10","50","100","150","200","255"]
	
	#filesIn=["logInj/chip2_2min_analogPaired_0.2_injection_20220609-153604.log","logInj/chip2_2min_analogPaired_00_0.3_injection_20220609-102112.log","logInj/chip2_2min_analogPaired_0.4_injection_20220609-153348.log","logInj/chip2_2min_analogPaired_0.5_injection_20220609-153130.log","logInj/chip2_2min_analogPaired_00_0.6_injection_20220609-102327.log","logInj/chip2_2min_analogPaired_0.7_injection_20220609-152912.log","logInj/chip2_2min_analogPaired_0.8_injection_20220609-152656.log","logInj/chip2_2min_analogPaired_00_0.9_injection_20220609-102554.log","logInj/chip2_2min_analogPaired_1.0_injection_20220609-152435.log","logInj/chip2_2min_analogPaired_1.1_injection_20220609-152221.log","logInj/chip2_2min_analogPaired_00_1.2_injection_20220609-102829.log","logInj/chip2_2min_analogPaired_1.3_injection_20220609-152005.log","logInj/chip2_2min_analogPaired_1.4_injection_20220609-151746.log","logInj/chip2_2min_analogPaired_1.5_injection_20220609-151529.log"]
	#labels=["0.2","0.3","0.4","0.5","0.6","0.7","0.8","0.9","1.0","1.1","1.2","1.3","1.4","1.5"]
	#inj=True
	mean=[]
	
	
	if timestmp:
		#overlaid plots of timestamp values 
		for i,f in enumerate(filesIn):
			fi=ddh.reduceFile(dirPath+f)
			df=ddh.getDF(fi)
			plt.scatter(df['NEvent'],df['tStamp'],label=labels[i])
		plt.xlabel('Event number')
		plt.ylabel('Timestamp')
		plt.legend(loc='best')
		plt.show()
	
	else:
		#plot histogram of ToT - overlaid from all files in filesIn
		for i,f in enumerate(filesIn):
			fi=ddh.reduceFile(dirPath+f)
			df=ddh.getDF(fi)
			hist=plt.hist(df['ToT(us)_row'].append(df['ToT(us)_col']),40, alpha=0.3, label=labels[i])
			ydata=hist[0]
			binCenters=hist[1]+((hist[1][1]-hist[1][0])/2)
			binCenters=binCenters[:-1]
			popt, pcov = curve_fit(Gauss, xdata=binCenters, ydata=ydata, bounds=(0,np.inf), maxfev=5000, absolute_sigma=True)
			mean.append(popt[1])
			xspace=np.linspace(binCenters[0],binCenters[-1],len(binCenters)*10)
			print(popt)
			if inj:
				plt.plot(xspace, Gauss(xspace, *popt))  
				plt.title(f"{labels[i]} V Injection")
				plt.xlabel('ToT (us)')
				plt.ylabel('counts')
				plt.show()
			
		if not inj:
			#plot overlaid ToT histograms
			plt.xlabel('ToT (us)')
			plt.ylabel('Counts')
			plt.legend(loc="best")
			plt.title('DisHiDR=0, 0.3V inj')
			plt.show()
	
		if inj:
			#injection scan
			x=[0.2+(i*0.1) for i in range(14)]
			plt.plot(x,mean,marker="o")
			plt.xlabel("Injected voltage [V]")
			plt.ylabel("Average ToT [us]")
			plt.show()
		