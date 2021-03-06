

# This script will parse through CSV files to capture the frequency of each 
# unique polymorphism found in a given peptide fragment across samples.
#
# Run the script using a command like this:
# python3 calc_poly_freq.py -peptide_map peptide_map.csv -sample_maps sample_map.csv -outfile my_out.tsv
#
# Author: James Matsumura

import pandas,argparse,collections

def main():

    parser = argparse.ArgumentParser(description='Script to count polymorphisms given a peptide map and sample data.')
    parser.add_argument('-peptide_map', type=str, required=True, help='Path to peptide file.')
    parser.add_argument('-sample_maps', type=str, required=True, help='Comma separated list of sample data.')
    parser.add_argument('-outfile', type=str, required=True, help='Name of the output file.')
    parser.add_argument('-nonreference', type=str, required=False, help='Add "yes" to this argument if there are variants to the same region present and you want to display each peptide fragment for poly AAs distinctly.')
    args = parser.parse_args()

    # row names are peptides, col names are sample IDs by their Subj+Timepoint
    rownames = []

    peptide_df = pandas.read_csv(args.peptide_map) # open up the peptide file
    peptide_dict = {}

    for index,row in peptide_df.iterrows():

        peptide_dict[row["Name"]] = {
            'name': row["Name"],
            'seq': row["Sequence"],
            'seq_s': row["StartAA"],
            'seq_e': row["EndAA"],
            'original_poly': set()
        }

        rownames.append(row["Name"]) # maintain dict order via this

    samples = args.sample_maps.split(',')
    sample_dict = {}
    for sample in samples:
        sample_df = pandas.read_csv(sample)
        # want these ordered so that we can build the output in order
        poly_aa_pos = [] 

        for col in list(sample_df):
            if col.startswith("AA"):
                # this tells us which polymorphic AA positions we will check 
                # against each peptide fragment
                poly_aa_pos.append(int(col.split('AA')[1]))

        # each sample will have a dif set of fragments we want to check, note which
        relevant_peptides = set() 
        for fragment in rownames:
            start = int(peptide_dict[fragment]['seq_s'])
            end = int(peptide_dict[fragment]['seq_e'])

            for pos in poly_aa_pos:
                if start <= pos <= end:
                    relevant_peptides.add(fragment)
                    break

        for index,row in sample_df.iterrows():

            curr_sample = [] # a list of all the values found for this sample

            for fragment in rownames:

                if fragment in relevant_peptides: 

                    relevant_positions = []
                    num_of_poly = 0
                    seq = peptide_dict[fragment]['seq']
                    start = int(peptide_dict[fragment]['seq_s'])
                    end = int(peptide_dict[fragment]['seq_e'])

                    for pos in poly_aa_pos:
                        if start <= pos <= end:
                            relevant_positions.append(pos)
                        elif end < int(pos): # got em all, do a check
                            break

                    if len(relevant_positions) > 0:
                        for pos in relevant_positions:

                            pos_with_aa = "AA{0}".format(pos)

                            # need to offset based on where the fragment starts
                            adj_pos = pos - start
                            peptide_dict[fragment]['original_poly'].add("{0}:{1}".format(seq[adj_pos],pos))
                            
                            if pos not in peptide_dict[fragment]:
                                peptide_dict[fragment][pos] = ""

                            peptide_dict[fragment][pos] += row[pos_with_aa]

    # it's a bit tricky since only some of the keys made in the peptide_dict
    # are the poly AA positions. Thus, going to build a final dictionary that
    # can be more easily sorted and written out using the positions as keys. 
    final_dict = {} 
    
    for fragment in rownames:
        for key in peptide_dict[fragment]:
            if isinstance(key, int):

                original_aa = ""

                # find out the original base using the set built in original_poly
                for original in peptide_dict[fragment]['original_poly']:
                    ele = original.split(':')
                    if key == int(ele[1]):
                        original_aa = ele[0]

                # if it's not a reference sequence split into multiple fragments 
                # and we have variant seqs, need the final_dict to be composed of
                # poly AAs per distinct peptide. 
                if args.nonreference:
                    if fragment not in final_dict:
                        final_dict[fragment] = {}

                    # know that each key will be unique to each fragment
                    final_dict[fragment][key] = {'original_aa':original_aa,'freqs':frequency_check(peptide_dict[fragment][key])}

                
                elif key not in final_dict:
                    final_dict[key] = {'original_aa':original_aa,'freqs':frequency_check(peptide_dict[fragment][key])}

    with open(args.outfile,'w') as out:

        if args.nonreference:
            for fragment in rownames:
                if fragment in relevant_peptides:
                    ordered = collections.OrderedDict(sorted(final_dict[fragment].items()))

                    for key in ordered:
                        out.write("{0}\t{1}\t{2}\t{3}\n".format(fragment,ordered[key]['original_aa'],key,ordered[key]['freqs']))

        else:
            ordered = collections.OrderedDict(sorted(final_dict.items()))

            for key in ordered:
                out.write("{0}\t{1}\t{2}\n".format(ordered[key]['original_aa'],key,ordered[key]['freqs']))


# Returns a string with frequencies for how many times each amino acid appears
# in a string
def frequency_check(string):
    freqs = collections.Counter(string).most_common()
    total = sum(collections.Counter(string).values())
    final_list = []
    for counts in freqs:
        final_list.append("{0}:{1:.3f}".format(counts[0],counts[1]/total))
    return "\t".join(final_list)

if __name__ == '__main__':
    main()