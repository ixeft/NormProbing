import conf 
import sys, os, traceback, copy, re, math
from os.path import isfile, join
import numpy as np
from collections import defaultdict
import itertools

def parseLine(line):  
    """split a line by standard separator (\t, space)"""
    return [elem for elem in line.split()]

def openfile(Path):
    """take filepath as argument and return line of a file in a list."""
    fileIn = open(Path, "r")
    lines = fileIn.readlines()
    fileIn.close()
    return lines

def Add_New_Element_ToList(Id, List):
    """Append an element to a list if the element is not already present, as a set would work"""
    if Id not in List:
        List.append(Id)
    return List

def GetListFile(PathFile, FileExtension):
    """return list of file without extension from a list of files"""
    return [os.path.splitext(f)[0] for f in os.listdir(PathFile) if isfile(join(PathFile, f)) and os.path.splitext(f)[1] == '.' + FileExtension]

def parseFile(myFile):
    SeqNume=[]
    seqRNA=[]
    areaRX=[]
    areaBG=[]
    next(myFile)# to start from the second line
    for line in iter (myFile):
        sline = parseLine(line)
        SeqNume.append(sline[0])
        seqRNA.append(sline[1])
        areaRX.append(sline[4])
        areaBG.append(float(sline[6]))
    myFile.close()
    return SeqNume,seqRNA, areaRX, areaBG

def Filter_Raws_Nucleotides(var1,var2,var3,var4,SelectedNuc):
    Positions=[i for i,j in enumerate(var2) if j.upper() in [x.upper() for x in SelectedNuc] and j in ['A','U','C','G'] ]
    return Positions

def Mean_Meandeviation(List_reactiv,threshold,thresh_activ):
    Excluded=[elem for elem in List_reactiv if elem==-10 or elem=='NV']
    #print Excluded
    SET=list(set(List_reactiv)-set(Excluded))
    #print SET
    Exclusion=0
    if len(SET)<=1: # if only one value exists
        return (-10,0) 
    else:

        if len(Excluded)==1:
                # Get couple of 2 by 2 values then calculate their distance to chek if there is one distance above the threshold. This filter is applied only for values below 0.6

            for (item1,item2) in [elem for elem in itertools.combinations(SET,2)]:
                if abs(item1-item2)>threshold :
                    Exclusion=1
                    if item1>thresh_activ and item2>thresh_activ:
                        Exclusion=0
            if Exclusion==1:
                return (-20,0) 
            else:
                Mean=np.mean(SET)
                Meandev=sum([np.abs(xi-Mean) for xi in SET ])/float(len(SET))
                return (Mean, Meandev)
        else:     # in normal case the mean is calcuated
            return ( round(np.mean(SET),6), round(sum([np.abs(xi-np.mean(SET)) for xi in SET ])/float(len(SET)),6))



if __name__ == "__main__":
    SeqNume=[]
    seqRNA=[]
    areaRX=[]
    areaBG=[]
    NormDiff=dict()
    Data=dict()
    ListFile=[]
    Minimal_size=[]
    Listref=[]
    #Start=15
    #End=283
    for filz in GetListFile(conf.Path, conf.FileExtension):
       Listinter=[]
       ListFile.append(filz)
       try:
           Add_New_Element_ToList(filz.split('_')[0]+ '_'+ filz.split('_')[1]+ '_',Listref)
       except:
           print("Error: Filename must have the following format: [RNAseqname]_[reagent]_[number].txt\n" \
                 "Invalid format \"%s\"" % filz)
           sys.exit(1)

    #FileName=sys.argv[1]
    myFile=open( os.path.join(conf.Path, filz + '.' + conf.FileExtension),'r')  
    #Getlist(Path, fileextension):
    #filz= open ("./Qu-shape-output/"+FileName,'r')
            #print myFile
    [SeqNume,seqRNA, areaRX, areaBG]=parseFile(myFile)
            #print [SeqNume,seqRNA, areaRX, areaBG]
    if len([x.upper() for x in conf.SelectedNuc if x.upper() in ['A','U','C','G']])!=0 :
        Nucl=conf.SelectedNuc
    else:
        Nucl=["A","C","G","U"]
        
    index= Filter_Raws_Nucleotides(SeqNume,seqRNA, areaRX, areaBG,Nucl)
        #print SeqNume[0],SeqNume[-1]
    Minimal_size.append((filz,len(SeqNume)))
    # sort element from area BG
            #print areaBG
    sortedareaBG=sorted([areaBG[i] for i in index])
            #print sortedareaBG
    # get the last element in 10% of maximum value via percentile
    threshold=np.percentile(sortedareaBG, 90) 
    # Recalculate area BG values: value above the 90 percentile will have a value of 10^10
    #in order to mark stops position
    for item in index:
        if areaBG[item]>threshold:
            areaBG[item]=pow(10,10)
    #fixedLines = [list(line) for line in lines[1:]]
    # create reactivity profile
    diff = [(areaRX[i]-areaBG[i]) for i in index]
    # sort diff
    sortedDiff=sorted([diff[i] for i in range(len(diff))])
    # get 10 %  of the maximal differences, 2 % are considered as outliers 
    thresholdUp=np.percentile(sortedDiff, 98) 
    thresholdDown=np.percentile(sortedDiff, 90)
    # normalization with values between 
    Percen75=np.percentile(sortedDiff, 75)
    Percen25=np.percentile(sortedDiff, 25) 
    DF=1.5*(Percen75-Percen25)
    if len(SeqNume)<=300 or conf.Method=="Norm1":
        # Calculate average from the interval between 98 and 90 percentile
        normalizationTerm=np.average([sortedDiff[i] for i in range(len(sortedDiff)) if sortedDiff[i]<thresholdUp and sortedDiff[i]>thresholdDown])
    if len(SeqNume)>300 or conf.Method=="Norm2":
        # remove peaks with value above 75th percentile and 1.5(75th perc -25th perc)
                    
        AcceptedValues=[sortedDiff[i] for i in range(len(sortedDiff)) if (sortedDiff[i]<DF and sortedDiff[i]<Percen75 )]
        # 10% of the highest remining reactivities
        Perc=np.percentile(AcceptedValues, 90)
        normalizationTerm=np.average([AcceptedValues[i] for i in range(len(AcceptedValues))  if AcceptedValues[i] > Perc ])
    #calculate normalization_term
    #1- specify the nucleotides to undergo the normalization
    if len([x.upper() for x in conf.Nucreadout if x.upper() in ['A','U','C','G']])!=0 :
        Nuclreadout=conf.Nucreadout
    else:
        Nuclreadout=["A","C","G","U"]

    indexNucreadout = Filter_Raws_Nucleotides(SeqNume,seqRNA, areaRX, areaBG,Nuclreadout)

    for i in indexNucreadout:
        NormDiff[i]= (areaRX[i]-areaBG[i])/normalizationTerm 
    # Conditions on  Normdiff values <-10 takes as new value  -10,Normdiff between -10 and -0.3 becomes 0      
    for i in indexNucreadout:
        if NormDiff[i]<=-10:
            NormDiff[i]=-10
        if -10 < NormDiff[i] < conf.Lowervalue:
            NormDiff[i]=0
    # write in a file 
    with open( os.path.join(conf.OutputPath, filz + '.' + conf.FileExtension),'w') as o:
        o.write("%s\t%s\t%s\t\n"%("SeqNum","SeqRNA","Normalized_reactivity"))
        for i in range(len(SeqNume)):
            if i in indexNucreadout:
                o.write("%i\t%s\t%f\t\n"%(int(SeqNume[i]),seqRNA[i],float(NormDiff[i])))
                Listinter.append((int(SeqNume[i]),seqRNA[i],float(NormDiff[i])))
            else:
                o.write("%i\t%s\t%s\t\n"%(int(SeqNume[i]),seqRNA[i],'NV'))
                Listinter.append((int(SeqNume[i]),seqRNA[i],'NV'))
    
    Data[filz]=Listinter
    #print filz, Data['343_1M7_3']
    
    #for item in  Data['343_1M7_3']:
    #   print item[0]
     #       #print filz, Listinter[0][0], Listinter[-1][0]
    #print [len(Data[elem])for elem in Data.keys()]
    
    min_start=np.min([Data[elem][0][0] for elem in Data.keys()])
    #print min_start
    max_end=np.max([Data[elem][-1][0] for elem in Data.keys()])
    for elem in Data.keys():
        ToAd=[]
        ToAdend=[]
        if Data[elem][0][0]>= min_start:        
            ToAd=[(int(SeqNume[i]),seqRNA[i],'NV') for i in range(Data[elem][0][0]-min_start) ]
        Data[elem]=ToAd+Data[elem]

        if Data[elem][-1][0]<= max_end:
            ToAdend =[(int(SeqNume[i]),seqRNA[i],'NV') for i in range(max_end-Data[elem][-1][0])]
                            #print 
        Data[elem]=Data[elem]+ToAdend

    print "Normalization has been run successfully" 
    if int(conf.Task)==2 :
        Rang=dict()
        #print [len(Data[elem])for elem in Data.keys()]
        #print Listref
        OutputFolder='Reactivity'
        for elem in Listref:
            #print elem 
            if len([elem2 for (elem1,elem2) in Minimal_size if elem1.startswith(elem)])==1:
                print "You need more input files to calculate the reactivity for ", elem[:-1]
            else:
                #print [(elem1,elem2) for (elem1,elem2) in Minimal_size]
                # To normalize using the same size 
                Rang[elem]= np.min([elem2 for (elem1,elem2) in Minimal_size if elem1.startswith(elem) ] )
                #print Rang[elem]
                with open( os.path.join(OutputFolder, elem[:-1] + '.shape'),'w') as o:
                    o.write("%s\t%s\t%s\t%s\t\n"%("SeqNum","SeqRNA","Reactivity","Ecart_Moyen"))
                    for items in range(conf.Start,conf.End+1):
                        Lista=[]
                        #print "ietms",items, [indexNucreadout for indexNucreadout in Data.keys()]
                        #print "lol",indexNucreadout
                        for indexNucreadout in Data.keys() :
                            if indexNucreadout.startswith(elem):
                                #print indexNucreadout,Data[indexNucreadout]
                                indexation=0
                                for element in Data[indexNucreadout]:
                    
                                    if element[0]==items:
                                        Lista.append(Data[indexNucreadout][indexation][2])
                                        
                                    indexation+=1
                        if len(Lista)>1:
                            #print items,Lista
                            Mean_Mean=Mean_Meandeviation(Lista,conf.Threshold,conf.Desactiv_threshold)
                        else:
                            Mean_Mean=(-10,0)
                        #print Data[elem+'1'][items][0]
                        #print items,Mean_Mean[0],Mean_Mean[1]
                        o.write ("%i\t%f \t %f \t\n"%(items,Mean_Mean[0],Mean_Mean[1]))
                print "Normalization and Reactivity calculation have been run successfully for",elem[:-1]
