import re
import pandas as pd

class Autorep:
    
    def __init__(self, word="", mel='', reduced_mel="", assoc=None):
        """
        Initialize an Autorep object.

        Parameters:
        - word (str): The word with tone markers. Default is an empty string.
        - tone (str): The tone markers directly extracted from the word(HFLR). Default is an empty string.
        - mel (str): The melody (F -> HL and R -> LH) before OCP. Default is an empty string.
        - reduced_mel (str): The OCP-applied tone representation of the word. Default is an empty string.
        - assoc (list): A list of tuples (j,k) indicating the association between tone (indexed by j) and syllable (indexed by k) list.
        """
        self.word = word
        self.tone = ''
        self.mel = ''
        self.reduced_mel = reduced_mel
        self.assoc = assoc if assoc is not None else []
        
        h_tone = "áéíóú"
        l_tone = "àèìòù"
        f_tone = "âêîôû"
        r_tone = "ǎěǐôû"
        
        if len(self.reduced_mel) != max([j for j, k in self.assoc if j is not None], default=0):
            raise ValueError("The length of the melody does not match the number of tone units.")
        
        if not reduced_mel: #if tone is specified convert to OCP melody
            self.tone_labels = {'H': h_tone, 'L': l_tone, 'F': f_tone, 'R': r_tone}
            self.tone += ''.join(next((k for k, v in self.tone_labels.items() if seg in v), '') for seg in self.word)
            self.mel = self.tone 

            # Convert 'F' and 'R' into 'HL' and 'LH' respectively
            for i in range(len(self.tone)):
                contour_count = 0 
                self.assoc.append((i + 1, i + 1)) 
                if self.tone[i] == 'F':
                    k, v = self.assoc[i]
                    self.mel = self.mel.replace('F', 'HL')
                    self.assoc.insert(2 * i + 1, (i + contour_count, i + 1))
                elif self.tone[i] == 'R':
                    k, v = self.assoc[i]
                    self.mel = self.mel.replace('R', 'LH')
                    self.assoc.insert(2 * i + 1, (i + contour_count, i + 1))

            # Adjust association indices
            for i in range(1, len(self.mel)):
                j, k = self.assoc[i]
                p, q = self.assoc[i - 1]
                if self.mel[i] == self.mel[i - 1]:
                    for j in range(i, len(self.assoc)):
                        self.assoc[j] = (self.assoc[i - 1][0], self.assoc[j][1])
                else:
                    j = p + 1
                    self.assoc[i] = (j, k)

            self.reduced_mel = re.sub(r"(.)\1+", r"\1", self.mel)

        print(self.word, self.reduced_mel, self.assoc) 
    
    def check_empty(self):
        return (self.word == "" and self.assoc == [] and self.mel == "" and self.reduced_mel == "")     


    def tone_pos(self, check_tone):
        """
        Get positions of a particular tone in the melody.
        """
        check_tone = check_tone.upper()
        if check_tone not in set(self.mel):
            return False
            
        else:
            return [1 + i for i, j in enumerate(self.mel) if j == check_tone]      
    
    @staticmethod
    def index_reset(lst):
            """
            Reset indices of the association list to start from 1.
            """
            j, k = lst[0] if lst else (None, None)
            distance_k = k - 1 if k is not None else None
            distance_j = j - 1 if j is not None else None
            new_list = []
            for (j, k) in lst:
                j = j - distance_j if j is not None else None 
                k = k - distance_k if k is not None else None 
                new_list.append((j, k))
            return new_list
        
        
    def check_contain(self, ar):
        """
        Check if the Autorep object contains another Autorep object.
        """ 
        if self.check_empty() or ar.check_empty():
            return False if not ar.check_empty() else True 
        if ar.reduced_mel not in self.reduced_mel:
            return False
        else:
            check_position = [m.start() + 1 for m in re.finditer(r'(?={})'.format(ar.reduced_mel), self.reduced_mel)]
            check_span = len(ar.assoc)
            for i in check_position:
                selected_indices = [index for index, tup in enumerate(self.assoc) if tup[0] == i]
                for j in selected_indices:
                    matching = []
                    if len(self.assoc[j:j+check_span]) < check_span:
                        return False
                    elif self.index_reset(self.assoc[j:j+check_span]) == ar.assoc:
                        return True  # Match found, return True
                    else:
                        for (j1, k1), (j2, k2) in zip(self.index_reset(self.assoc[j:j+check_span]), ar.assoc):
                            if (j2 is None or j1 == j2) and (k2 is None or k1 == k2):
                                matching.append(True)
                            else:
                                matching.append(False)
                        if all(matching):
                            return True  # Match found, return True
        return False  # No match found, return False
    

    def add_tone(self):
        """
        Add an unassociated tone in the AR by adding a tone to the melody and an association (j,k)
        j is one-unit increase of the tone numbers
        k is 'None' indicating the syllable is not associated with any tone unit
        """
        new_assoc = self.assoc.copy() 
        
        if self.reduced_mel == '':
            new_assoc.append((1, None))
            new_autorep = [
                Autorep(reduced_mel='H', assoc=new_assoc),
                Autorep(reduced_mel='L', assoc=new_assoc)
            ]
        else:
            if len(self.reduced_mel) == 1:
                new_reduced_mel = "HL" if self.reduced_mel == "H" else "LH"
            else:
                new_reduced_mel = self.reduced_mel + self.reduced_mel[-2] 
            new_assoc.append((len(new_reduced_mel), None))
            new_autorep = [Autorep(reduced_mel=new_reduced_mel, assoc=new_assoc)]
        
        return new_autorep


    def add_syl(self):
        """
        Add an unassociated syllable in the AR by adding an assocation (j,k)
        j is 'None' indicating the syllable is not associated w any tone unit
        k is the one-unit increase of current syllable number (the variable max_syllable)
        """
        current_syl = [k for j,k in self.assoc if k is not None]
    
        if current_syl:
            max_syllable_index = max(current_syl)
            new_assoc = self.assoc.copy()  # Create a copy to avoid modifying the original assoc list
            new_max_syllable_index = max_syllable_index +1
            new_assoc.append((None, new_max_syllable_index))
            new_autorep = [Autorep(mel = self.mel, reduced_mel = self.reduced_mel, assoc=new_assoc)]
        else:
            new_autorep = [Autorep(mel = self.mel, reduced_mel = self.reduced_mel, assoc=self.assoc + [(None, 1)])]
        
        return new_autorep
    

    def float_tone(self):
        if len(self.assoc) > 1:
            return ([(_,k) for (_,k) in reversed(self.assoc) if k is None][::-1])
        else:
            return ([(_,k) for (_,k) in self.assoc if k is None])
    

    def float_syl(self):
        return [(j,_) for (j,_) in reversed(self.assoc) if j is None][::-1]

    
    def check_float(self):
        return any([self.float_tone(),self.float_syl()])


    def float_tone_to_syl(self):
        """
        Associate the first floating tone to the last syllable
        e.g LH [(1,1), (2,None)] -> [(1,1), (2,1)]
        """
        if self.float_tone():
            doubly_linked_pair = [(j,k) for (j,k)in self.assoc if j is not None and k is not None]
            if doubly_linked_pair:
                last_valid_tuple = max(doubly_linked_pair)
                t,s = last_valid_tuple
                first_float_tone = min(((j,k) for (j,k)in self.assoc if k is None), default=(float('inf'), None))
                k,_ = first_float_tone
                first_float_tone_index = self.assoc.index(first_float_tone)
                new_assoc = self.assoc[:]
                new_assoc[first_float_tone_index] = (k,s)
                return new_assoc
        
    
    def float_syl_to_tone(self):
        if self.float_syl():
            doubly_linked_pair = [(j,k) for (j,k)in self.assoc if j is not None and k is not None]
            if doubly_linked_pair:
                last_doubly_linked_pair = max(doubly_linked_pair)
                t,s = last_doubly_linked_pair
                first_float_syl = min(((j,k) for (j,k)in self.assoc if j is None), default=(float('inf'), None))
                _,k = first_float_syl
                first_float_syl_index = self.assoc.index(first_float_syl)
                new_assoc = self.assoc[:]
                new_assoc[first_float_syl_index] = (t,k)
                return new_assoc


    def flt_syl_flt_tone(self):
        if self.float_syl and self.float_tone:  # Removed unnecessary bool() and == True
            # Renamed variables to avoid naming conflict
            min_float_tone = min(((j, k) for j, k in self.assoc if k is None), default=None)
            min_float_syl = min(((j, k) for j, k in self.assoc if j is None), default=None)

            if min_float_tone and min_float_syl:  # Check if both are not None
                new_assocline = (min_float_tone[0], min_float_syl[1])
                position_to_keep = min(self.assoc.index(min_float_tone), self.assoc.index(min_float_syl))
                position_to_remove = max(self.assoc.index(min_float_tone), self.assoc.index(min_float_syl))
                new_assoc = self.assoc[:]
                new_assoc[position_to_keep] = new_assocline
                del new_assoc[position_to_remove]  # Use del to remove an item from a list
                return new_assoc
       

    def add_assoc(self):
        if self.check_float and len(self.assoc) > 1:  
            new_ar = []
            new_assoc1 = self.flt_syl_flt_tone()
            new_assoc2 = self.float_syl_to_tone()
            new_assoc3 = self.float_tone_to_syl()   
            
            if new_assoc1 is not None:
                new_ar.append(Autorep(mel=self.mel, reduced_mel=self.reduced_mel, assoc=new_assoc1))

            if new_assoc2 is not None:
                new_ar.append(Autorep(mel=self.mel, reduced_mel=self.reduced_mel, assoc=new_assoc2))

            if new_assoc3 is not None:
                new_ar.append(Autorep(mel=self.mel, reduced_mel=self.reduced_mel, assoc=new_assoc3))
            return new_ar
        
    


    def next_ar(self):
        if not self.assoc:
            next_ar= [Autorep(reduced_mel= "H",mel='H', assoc= [(1,None)]),
                            Autorep(reduced_mel= "L",mel='L', assoc= [(1,None)]),
                            Autorep(reduced_mel= "", assoc= [(None,1)])]
        else:
            next_ar = []
            tone_list = self.add_tone()
            syl_list = self.add_syl()
            assoc_list = self.add_assoc()

            if tone_list is not None:
                next_ar += tone_list

            if syl_list is not None:
                next_ar += syl_list

            if assoc_list is not None:
                next_ar += assoc_list
        return next_ar    
    
    
    def k_factor(self):
        tone_num = len(self.reduced_mel)
        syl_num = max([k for j, k in self.assoc if k is not None], default=0)
        return tone_num + syl_num     


    def info(self):
        return Autorep(reduced_mel = self.reduced_mel, assoc = self.assoc)
    
    
    def show(self):
        return(self.reduced_mel,self.assoc) 


    def __eq__(self, other):
        return self.reduced_mel == other.reduced_mel and self.assoc == other.assoc  
    
    
    def __str__(self):
        return f"{self.reduced_mel}, {self.assoc}"
  