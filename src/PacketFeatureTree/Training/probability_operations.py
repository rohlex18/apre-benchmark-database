from typing import List, Tuple
import numpy as np
import dataclasses

@dataclasses.dataclass(frozen=True)
class Field:
    name: str   
    n_bytes: int
    
def best(probabilities: np.ndarray, fields: List[Field]) -> Tuple[List[str], float]:
    length = len(probabilities)
    #cache = [([], 1.0)] # With zero bytes remaining, best option is [], with probability 1.0
    best_prob = np.zeros(length+1)
    best_prob[0] = 1
    best_path = [[]] * (length+1)
    # Iteratively build solutions with 1 byte remaining, 2 bytes remaining, etc.   
    for n_bytes_remaining in range(1, len(probabilities) + 1):
        #best_prob = 0        
        #best_path = None        
        for i, field in enumerate(fields):
            if (next_bytes_remaining := n_bytes_remaining - field.n_bytes) >= 0:
                next_path, next_prob = best_path[next_bytes_remaining], best_prob[next_bytes_remaining]
                this_prob = probabilities[-n_bytes_remaining:len(probabilities) - (next_bytes_remaining), i].prod()*next_prob#*(1/len(fields))           
                if this_prob > best_prob[n_bytes_remaining]:
                    best_prob[n_bytes_remaining] = this_prob                    
                    best_path[n_bytes_remaining] = [field] + next_path        
    # Return final solution
    assert sum([f.n_bytes for f in best_path[-1]]) == len(probabilities), best_path[-1]
    return best_prob[-1], best_path[-1]

def flatten_seq(seq, lengths_dict):
    res = []
    i=0
    while i < len(seq):
        res.append(seq[i])
        i += lengths_dict[seq[i]]
    return res    