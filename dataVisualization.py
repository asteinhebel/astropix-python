import glob,os
import numpy as np
import matplotlib.pyplot as plt

#####################################
## RUN noiseVisualization.py FIRST
## Need input txt file of masked pixels
######################################

def getHitPixels(f):

	fileIn = open(f,'r')
	lines = fileIn.readlines()
	del lines[0:7] #header
	
	hits=[]
	for line in lines:
		lineVals=line.split('\t')
		if lineVals[0]=='0':#part of initial FPGA dump
			continue
		if len(lineVals)==1: #empty line
			continue
		lineVals[-1]=lineVals[-1][:-2] #remove \n at end of line
		#Convert Row/Col distinction to float: Row==0, Col==1
		if lineVals[4]=='Row':
			lineVals[4]=0
		else:
			lineVals[4]=1
		hits.append([float(x) for x in lineVals])
	
	foundHits=[]
	#Find paired hit events - for each event number there should only be two entries and it should be one row/one column
	for i in range(len(hits)-1):
		if (hits[i][0]==hits[i+1][0]) and (hits[i][0]!=hits[i-1][0]) and (hits[i][4]!=hits[i+1][4]):#if same event but one row and one column and no other listed rows before this pair
			foundHits.append([int(hits[i+1][3]),34-int(hits[i][3]),hits[i+1][-1],hits[i][-1]])
			#subtract row number from 35 so it plots in proper orientation

	return foundHits

def saveFromInput(saveFile): 
	plot=plt.gcf() #get current figure - saves fig in case savePlt==True
	plt.show() #creates new figure for display
	inp= 'a'
	while inp!='y' and inp!='n':
		print("Save plot? y/n")
		inp = input()
	savePlt=True if inp=='y' else False
	if savePlt: #save plt stored with plt.gcf()
		print(f"Saving {saveFile}")
		plot.savefig(saveFile)

if __name__ == "__main__":

	#########################
	## variables you may want to change
	testRun="TEST"
	dataDir=f"data_noiseTesting/"
	saveto=f"hitmap_{testRun}.pdf"
	mask="noise_cavern/maskedPixels_cavern_threshold0.txt"
	#########################


	#Pull in array structure and masked pixels from external file
	#counts=[[-100]*35]*35 #filler value
	hits=np.loadtxt(mask)
	
	#Plot masked pixels
	fig = plt.figure()
	ax = fig.add_subplot(111)
	cax=ax.matshow(hits,cmap=plt.cm.YlOrRd)
	#redisplay y axis to match proper labeling
	ylabels=[34-2*i for i in range(18)]
	ax.set_xticks([2*i for i in range(18)])
	ax.set_yticks([2*i for i in range(18)])
	ax.set_yticklabels(ylabels)
	cbar = plt.colorbar(cax)
	cbar.set_label('Counts') 	
	plt.tight_layout() #reduce margin space	
	
	#plt.show()
	saveFromInput(f"{dataDir}maskedPixels_{testRun}.pdf")
	
	
	totPixels=len(hits)*len(hits[0])
	maskedPixels=abs(sum(sum(hits)))
	print(f"{maskedPixels/totPixels*100:.2f}% of pixels masked ({int(maskedPixels)}/{totPixels})")
	
	#Pull in data files
	#Store pixel position and ToT(us) value for matching row/col pairs of a real hit
	os.chdir(dataDir)	
	for f in sorted(glob.glob("beam*.txt")): #get all txt files in datadir in alphabetic order ('sorted' alphabatizes)
		recHit=getHitPixels(f) #Returns: [col, row, col ToT, row ToT]
		#dataHits.append(recHit)#Each data file is a 2D array with 4 columns
		#Add a hit in the plotted matrix 
		for foundHit in recHit:
			hits[foundHit[1]][foundHit[0]]+=1
			
	#Plot activated pixels
	fig = plt.figure()
	ax = fig.add_subplot(111)
	cax=ax.matshow(hits, cmap=plt.cm.YlOrRd)
	#redisplay y axis to match proper labeling
	ylabels=[34-2*i for i in range(18)]
	ax.set_xticks([2*i for i in range(18)])
	ax.set_yticks([2*i for i in range(18)])
	ax.set_yticklabels(ylabels)
	cbar = plt.colorbar(cax)
	cbar.set_label('Counts') 	
	plt.tight_layout() #reduce margin space	
	
	#plt.show()	
	saveFromInput(saveto)
	
	