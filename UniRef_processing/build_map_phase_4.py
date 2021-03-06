#!/usr/bin/python
#
# Final script once again just requires the same input from phase 3/3.5.
#
# Author: James Matsumura

import sys, os, re, gzip

sprot_dat =  str(sys.argv[1]) 

sprot_file = gzip.open(sprot_dat, 'rb') 
outFile = './final_file.tsv'

footerFound = False
accessionFound = False
relevantUnirefEntry = False 

regexForAccession = r"^AC\s+(.*);"
regexForFooter = r"^\/\/$"
regexForMappedAccession = r"UniRef100\_(\w+)"
regexForSprotReferences = r"ECO:0000269\|PubMed:(\d+)"

uniquePMIds = set()
uniqueUnirefIds = set()
sprotData = {}

print 'stage1'
# Just gather the data from the sprot file, add these values to their objects later. Note
# that only a hash/dict is needed here as there are only two data points to store. 
for line in sprot_file:
	if footerFound == True: # reinitialize values for next record
		accessionFound = False
		footerFound = False
		uniquePMIds.clear()
	elif accessionFound == True:
		if re.search(regexForFooter, line):
			if ';' in foundAccession:
				multiAccessions = foundAccession.split('; ')
				for x in multiAccessions: # iterate over this ~2-3 len list
					if not len(uniquePMIds) == 0:
						sprotData[x] = '|'.join(uniquePMIds)
			else:
				if not len(uniquePMIds) == 0:
					sprotData[foundAccession] = '|'.join(uniquePMIds)
			footerFound = True
		else:
			if 'ECO:0000269|PubMed' in line:
				pmid = re.search(regexForSprotReferences, line).group(1)
				uniquePMIds = uniquePMIds | {pmid}
	else:
		findAccession = re.search(regexForAccession, line)
		if findAccession:
			foundAccession = findAccession.group(1)
			accessionFound = True

# These next chunks are inefficient, but I only need to run this code once to get the output and
# the inconsistent formatting of the data pulled made it too much a hassle to reformat only to 
# make this step more efficient. Broken up in such a way via intermediary files used to avoid 
# hitting >n^2 complexity. 

print 'stage2'
# Finally, append the SwissProt data and all the references associated with each UniProt acc
with open('./phase_3.5.tsv', 'r') as input_file, open(outFile, 'w') as output_file:
	for line in input_file:
		line = line.replace('\n','')
		elements = line.split('\t')
		uniprot_refs = '' # PM IDs linked to the accs
		uniref_refs = ''
		if elements[4]=='' and elements[5]=='': # no UniRef/UniProt
			continue
		# Should assume that if there's a UniRef, there's a UniProt
		elif not elements[4]=='' and not elements[5]=='': 
			if ',' in elements[4]:
				uniprots = elements[4].split(',')
				for x in uniprots:
					if x in sprotData:
						if uniprot_refs == '':
							uniprot_refs += 'PMID:'+sprotData[x]
						else:
							uniprot_refs += ';PMID:'+sprotData[x]
					else:
						if uniprot_refs != '':
							uniprot_refs += ';NONE'
			else:
				if elements[4] in sprotData:
					uniprot_refs += 'PMID:'+sprotData[elements[4]]
			if ',' in elements[5]:
				unirefs = elements[5].split(',') # possible to have multiple here
				for x in unirefs:
					if x in sprotData:
						if uniref_refs == '':
							uniref_refs += 'PMID:'+sprotData[x]
						else:
							uniref_refs += ';PMID:'+sprotData[x]
					else:
						if uniref_refs != '':
							uniref_refs += ';NONE'
			else:
				if elements[5] in sprotData:
					uniref_refs += 'PMID:'+sprotData[elements[5]]
		output_file.write(line+'\t'+uniprot_refs+'\t'+uniref_refs+'\n')
