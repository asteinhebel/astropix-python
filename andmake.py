import regex as re
MASK1 = "C:\\Users\\gs66c235\\astropix\kit-adl\cleanAstroPix\\amanda_python\\noiseMap_06_22_2022_603_75mV_lbnlTestFinal0\maskedPixels_GSFCbench_75mV_threshold0.txt"
MASK2 = "C:\\Users\\gs66c235\\astropix\kit-adl\cleanAstroPix\\amanda_python\\noiseMap_06_22_2022_603_75mV_lbnlTestFinal1\maskedPixels_GSFCbench_75mV_threshold0.txt"
#MASK3 = ""


# Stuff to and together two noise masks, for testing NOT FOR USE 
with open(MASK1, 'r') as file:
    mask1 = file.read()
with open(MASK2, 'r') as file:
    mask2 = file.read()
#with open(MASK3, 'r') as file:
#    mask3 = file.read()
        
bitmask1 = re.sub("[^01\n]", "", mask1).split('\n')
bitmask2 = re.sub("[^01\n]", "", mask2).split('\n')
#bitmask3 = re.sub("^[01\n]", "", mask3)
print(mask1)
#print(mask2)
bitmask1 = bitmask1[0:35]
bitmask2 = bitmask2[0:35]
#bitmask3 = bitmask3[0:35]
# used in construction
bitsmasked = 0
for i in range(0,35):
#    bits = (int(bitmask1[i], 2)) << 1
    bits = (int(bitmask1[i], 2) | int(bitmask2[i], 2)) << 1
    bitsmasked = bitsmasked + format(bits, '036b').count("1")

    print(f"self.recconfig[f'ColConfig{i}'] = 0b00{format(bits, '036b')}") 
print(f"Masked {bitsmasked} pixels, a total of {((bitsmasked/(35**2)) * 100)}% of the sensor")