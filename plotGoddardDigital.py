import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm
import glob

import argparse

def getPSData( name ):
    a = pd.read_csv(name , sep=',')
    return a

def getMaskLogData(dir="logScanData", gl="logMaskNoise_Col*_20220509*.txt"):
   
    allHits = None


    for name in glob.glob(f"{dir}/{gl}") :
    
        #a = pd.read_csv(name , sep='\s+')
        a = pd.read_csv(name , sep=',')
        print(name, a.columns)
        
        if allHits is None:
            allHits = a
        else:
            allHits = pd.concat([allHits, a])

        
    allHits.rename(columns = {'#Col':'Col'}, inplace = True)

    mask = allHits.groupby(["Row", "Col"]).min()["Count"]
    
    mask = mask[mask>0]

    return mask


def getBeamData(dir="FermilabTestBeamData_Proton120GeV_May2022", gl="beamDigitalMasked_inBeam_*.txt"):

    allEvents = None

    print( f"{dir}/{gl}" )

    for i, name in enumerate( glob.glob(f"{dir}/{gl}") ):

        h = 0
        j = 0
       # with open(name, "r") as f:
       #     for line in f.readlines() :
       #         if(len(line))>1:
       #             j = j + 1
       #
       #         if "NEvent" in line:
       #             h = j-1
       #             break
    
        
       # if h > 0:
        
        try:

                a = pd.read_csv(name , sep=',', header=h)
                #a = pd.read_csv(name , sep='\s+', header=h)
                a["fileID"] = i
                
                if allEvents is None:
                    allEvents = a
                else:
                    allEvents = pd.concat([allEvents, a])
        except:
                pass

    return allEvents


parser = argparse.ArgumentParser(description='Plot beam test results')
parser.add_argument('--beamdir', type=str, default="FermilabTestBeamData_Proton120GeV_May2022", required=False,
                    help='Directory with test beam data')
                                        
parser.add_argument('--beamglob', type=str, default="beamDigitalMasked_inBeam_*.txt", required=False,
                    help='filenames (string with wildcards) for mask log names')

parser.add_argument('--maskdir', type=str, default="logScanData", required=False,
                    help='Directory with mask log files')
                    
parser.add_argument('--maskglob', type=str, default="logMaskNoise_Col*_20220509*.txt", required=False,
                    help='filenames (string with wildcards) for mask log names')
parser.add_argument('--hvfile', type=str, default="lbnl_ps_data/LBNL_beam_603_30_table_22-06-26_01-04-11.csv", required=False,
                    help='filename for PS data')

args = parser.parse_args()
print(args)


a = getBeamData(args.beamdir, args.beamglob)

print(a)

theTimes = a.groupby(["NEvent", "fileID"]).mean().RealTime.to_numpy()
theTimes.sort()
deltaT = theTimes[1:] - theTimes[:-1]

plt.hist( deltaT, bins= np.linspace(0, 10, 100) )
plt.yscale("log")

plt.grid()
plt.xlabel("DeltaT between successive events")

plt.savefig("DeltaT.png")
plt.show()

exit()



v_raw = getPSData(args.hvfile)

v = v_raw.groupby(v_raw.SEC).mean()

v.REL = v.index - a.RealTime.min() - 31820.6824157238


a.RealTime -= a.RealTime.min()

print(a)

a = a.reset_index()

n, bins, _ = plt.hist(a.Payload, bins = np.linspace(-0.5, 8.5, 10))

print(bins)

plt.xlabel("Payload value")
plt.ylabel("Frequency [a.u.]")
plt.grid()
plt.yscale("log")

plt.savefig("payload.png")
plt.clf()

print(set(a.Payload))

print(set(a.ChipId))

a["Valid Payload"] = ((a.Payload == 4 ) | (a.Payload == ' 4' ))
a["Valid ChipID"] = ((a.ChipId == 0) | (a.ChipId == '0'))

a.pivot(columns=['Valid Payload', 'Valid ChipID']).RealTime.plot(kind = 'hist', stacked=True, bins = np.linspace(0, 900, 181), zorder=1)
#a.RealTime.plot(kind = 'hist', stacked=True, bins = np.linspace(0, 300, 61), zorder=1)

plt.xlabel("Time in run (s)")

plt.legend(title="Valid Payload, valid ChipID")

plt.title(args.beamglob)

if True:
    ax1 = plt.subplot()
    ax1.set_ylabel("Rate (per 5s)")
    ax2 = ax1.twinx()
    ax2.set_ylabel("- bias current (A)")
    #ax2.set_yscale("log")
    l2, = ax2.plot(v.REL, -v.READ, "-", color="black", zorder = 2, lw=0.5)


plt.savefig("rates2.png")
#plt.show()
plt.clf()

a.pivot(columns=['Row/Col']).RealTime.plot(kind = 'hist', stacked=True, bins = np.linspace(0, 900, 181), zorder=1)
#a.RealTime.plot(kind = 'hist', stacked=True, bins = np.linspace(0, 300, 61), zorder=1)

plt.xlabel("Time in run (s)")

plt.legend(title="")

plt.title(args.beamglob)

if True:
    ax1 = plt.subplot()
    ax1.set_ylabel("Rate (per 5s)")
    ax2 = ax1.twinx()
    #ax2.set_yscale("log")

    ax2.set_ylabel("- bias current (A)")
    l2, = ax2.plot(v.REL, -v.READ, "-", color="black", zorder = 2, lw=0.5)


plt.savefig("rates3.png")
#plt.show()
plt.clf()


a.groupby(["NEvent", "fileID"]).mean().RealTime.plot(kind = 'hist', stacked=True, bins = np.linspace(0, 900, 181), zorder=1)
#a.RealTime.plot(kind = 'hist', stacked=True, bins = np.linspace(0, 300, 61), zorder=1)

plt.xlabel("Time in run (s)")

#plt.legend(title="")

plt.title(args.beamglob)

if True:
    ax1 = plt.subplot()
    ax1.set_ylabel("Readout rate (per 5s)")
    ax2 = ax1.twinx()
    ax2.set_ylabel("- bias current (A)")
    l2, = ax2.plot(v.REL, -v.READ, "-", color="black", zorder = 2, lw=0.5)
    #ax2.set_yscale("log")


plt.savefig("rates4.png")
#plt.show()
plt.clf()

#remove hits with invalid payload or chipID
a = a[ ((a.Payload == 4 ) | (a.Payload == ' 4' )) & ((a.ChipId == 0) | (a.ChipId == '0')) ]

b = a.set_index(["NEvent", "tStamp", "fileID"])

#this is needed to find "good" (uniquely associated) hits
g  = a.groupby(["NEvent", "tStamp", "fileID"] )

n, bins, _ = plt.hist(g.count().Payload, bins = np.linspace(0.5, 25.5, 26))

plt.xlabel("Number of hits with same timestamp and eventID")
plt.ylabel("Frequency [a.u.]")
plt.grid()
plt.yscale("log")

n = n.astype(int)

total = np.sum(n)

print( f"1:  {n[0]} ({100*n[0]/total:.1f}%)" )
print( f"2:  {n[1]} ({100*n[1]/total:.1f}%)" )
print( f"3+: {np.sum(n[2:])} ({100*np.sum(n[2:])/total:.1f}%)" )

plt.savefig("hitMultiplicity.png")
plt.clf()


c = g.count().Payload

t = g.mean()

t["multiplicity"] = c


#for i, tt in t.groupby(t.multiplicity):
#    plt.hist( tt.RealTime, bins = np.linspace(0, 300, 31), alpha=0.5, label=i, stacked=True )
#plt.hist( t.groupby(t.multiplicity).RealTime, bins = np.linspace(0, 300, 31), alpha=0.5, stacked=True)


t.pivot(columns='multiplicity').RealTime.plot(kind = 'hist', stacked=True, bins = np.linspace(0, 900, 181), zorder=1)

plt.xlabel("Time in run (s)")

plt.legend(title="Hit multiplicity")

plt.title(args.beamglob)

if True:
    ax1 = plt.subplot()
    ax1.set_ylabel("Rate (per 5s)")
    ax2 = ax1.twinx()
    ax2.set_ylabel("- bias current (A)")
    l2, = ax2.plot(v.REL, -v.READ, "-", color="black", zorder = 2, lw=0.5)


plt.savefig("rates.png")
#plt.show()


print(t[t.multiplicity==2])

#plt.show()

#exit()

c = c[c==2]
i = c.index

b = b.loc[i]
#these are now the "good" hits

print( b )

df_row = b[b["Row/Col"]=="Row"]
df_col = b[b["Row/Col"]=="Col"]


df = pd.merge(df_row, df_col, left_index=True, right_index=True, suffixes = ["_row", "_col"])

print(df)



plt.clf()

df_on = df[(df.Locatn_row<35) & (df.Locatn_col<35)]
df_off = df[(df.Locatn_row>=35) | (df.Locatn_col>=35)]

plt.plot(df_on["ToT(us)_col"], df_on["ToT(us)_row"], ".", alpha=0.3, label = "Valid location" )
plt.plot(df_off["ToT(us)_col"], df_off["ToT(us)_row"], ".", alpha=0.3, label = "Invalid location" )
plt.legend()

plt.grid()
plt.xlabel("ToT_col (us)")
plt.ylabel("ToT_row (us)")


plt.savefig("ToT.png")
plt.clf()


plt.hist(df_on["ToT(us)_col"] - df_on["ToT(us)_row"], bins = np.linspace(-0.5, 0.5, 100) )

plt.grid()
plt.xlabel("ToT_col - ToT_row (us), valid pixels only")
plt.ylabel("Occurences")
plt.yscale("log")

plt.savefig("deltaToT.png")
plt.clf()

bins = np.linspace(-0.5, 63.5, 65), np.linspace(-0.5, 63.5, 65),


n, binsx, binsy, art = plt.hist2d( df["Locatn_row"], df["Locatn_col"], bins=bins, cmin=1, norm=LogNorm())
plt.xlabel("Row ID")
plt.ylabel("Col ID")

cbar = plt.colorbar(art)
cbar.set_label("Number of hits")

plt.savefig("hitLocation.png")


plt.xlim(-0.5, 35.5)
plt.ylim(-0.5, 35.5)

if args.maskdir is not None:

    #mask = getMaskLogData(args.maskdir, args.maskglob)
    #plt.plot( mask.index.get_level_values("Row"), mask.index.get_level_values("Col"), "s", color="red", markersize=3, alpha=0.4, label = "masked pixel")

    #plt.title("Masked pixels overlaid in red")

    #plt.savefig("hitLocationMask.png")
    plt.clf()


    #now select only the hits with consistent ToT measurements.

    #df_goodToT = df[(df["ToT(us)_col"] - df["ToT(us)_row"]<0.0) & (df["ToT(us)_col"] - df["ToT(us)_row"]>-0.3)  ]
    df_goodToT = df[(df["ToT(us)_col"] - df["ToT(us)_row"]<0.2) & (df["ToT(us)_col"] - df["ToT(us)_row"]>-0.3)  ]

    n, binsx, binsy, art = plt.hist2d( df_goodToT["Locatn_row"], df_goodToT["Locatn_col"], bins=bins, cmin=1, norm=LogNorm())
    plt.xlabel("Row ID")
    plt.ylabel("Col ID")

    cbar = plt.colorbar(art)
    cbar.set_label("Number of hits")


    plt.xlim(-0.5, 35.5)
    plt.ylim(-0.5, 35.5)


    #mask = getMaskLogData(args.maskdir, args.maskglob)
    #plt.plot( mask.index.get_level_values("Row"), mask.index.get_level_values("Col"), "s", color="red", markersize=3, alpha=0.4, label = "masked pixel")

    #plt.title("Masked pixels overlaid in red, hits with consistent ToT only")
    plt.title("Hits with consistent ToT only")

    plt.savefig("hitLocationGoodToT.png")
    plt.clf()

