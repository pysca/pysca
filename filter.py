###############################################################################
# Part of a group of scripts targetted at performing genome wide statistical  #
# coupling analysis to predict protein interactions.                          #
# filter.py removes nonredundant taxa from the database. This saves space and #
# speeds up the execution for the clustal.py                                  #
###############################################################################

import water,fasta
from sys import exit
import os

#Location of the proteome.fa file and the base directory for all the analysis
headDir = '__ur_directory_goes_here__'

if headDir[-1] != '/':
    headDir = headDir + '/'
inFN    = headDir + "proteome.fa"
searchDir  = headDir + "search/"
outDir  = headDir + "filter/"

if not os.path.isfile(inFN):
    print "Input file, proteome.fa not found in the head directory: %s" %headDir
    print "Will now exit ..."
    exit()


try:
    os.mkdir(outDir)
except OSError:
    print "The output file directory (%s) already exists... Not creating" %outDir

#This script needs to run two loops -- The first accrues a list of taxids & the second will remove 
#taxids that do not appear more than once in the database -- there cannot be coevolution info in 
#a taxon that only appears once in one gene

h,s = fasta.importFasta(inFN)
nseqs  = len(h)
digits = len(str(h))

files = [i for i in os.listdir(searchDir) if i[-3:] == '.fa']
files.sort(key = lambda x: int(x[:-3]))

taxa = {}

#First loop builds list of redundant taxa
for FN in files:
    with open(searchDir + FN) as lines:
        for line in lines:
            if line[0] == '>':
                taxids = line.split('|')[-1].split(';')
                for taxid in taxids:
                    if taxid in taxa:
                        taxa[taxid] = True
                    else:
                        taxa[taxid] = False
for k,v in taxa.items():
    if not v:
        taxa.pop(k, None)

#Second loop filters fasta files to remove nonredundant taxa
#Note -- this will also expand redundant sequences with different taxids into separate entries
for FN in files:
    outFN = outDir + FN 
    with open(searchDir + FN) as lines, open(outFN, 'w') as out:
        for header in lines:
            taxids = header.split('|')[-1].split(';')
            header = '|'.join(header.split('|')[:-1]) + '\n'
            seq    = lines.next()
            for taxid in taxids:
                if taxid in taxa:
                    out.write(header)
                    out.write(seq)
