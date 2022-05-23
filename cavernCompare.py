import glob,os
import numpy as np
import matplotlib.pyplot as plt





if __name__ == "__main__":

	#########################
	## variables you may want to change
	testRun="TEST"
	mask0="noise_cavern/maskedPixels_cavern_threshold0.txt"
	mask1="noise_cavern_retest/maskedPixels_cavern_retest_threshold0.txt"
	#########################


	#Pull in array structure and masked pixels from external file
	#counts=[[-100]*35]*35 #filler value
	noise0=np.loadtxt(mask0)
	noise1=np.loadtxt(mask1)
	
	print(f"Total noisy pixels in orig run: {abs(sum(sum(noise0)))}")
	print(f"Total noisy pixels in new run: {abs(sum(sum(noise1)))}")
	
	origNoise=0
	newNoise=0
	sharedNoise=0
	unsharedNoise=0
	#See if noise0 a subset of noise1
	for i in range(len(noise0)):
		for j in range(len(noise0[0])):
			if noise0[i][j]==-1:
				origNoise+=1
				if noise1[i][j]==-1:
					sharedNoise+=1
				else:
					unsharedNoise+=1
					
	print(f"Orig noisy pixels also in new run: {sharedNoise}")
	print(f"Orig noisy pixels NOT NOISY in new run: {unsharedNoise}")
	print(f"New noisy pixels not noisy in orig run: {abs(sum(sum(noise1)))-sharedNoise}")