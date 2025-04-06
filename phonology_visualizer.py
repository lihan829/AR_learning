import os
import graphviz

class PhonologyVisualizer:
    def __init__(self, word=None, ocp_mel=None, assoc=None, moralist=True):
        self.word = word
        self.ocp_mel = ocp_mel if ocp_mel else []
        self.assoc = assoc if assoc else []
        self.moralist = moralist
        print("PhonologyVisualizer initialized with:", self.word, self.ocp_mel, self.assoc, self.moralist)
    
    def draw(self, name=""):
        print("Starting draw method...")
        drawing = self.assoc[:]
        print("Initial drawing data:", drawing)

        for i, tup in enumerate(self.assoc, start=1):  # Assign sequential mora index
            if tup[1] is not None or tup[2] is not None:  # Check valid mora assignment
                drawing[i - 1] = (tup[0], i, tup[2])  # Create a new tuple with updated mora
                print(f"Updated drawing[{i - 1}] to {drawing[i - 1]}")

        # Define file path
        file_name = name if name else (self.word if self.word else self.ocp_mel)
        file_path = os.path.join("new_cons", file_name)
        print("Graph file path:", file_path)
        
        # Initialize Graphviz Digraph
        d = graphviz.Digraph(filename=file_path, format='png')
        d.attr(nodesep="0.01", ranksep="0.1")
        print("Graphviz Digraph initialized")

        # Melody nodes
        with d.subgraph() as s1:
            s1.attr(rank='source', rankdir='LR', nodesep="0.01")
            for i, t in enumerate(self.ocp_mel):
                s1.node(f'Mel_{i+1}', label=t, shape='plaintext')
                print(f"Added melody node: Mel_{i+1} with label {t}")
        
        if not self.moralist:
            print("Moralist is False. Returning early.")
            return s1
        
        # Mora and syllable associations
        for t, m, s in self.assoc:
            if m:
                syl_label = 'σ_l' if m == 1 else 'σ_h' if m == 2 else 'σ_sh'
                d.node(f'Syl_{s}', label=syl_label, shape='plaintext')
                print(f"Added syllable node: Syl_{s} with label {syl_label}")
            if t:
                d.edge(f'Mel_{t}', f'Syl_{s}', dir='none')
                print(f"Added edge from Mel_{t} to Syl_{s}")

        print("Graph construction completed for:", self.word, self.assoc)
        return d
