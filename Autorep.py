import re

h_tone = "áéíóú"
l_tone = "àèìòù"
f_tone = "âêîôû"
r_tone = "ǎěǐôû"

class Autorep:   
    def __init__(self, word):
        self.word = word
        self.tone = ''
        self.mel = ''
        self.reduced_mel = ''
        self.assoc = []
 
        self.tone_labels = {'H': h_tone, 'L': l_tone, 'F': f_tone, 'R': r_tone}
        self.tone += ''.join(next((k for k, v in self.tone_labels.items() if seg in v), '') for seg in self.word)

        self.mel = self.tone 
        
        # if the tone sequence contains 'F', convert 'F' into 'HL'
        for i in range(len(self.tone)):
            contour_count = 0 
            self.assoc.append((i+1,i+1)) 
            if self.tone[i] == 'F':
                k,v = self.assoc[i]
                self.mel = self.mel.replace('F','HL')
                self.assoc.insert(2*i+1,(i+contour_count,i+1))
            elif self.tone[i] == 'R':
                k,v = self.assoc[i]
                self.mel = self.mel.replace('R','LH')
                self.assoc.insert(2*i+1,(i+contour_count,i+1))


        for i in range(1,len(self.mel)):
            j,k = self.assoc[i]
            p,q = self.assoc[i-1]
            if self.mel[i] == self.mel[i-1]:
                for j in range(i, len(self.assoc)):
                    self.assoc[j] = (self.assoc[i-1][0], self.assoc[j][1])
            else:
                j = p + 1
                self.assoc[i] = (j,k)
        
        self.reduced_mel = re.sub(r"(.)\1+", r"\1", self.mel)
           
        print (self.word, self.tone, self.reduced_mel, self.assoc) 

    def _tone_pos(self,check_tone):
            check_tone = check_tone.upper()
            if check_tone not in set(self.mel):
                return False
            else:   
                return [1+ i for i, j in enumerate(self.mel) if j == check_tone]      
    
    def spreading_count(self,check_tone):
        for i in self._tone_pos(check_tone):
            spreading = 0
            for j in self.assoc:
                if j[0] == i:
                    spreading += 1 
            print(check_tone,i,"spread length",spreading)
            
    def check_contain(self, ar):
        matching = False
        if len(ar.mel) <= len(self.mel) and ar.mel in self.mel:
            j,k = re.search(ar.mel, self.mel).span() # take out the first piece where two ARs match 
            shared_piece = self.assoc[j:k]
            updated_piece = []
            for (p,q) in shared_piece:
                p_2 = shared_piece[0][0] - 1 # p2 = 0
                q_2 = shared_piece[0][1] - 1 # q2 = 2
                updated_piece.append((p-p_2, q-q_2)) 
                if updated_piece == ar.assoc:
                    return(True)
        return(matching)
    

    def add_tone(self):
       self.reduced_mel = self.reduced_mel +  self.reduced_mel[-2]
       self.assoc.append((len(self.reduced_mel),None))
       return self.reduced_mel, self.assoc
    
    def add_syl(self):
        """
        Add a syllable in the AR by adding an assocation (j,k)
        where j is the 'none' indication the syllable is not associated
        k is the one-unit increase of current syllable number 
        """
        max_syllable = max([k for _, k in self.assoc if k is not None])
        self.assoc.append((None, max_syllable+1))
        return self.assoc
    
    def float_tone(self):
        self.float_tone_list = [i for i in reversed(self.assoc) if i[1] is None][::-1]
        return(self.float_tone_list)
    
    def float_syl(self):
        self.float_syl_list = [i for i in reversed(self.assoc) if i[0] is None][::-1]
        return(self.float_syl_list)   
    
    def float_tone_to_syl(self):
        """
        Associate the first floating tone to the last syllable
        e.g LH [(1,1), (2,None)] -> [(1,1), (2,1)]
        """
        float_tone_lists = self.float_tone()
        if float_tone_lists:
            position_in_assoc = self.assoc.index(float_tone_lists[0]) # If the AR contains multiple floating tones, only process 1st
            previous_assoc_index = position_in_assoc - 1
            self.assoc[position_in_assoc] = (self.assoc[position_in_assoc][0],self.assoc[previous_assoc_index][1])
            return self.assoc

    def float_syl_to_tone(self):
        float_syl_list = self.float_syl()
        if float_syl_list:
            position_in_assoc = self.assoc.index(float_syl_list[0])
            previous_assoc_index = position_in_assoc - 1
            self.assoc[position_in_assoc] = (self.assoc[previous_assoc_index][0],self.assoc[position_in_assoc][1])
            return self.assoc
    
    def flt_syl_flt_tone(self):
        float_tone = min(((j, k) for j, k in self.assoc if k is None), default=(float('inf'), None))
        float_syl = min(((j, k) for j, k in self.assoc if j is None), default=(None, float('inf')))
        new_assoc = (float_tone[0], float_syl[1])
        position_to_keep = min(self.assoc.index(float_tone),self.assoc.index(float_syl))
        position_to_remove = max(self.assoc.index(float_tone),self.assoc.index(float_syl))
        self.assoc[position_to_keep] = new_assoc
        self.assoc.remove(self.assoc[position_to_remove])
        return self.assoc


    
    def add_assoc(self):  # add one association line
        if self.float_tone() and not self.float_syl():
            return self.float_tone_to_syl()
        elif self.float_syl() and not self.float_tone():
            return self.float_syl_to_tone()
        else:
            ar1 = self
            ar3 = self
            option1 = ar1.float_tone_to_syl()
            #option2 = self.float_syl_to_tone()
            option3 = ar3.flt_syl_flt_tone()
            return option1,option3#, option3


                
    def show(self):
        print (self.word, self.tone, self.reduced_mel, self.assoc) 

    def __eq__(self, other):
        return self.mel == other.mel and self.assoc == other.assoc  
