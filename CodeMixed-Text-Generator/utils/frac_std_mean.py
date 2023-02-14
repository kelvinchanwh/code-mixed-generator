import numpy as np
import os

BASE_DIR = os.getcwd().split('utils')[0]
DATA_DIR = os.path.join(BASE_DIR, 'data')

def count_cs(tag3d, langtags, langind=1):
    '''
    Number of CS terms in an utterance.
    '''
    counter = 0
    for i in tag3d:
        if i[langind] != langtags[1] and i[langind] in langtags:
            counter += 1
    return counter


def stats_cs(tags3d, langtags, langind=1):
    '''
    Average of count_cs over all the utterances present.
    '''
    sp_avg, sp_std = 0, 0
    sp_list = []
    for tag in tags3d:
        sp_list.append(count_cs(tag, langtags, langind))

    sp_avg = np.mean(sp_list)
    sp_std = np.std(sp_list)

    return sp_avg, sp_std

def main(rcm_corpus, langtags):
    rcm_corpus = os.path.join(DATA_DIR, rcm_corpus)

    with open(rcm_corpus, "r") as f:
        data = f.readlines()

    processed_data = []
    for d in data:
        t = d.split()
        tmp = []

        for x in t:
            tmp.append(x.split('/'))
        
        processed_data.append(tmp)

    sp_avg, sp_std = stats_cs(processed_data, langtags)
    print("Mean and Standard Deviation of RCM Corpus:", (sp_avg, sp_std))

    return sp_avg, sp_std