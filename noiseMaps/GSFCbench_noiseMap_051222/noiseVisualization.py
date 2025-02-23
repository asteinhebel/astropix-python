import glob,os
import numpy as np
import matplotlib.pyplot as plt
import numpy.ma as ma
from matplotlib import colors

def getRowCounts(f):

	fileIn = open(f,'r')
	lines = fileIn.readlines()
	#line[0] = header -> remove
	del lines[0]
	#columns separated by tabs
	#Column ~ Row ~ Counts ~ Timestamp
	countVals=np.ones((35))*-100
	for line in lines:
		#countVals.append(float(line.split('\t')[2]))
		countVals[int(line.split('\t')[1])]=int(line.split('\t')[2])
	return countVals

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
	loc="cavern_retest"
	dataDir=f"noise_{loc}/"
	dataDir="./"
	saveto=f"noiseMap_{loc}.pdf"
	threshold=0
	maxIt=100
	#########################


	#create empty full size array
	#counts=[[-100]*35]*35 #filler value
	counts = np.ones( (35, 35) )*-100
	arrMax=[]
	nmbs=['0','1','2','3','4','5','6','7','8','9']
	
	os.chdir(dataDir)	
	for f in sorted(glob.glob("log*.txt")): #get all txt files in datadir in alphabetic order ('sorted' alphabatizes)
		colname=f.split('_')[1]
		if colname[-2] in nmbs: #if two digit column
			colVal=int(colname[-2])*10+int(colname[-1])
		else:
			colVal=int(colname[-1])
		countVals=getRowCounts(f)
		counts[colVal]=countVals
		for i,c in enumerate(countVals):
			if c==maxIt:
				arrMax.append([colVal,i])
	
	totalCols=len(counts)
	counts_tst=np.reshape(counts,(totalCols,35)).T
	counts_tst=ma.masked_equal(counts_tst, -100)
	fig = plt.figure()
	ax = fig.add_subplot(111)
	cax=ax.matshow(counts_tst) #, norm=colors.LogNorm()
	ax.invert_yaxis()#Show (0,0) origin on bottom left
	cbar = plt.colorbar(cax)
	cbar.set_label(f'Counts (of {maxIt})') 	
	plt.tight_layout() #reduce margin space	
	
	#plt.show()
	saveFromInput(saveto)
	
	#Create masking strings
	print("Create Masking Strings")
	maskArr=constructMasks(counts,threshold)
	
	#fullArray=35*totalCols
	#counts=sum(counts,[])#flatten list

	noisy = np.sum(counts>threshold)
	noisyish = np.sum((counts>0) & (counts<maxIt))
	fullArray = ma.count(counts_tst)
	saturated = np.sum(counts == maxIt)
	#noisy=0
	#noisyish=0
	#for c in counts:
	#	if c>threshold:
	#		noisy+=1
	#	elif c>0:
	#		noisyish+=1
	
	print(f"Total Pixels: {fullArray}")
	print(f"Saturated pixels (count=={maxIt}): {saturated/fullArray*100:.3f}% ({saturated} pixels)")
	print(f"Noisy pixels (count>{threshold}): {noisy/fullArray*100:.3f}% ({noisy} pixels)")
	print(f"Slightly noisy pixels (0<count<{maxIt}): {noisyish/fullArray*100:.3f}% ({noisyish} pixels)")

	#export array of which pixels are masked
	filename=f"maskedPixels_{loc}_threshold{threshold}.txt"
	#Organize array so that it matches structure of visualization ((0,0) origin pixel at bottom left)
	maskArr=np.fliplr(maskArr)
	maskArr=maskArr.T
	np.savetxt(filename, maskArr, fmt="%i")#save as ints
