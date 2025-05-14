import json
import os
import argparse
import subprocess

from scripts.poseidon_utils import poseidon_hash_inputs, P_BN254
from scripts.merkle_tree import MerkleTree
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(SCRIPT_DIR, 'build')
COMMITMENTS_FILE = os.path.join(BUILD_DIR, 'commitments.json')
TREE_JSON_FILE = os.path.join(BUILD_DIR, 'tree.json')
WASM_PATH = os.path.join(BUILD_DIR, 'shielded_tx_js', 'shielded_tx.wasm')
GEN_WITNESS_SCRIPT_PATH = os.path.join(BUILD_DIR, 'shielded_tx_js', 'generate_witness.js')
ZKEY_FINAL_PATH = os.path.join(BUILD_DIR, 'shielded_tx_final.zkey')
VERIFICATION_KEY_PATH = os.path.join(BUILD_DIR, 'shielded_tx_verification_key.json')
SESSION_ID = os.urandom(4).hex()
INPUT_JSON_PATH = os.path.join(BUILD_DIR, f'withdraw_input_{SESSION_ID}.json')
WITNESS_PATH = os.path.join(BUILD_DIR, f'withdraw_witness_{SESSION_ID}.wtns')
PROOF_PATH = os.path.join(BUILD_DIR, f'withdraw_proof_{SESSION_ID}.json')
PUBLIC_JSON_PATH = os.path.join(BUILD_DIR, f'withdraw_public_{SESSION_ID}.json')
CIRCUIT_MIN_VAL = 0
CIRCUIT_MAX_VAL = 10000

def load_commitments():
    if not os.path.exists(COMMITMENTS_FILE):
        print(f"ERROR: Commitments file not found at {COMMITMENTS_FILE}")
        return None
    with open(COMMITMENTS_FILE, 'r') as f:
        return json.load(f)

def withdraw(amount, blinding_hex, secret_hex, leaf_index):
    print(f"--- Performing Withdrawal for amount: {amount}, leafIndex: {leaf_index} ---")
    
    blinding_int = int(blinding_hex, 16)
    secret_int = int(secret_hex, 16)

    # Recalculate commitment to make sure it matches what should be in the tree
    expected_commitment_int = poseidon_hash_inputs([amount, blinding_int])
    expected_commitment_hex = format(expected_commitment_int, 'x').zfill(64)
    print(f"Re-calculated expected commitment (hex): {expected_commitment_hex}")

    # Load commitments and verify the provided leaf_index and commitment
    commitments_list = load_commitments()
    if commitments_list is None: return

    if leaf_index >= len(commitments_list) or commitments_list[leaf_index] != expected_commitment_hex:
        print("ERROR: Provided note details (amount, blinding, leaf_index) do not match a known commitment.")
        print(f"Expected commitment {expected_commitment_hex} at index {leaf_index}, found {commitments_list[leaf_index] if leaf_index < len(commitments_list) else 'None'}")
        return
    print("Note details match a known commitment.")

    # Load Merkle tree and get path elements and current root
    print("Loading Merkle tree to get proof path and root...")
    tree = MerkleTree(commitments_list)
    
    try:
        path_elements_hex = tree.get_merkle_proof_hex(leaf_index)
    except IndexError as e:
        print(f"ERROR: Could not get Merkle proof for leaf index {leaf_index}: {e}")
        return
    
    current_merkle_root_hex = tree.root
    print(f"Merkle Proof Path Elements (hex, first 3): {path_elements_hex[:3]}...")
    print(f"Current Merkle Root (hex): {current_merkle_root_hex}")

    # Prepare inputs for the ZK circuit
    inputs = {
        'amount': amount,
        'blinding': blinding_int,         
        'secret': secret_int,             
        'leafIndex': leaf_index,
        'pathElements': [int(x, 16) for x in path_elements_hex], 
        'merkleRoot': int(current_merkle_root_hex, 16),         
        'MIN': CIRCUIT_MIN_VAL,
        'MAX': CIRCUIT_MAX_VAL
    }
    with open(INPUT_JSON_PATH, 'w') as f:
        json.dump(inputs, f, indent=2)
    print(f"Circuit inputs saved to: {INPUT_JSON_PATH}")

    # Generate Witness and Proof using snarkjs
    try:
        print("Generating witness...")
        subprocess.run(['node', GEN_WITNESS_SCRIPT_PATH, WASM_PATH, INPUT_JSON_PATH, WITNESS_PATH], check=True, capture_output=True, text=True)
        print(f"Witness generated: {WITNESS_PATH}")

        print("Generating proof...")
        subprocess.run(['snarkjs', 'groth16', 'prove', ZKEY_FINAL_PATH, WITNESS_PATH, PROOF_PATH, PUBLIC_JSON_PATH], check=True, capture_output=True, text=True)
        print(f"Proof generated: {PROOF_PATH}")
        print(f"Public signals: {PUBLIC_JSON_PATH}")

        # Verify the proof locally (as the contract would)
        print("Verifying proof locally...")
        result = subprocess.run(['snarkjs', 'groth16', 'verify', VERIFICATION_KEY_PATH, PUBLIC_JSON_PATH, PROOF_PATH], capture_output=True, text=True)
        
        if "OK!" in result.stdout:
            print("Proof VERIFIED successfully locally! OK.")
            with open(PUBLIC_JSON_PATH, 'r') as f_pub:
                public_signals_str_array = json.load(f_pub)
            print(f"Raw public_signals array from {PUBLIC_JSON_PATH}: {public_signals_str_array}")
            print(f"Number of public signals: {len(public_signals_str_array)}")
            print("Decoded Public Signals from Proof:")
            labels = [
                "Merkle Root (Circuit Input)", 
                "MIN (Circuit Input)", 
                "MAX (Circuit Input)", 
                "Output Commitment (Circuit Output)", 
                "Output Nullifier (Circuit Output)"
            ]

            if len(public_signals_str_array) == 2:
                print("2 public signals found.")
                labels_to_use = [
                    "Output Commitment (from proof)", 
                    "Output Nullifier (from proof)"
                ]
                merkle_root_in_proof = inputs['merkleRoot']
                min_in_proof = inputs['MIN']
                max_in_proof = inputs['MAX']
                out_commitment_from_proof = int(public_signals_str_array[0])
                out_nullifier_from_proof = int(public_signals_str_array[1])
            elif len(public_signals_str_array) == 5:
                print("  INFO: 5 public signals found. Assuming standard order.")
                labels_to_use = labels
                merkle_root_in_proof = int(public_signals_str_array[0])
                min_in_proof = int(public_signals_str_array[1])
                max_in_proof = int(public_signals_str_array[2])
                out_commitment_from_proof = int(public_signals_str_array[3])
                out_nullifier_from_proof = int(public_signals_str_array[4])
            else:
                print("  WARNING: Unexpected number of public signals. Printing raw with indices.")
                labels_to_use = [f"Signal {i}" for i in range(len(public_signals_str_array))]

            for i, signal_str in enumerate(public_signals_str_array):
                label = labels_to_use[i] if i < len(labels_to_use) else f"Signal {i} (unexpected)"
                print(f"  {label}: {signal_str}") 

            displayed_merkle_root = hex(inputs['merkleRoot']).zfill(64)
            displayed_commitment = "N/A"
            displayed_nullifier = "N/A"

            if len(public_signals_str_array) == 2: # Assuming [outCommitment, outNullifier]
                displayed_commitment = format(int(public_signals_str_array[0]), 'x').zfill(64)
                displayed_nullifier = format(int(public_signals_str_array[1]), 'x').zfill(64)
            elif len(public_signals_str_array) == 5:
                displayed_commitment = format(int(public_signals_str_array[3]), 'x').zfill(64)
                displayed_nullifier = format(int(public_signals_str_array[4]), 'x').zfill(64)

            generated_proof_details = (
                f"Output Commitment (from proof signals): {displayed_commitment}\n"
                f"Output Nullifier (from proof signals): {displayed_nullifier}\n"
                f"Merkle Root Used (input to circuit): {displayed_merkle_root}\n"
                f"Proof and public signals are in build/ (suffixed with {SESSION_ID})."
            )
            print("--- Withdrawal Simulation Complete! ---")
        else:
            print("Proof verification FAILED locally.")
            print("snarkjs verify stdout:", result.stdout)
            print("snarkjs verify stderr:", result.stderr)

    except subprocess.CalledProcessError as e:
        print(f"Error during snarkjs execution: {e}")
        print("Command: ", " ".join(e.cmd))
        print("Stdout: ", e.stdout)
        print("Stderr: ", e.stderr)
    except FileNotFoundError as e:
        print(f"ERROR: A required file/tool was not found: {e}. Check paths and ensure snarkjs/node are installed.")
    finally:
        for f_path in [INPUT_JSON_PATH, WITNESS_PATH, PROOF_PATH, PUBLIC_JSON_PATH]:
            if os.path.exists(f_path):
                try:
                    os.remove(f_path)
                except OSError:
                    print(f"Warning: Could not remove temp file {f_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Withdraw a confidential note (CLI demo).")
    parser.add_argument("--amount", type=int, required=True, help="Amount of the note.")
    parser.add_argument("--blinding_hex", type=str, required=True, help="Blinding factor of the note (hex).")
    parser.add_argument("--secret_hex", type=str, required=True, help="Secret for the nullifier (hex).")
    parser.add_argument("--leaf_index", type=int, required=True, help="Leaf index of the commitment in the Merkle tree.")
    args = parser.parse_args()
    withdraw(args.amount, args.blinding_hex, args.secret_hex, args.leaf_index) 