import json
import os
from scripts.poseidon_utils import poseidon_hash_hex_strings, P_BN254

class MerkleTree:
    def __init__(self, leaves_hex):
        self.depth = 16 
        
        self.zero_leaf_hex = format(0, 'x').zfill(64)

        pad_leaf_hex = self.zero_leaf_hex

        real_leaves_hex = leaves_hex.copy()
        total_leaves_required = 2 ** self.depth
        if len(real_leaves_hex) > total_leaves_required:
            raise ValueError(f"Number of leaves ({len(real_leaves_hex)}) exceeds tree capacity for depth {self.depth}.")
        
        real_leaves_hex += [pad_leaf_hex] * (total_leaves_required - len(real_leaves_hex))

        self.layers = [real_leaves_hex]
        current_layer_hex = real_leaves_hex

        for _ in range(self.depth):
            next_layer_hex = []
            if len(current_layer_hex) % 2 != 0:
                current_layer_hex.append(pad_leaf_hex) 
            
            for i in range(0, len(current_layer_hex), 2):
                left_hex = current_layer_hex[i]
                right_hex = current_layer_hex[i+1]
                parent_hash_hex = poseidon_hash_hex_strings([left_hex, right_hex])
                next_layer_hex.append(parent_hash_hex)
            
            self.layers.append(next_layer_hex)
            current_layer_hex = next_layer_hex
            if len(current_layer_hex) == 1:
                break # Root reached

    @property
    def root(self):
        if not self.layers or not self.layers[-1]:
            return None
        return self.layers[-1][0]

    def get_merkle_proof_hex(self, leaf_index):
        if leaf_index < 0 or leaf_index >= len(self.layers[0]):
            raise IndexError("Leaf index out of bounds.")

        path_elements_hex = []
        current_index = leaf_index

        for d in range(self.depth):
            layer = self.layers[d]
            sibling_index = current_index ^ 1
            if sibling_index < len(layer):
                path_elements_hex.append(layer[sibling_index])
            else:
                path_elements_hex.append(self.zero_leaf_hex) 
            current_index //= 2
        
        return path_elements_hex

def save_tree(tree, path="build/tree.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump({
            "layers": tree.layers,
            "root": tree.root,
            "depth": tree.depth
        }, f, indent=2)

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.join(base_dir, '..')
    build_dir = os.path.join(project_root, 'build')
    commitments_file = os.path.join(build_dir, 'commitments.json')

    if not os.path.exists(commitments_file):
        print(f"Commitments file not found: {commitments_file}. Initializing with an empty list.")
        os.makedirs(build_dir, exist_ok=True)
        with open(commitments_file, 'w') as f:
            json.dump([], f)
        leaves_hex = []
    else:
        with open(commitments_file, 'r') as f:
            leaves_hex = json.load(f)
    
    print(f"Loaded {len(leaves_hex)} commitments.")
    
    tree = MerkleTree(leaves_hex)
    save_tree(tree, os.path.join(build_dir, 'tree.json'))
    if tree.root:
        print(f"New Merkle root (Poseidon based): {tree.root}")
    else:
        print("Merkle tree is empty or could not be constructed.")
