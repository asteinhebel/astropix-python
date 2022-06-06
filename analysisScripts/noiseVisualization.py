import glob,os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors


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
		
def constructMasks(counts,high):

	maskArr=np.zeros((35,35)) #filler value

	for col in range(len(counts)):
		bits="0" #Every one should end in 0 
		for row in range(len(counts[0])):
			if counts[col][row]>high:
				bits+="1"#mask
				maskArr[col][row]=-1
			else:
				bits+="0"#leave on
		#Add '_' delimeters 
		bits='_'.join(bits[i:i+5] for i in range(0, len(bits), 5))
		#invert order
		bits=bits[::-1]
		print(f"self.recconfig[f'ColConfig{col}'] = 0b00{bits}")
		#print(f"self.reconfig={{'ColConfig{col}':0b00{bits}}}")

	return maskArr

if __name__ == "__main__":

	#########################
	## variables you may want to change
	#loc="bench"
	#loc="cavern"
	loc="GSFCbench"
	dataDir=f"noise_{loc}/"
	saveto=f"noiseMap_{loc}.pdf"
	threshold=0
	maxIt=500
	#########################


	#create empty full size array
	allPix=35
	counts = np.ones( (allPix, allPix) )*np.nan
	expected=np.arange(allPix)
	
	os.chdir(dataDir)	
	for f in sorted(glob.glob("log*.txt")): #get all txt files in datadir in alphabetic order ('sorted' alphabatizes)
		colVal=np.loadtxt(f,usecols=0,skiprows=1,max_rows=2,dtype="int")[0]
		countVals=np.loadtxt(f,skiprows=1,usecols=(1,2))
		#insert np.nan into array pulled from file if there are missing pixels 
		## should be 35 entries for 35 pixels - if no data, holds np.nan
		missingPixels=np.setdiff1d(expected,countVals[:,0])
		pixelIndex= missingPixels - np.arange(len(missingPixels))
		countVals=np.insert(countVals,pixelIndex,np.nan,axis=0)
		countVals=countVals.reshape(allPix,2)
		counts[colVal]=countVals[:,1]
		
	counts_tst=np.reshape(counts,(allPix,allPix)).T
	fig = plt.figure()
	ax = fig.add_subplot(111)
	cax=ax.matshow(counts_tst)
	ax.invert_yaxis()#Show (0,0) origin on bottom left
	cbar = plt.colorbar(cax)
	cbar.set_label(f'Counts (of {maxIt})') 	
	plt.tight_layout() #reduce margin space	
	
	#plt.show()
	saveFromInput(saveto)
	
	#Create masking strings
	print("Create Masking Strings")
	maskArr=constructMasks(counts,threshold)
	
	#Count noisy pixels for display in terminal
	print(f"Total Pixels: {allPix*allPix}")
	unread=np.count_nonzero(np.isnan(counts))
	saturated=np.count_nonzero(counts==maxIt)
	good=np.count_nonzero(counts==0)
	noisy=(counts>threshold).sum()
	noisyish=allPix*allPix-noisy-good-unread
	print(f"Unread pixels: {unread/allPix/allPix*100:.3f}% ({unread} pixels)")
	print(f"Saturated pixels (count=={maxIt}): {saturated/allPix/allPix*100:.3f}% ({saturated} pixels)")
	print(f"Noisy pixels (count>{threshold}): {noisy/allPix/allPix*100:.3f}% ({noisy} pixels)")
	print(f"Slightly noisy pixels (0<count<{threshold}): {noisyish/allPix/allPix*100:.3f}% ({noisyish} pixels)")

	#export array of which pixels are masked
	filename=f"maskedPixels_{loc}_threshold{threshold}.txt"
	#Organize array so that it matches structure of visualization ((0,0) origin pixel at bottom left)
	maskArr=np.fliplr(maskArr)
	maskArr=maskArr.T
	np.savetxt(filename, maskArr, fmt="%i")#save as ints
