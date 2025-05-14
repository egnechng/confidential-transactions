import json
import os
import argparse

from scripts.poseidon_utils import poseidon_hash_inputs, P_BN254
from scripts.merkle_tree import MerkleTree, save_tree
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(SCRIPT_DIR, 'build')
COMMITMENTS_FILE = os.path.join(BUILD_DIR, 'commitments.json')
TREE_JSON_FILE = os.path.join(BUILD_DIR, 'tree.json')
CIRCUIT_MIN_VAL = 0 
CIRCUIT_MAX_VAL  = 10000

def load_commitments():
    if not os.path.exists(COMMITMENTS_FILE):
        return []
    with open(COMMITMENTS_FILE, 'r') as f:
        return json.load(f)

def save_commitments(commitments_list):
    os.makedirs(BUILD_DIR, exist_ok=True)
    with open(COMMITMENTS_FILE, 'w') as f:
        json.dump(commitments_list, f, indent=2)

def deposit(amount):
    print(f"--- Performing Deposit for amount: {amount} ---")
    if not (CIRCUIT_MIN_VAL <= amount <= CIRCUIT_MAX_VAL):
        print(f"ERROR: Amount must be between {CIRCUIT_MIN_VAL} and {CIRCUIT_MAX_VAL}.")
        return

    # Generate blinding and secret (as integers for Poseidon)
    blinding_int = int.from_bytes(os.urandom(16), 'big') % P_BN254
    secret_int = int.from_bytes(os.urandom(16), 'big') % P_BN254
    print(f"Generated Blinding (int): {blinding_int}")
    print(f"Generated Blinding (hex): {format(blinding_int, 'x')}")
    print(f"Generated Secret (int): {secret_int}")
    print(f"Generated Secret (hex): {format(secret_int, 'x')}")

    # Calculate Poseidon commitment (using mock hash from poseidon_utils)
    commitment_int = poseidon_hash_inputs([amount, blinding_int])
    commitment_hex = format(commitment_int, 'x').zfill(64)
    print(f"Calculated Commitment (hex): {commitment_hex}")

    # Add commitment to list and get leaf index
    commitments_list = load_commitments()
    if commitment_hex in commitments_list:
        print("Warning: This exact commitment already exists. For demo, proceeding.")
    
    commitments_list.append(commitment_hex)
    leaf_index = len(commitments_list) - 1
    save_commitments(commitments_list)
    print(f"Commitment added. Leaf Index: {leaf_index}")

    # Rebuild Merkle tree and get new root
    print("Rebuilding Merkle tree...")
    tree = MerkleTree(commitments_list)
    save_tree(tree, TREE_JSON_FILE)
    merkle_root_hex = tree.root
    print(f"New Merkle Root (hex): {merkle_root_hex}")

    print("--- Deposit Complete! --- ")
    print("IMPORTANT: Save these details for withdrawal:")
    print(f"  Amount: {amount}")
    print(f"  Blinding (hex): {format(blinding_int, 'x')}")
    print(f"  Secret (hex): {format(secret_int, 'x')}")
    print(f"  Leaf Index: {leaf_index}")
    print(f"  Commitment (hex): {commitment_hex}")
    print("---------------------------")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deposit a confidential note (CLI demo).")
    parser.add_argument("--amount", type=int, required=True, help="The amount to deposit.")
    args = parser.parse_args()
    deposit(args.amount) 