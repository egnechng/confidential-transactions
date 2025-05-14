# CSCI-GA 3033 (Cryptography of Blockchains) Final Project : Confidential Transactions with ZK-SNARKs - A Proof of Concept
> Why do we even need confidential transactions? Most of us are familiar with blockchains like Ethereum or Bitcoin, where transparency is a key feature. Every transaction – who sent what to whom – is publicly visible on the ledger. While this is great for auditability, it poses significant privacy challenges for both individuals and businesses who might not want their financial activities exposed. This project demonstrates a simplified confidential transaction system using Zero-Knowledge SNARKs (Groth16) with Circom and snarkjs. It allows users to "deposit" and "withdraw" values while keeping the transaction amounts private, using a command-line interface for the demo.

## Core Concepts
- Zero-Knowledge Proofs (ZK-SNARKs): Allows proving knowledge of some information without revealing the information itself. We use Groth16, a specific type of ZK-SNARK.
- Commitments: Users commit to a note (amount + secret blinding factor) using a SNARK-friendly hash function (Poseidon). `Commitment = Poseidon(amount, blinding)`. This hides the details but binds the user to them.
- Nullifiers: To prevent double-spending, a unique nullifier is derived from note secrets: `Nullifier = Poseidon(secret, leafIndex)`. This is revealed upon spending.
- Merkle Tree: Commitments are stored in a Merkle tree. The Merkle root is a compact representation of all commitments. Proof of membership in the tree is required for withdrawal

## Project Structure
```text
.
├── build/                  # Compiled circuit, keys, proofs, tree state
├── circuits/
│   └── shielded_tx.circom  # The ZK-SNARK circuit definition
├── contracts/              # Solidity smart contracts (conceptual)
│   └── ShieldedPool.sol
├── node_modules/           # Circomlib and other Node dependencies
├── scripts/
│   ├── merkle_tree.py      # Merkle tree construction logic
│   └── poseidon_utils.py   # (Mock) Poseidon hash utility
├── deposit_cli.py          # CLI script for depositing notes
├── withdraw_cli.py         # CLI script for withdrawing notes & generating proofs
├── README.md               # This file
└── ...                     # Other project files (package.json, etc.)
```

## Code Components Explained

### 1. `circuits/shielded_tx.circom` - The ZK-SNARK Circuit Logic

*   **Purpose:** This file defines the core rules and mathematical constraints for a valid confidential transaction using the Circom language.
*   **Main Logic Summary:**
    1.  **Inputs:** Takes private user data (like `amount`, `blinding` factor for the commitment, a `secret` for the nullifier, `leafIndex`, and `pathElements` for Merkle proof) and public data (like the current `merkleRoot`, and `MIN`/`MAX` amount values).
    2.  **Commitment Calculation:** Internally computes a cryptographic commitment to the user's note (`Poseidon(amount, blinding)`) using `circomlib`'s secure Poseidon hash. This commitment is an output of the circuit.
    3.  **Nullifier Calculation:** Internally computes a unique nullifier (`Poseidon(secret, leafIndex)`) using `circomlib`'s secure Poseidon hash. This is also an output and is used to prevent double-spending.
    4.  **Constraint Checks (Partially Bypassed for Demo):**
        *   It's designed to include an Amount Range Proof (checking `MIN < amount < MAX`) and a Merkle Proof Verification (using an `SMTVerifier` component to ensure the user's commitment is in the provided `merkleRoot` via the `pathElements`).
        *   **Disclosure for Demo:** To ensure a stable demonstration flow and to work around complexities with off-chain hash consistency (due to the mock Poseidon hash used in Python scripts), these two specific constraint checks (range proof and SMTVerifier's Merkle proof check) are currently bypassed within this circuit file (e.g., by commenting out assertions or setting component `enabled` flags to false).
*   **Overall:** The circuit's goal is to allow a user to prove they possess a valid note that can be spent, without revealing the note's sensitive details, by satisfying all encoded rules.

### 2. `scripts/poseidon_utils.py` - Off-Chain Poseidon Hashing (Mock Implementation)

*   **Purpose:** This Python script is intended to provide Poseidon hashing capabilities for the off-chain parts of the system, specifically for the `deposit_cli.py` and `scripts/merkle_tree.py` scripts.
*   **Key Functionality:**
    *   `poseidon_hash_inputs(inputs_arr)`: This function is responsible for taking input values (like `amount` and `blinding`, or two child Merkle nodes) and producing a Poseidon hash.
*   **Disclosure - Mock Implementation:**
    *   The current version of `poseidon_hash_inputs` in this file **does not implement the true cryptographic Poseidon algorithm.** Instead, it uses a simplified arithmetic placeholder (e.g., `(val1^2 + val2^2 + val1*val2 + C1 + C2*val2) % P_BN254`).
    *   **Reason for Mocking:** Implementing a Python Poseidon hash that is bit-for-bit compatible with `circomlib`'s specific parameters (field, constants, rounds, etc.) was a super hard task for me and was skipped to focus on the end-to-end ZK-SNARK workflow for this proof-of-concept.
        *   Commitments generated by `deposit_cli.py` are "mock" commitments.
        *   The Merkle tree built by `scripts/merkle_tree.py` (including its root and path elements) is based on these "mock" hashes.
        *   This is why the `SMTVerifier` check inside `circuits/shielded_tx.circom` had to be bypassed for the demo – the mock Merkle proof from Python would not pass verification against the circuit's real Poseidon calculations.

### 3. `scripts/merkle_tree.py` - Off-Chain Merkle Tree Management

*   **Purpose:** This Python script defines a `MerkleTree` class to construct and manage the Merkle tree of commitments off-chain.
*   **Main Logic Summary (`MerkleTree` class):**
    1.  **Initialization:** Takes a list of currently known commitment hex strings (which are generated by `deposit_cli.py` using the mock Poseidon hash from `poseidon_utils.py`).
    2.  **Tree Construction:** Builds a binary Merkle tree of a fixed depth. It pads the list of commitments with a default "zero" leaf to ensure a full tree. It then iteratively calculates parent nodes by hashing pairs of child nodes together.
        *   **Hashing Used:** It calls `poseidon_hash_hex_strings` (which in turn uses the mock `poseidon_hash_inputs` from `scripts/poseidon_utils.py`) for all hashing operations within the tree.
    3.  **Root Calculation:** The final single hash at the top of the tree is the Merkle root.
    4.  **Proof Generation (`get_merkle_proof_hex`):** Given the index of a specific commitment (leaf), this method provides the necessary sibling hashes (`pathElements`) that form the Merkle proof for that leaf. These `pathElements`, along with the leaf itself and the Merkle root, would be used by the ZK circuit to verify membership.
*   **Disclosure regarding Mock Hashing:** Since this script uses `poseidon_utils.py`, the entire Merkle tree it constructs (all intermediate nodes, the root, and the generated path elements) is based on the mock Posiedon Hash.

# Running the Demo

## Installing prerequisites

### Rust and Cargo (for Circom compiler)
The Circom compiler is written in Rust, so you need to install Rust and its package manager Cargo. 
```bash
curl --proto '=https' --tlsv1.2 https://sh.rustup.rs -sSf | sh
```
Configure the current shell:
```bash
source $HOME/.cargo/env
```

### Circom Compiler
1. Clone the Circom repo:
```bash
git clone https://github.com/iden3/circom.git ~/circom-rust
```
2. Build and install Circom:
```bash 
cd ~/circom-rust
cargo build --release
cargo install --path circom # puts `circom` in ~/.cargo/bin
```
3. Verify Circom installation:
```bash
circom --version # should print something like "circom compiler 2.2.2"
```

### Node.js & npm
`snarkjs` (for ZK-SNARK operations) and `circomlib` (for standard Circom circuits) are Node.js packages
- Install Node.js & npm (for snarkjs & circomlib): Use OS package manager or download from [nodejs.org](https://nodejs.org/en)
- Verfiy Installation:
```bash
node -v
npm -v
```

### Python
Install Python 3.8+ & pip since the CLI scripts are written in python
- Verify installation
```bash
python3 --version
pip3 --version
```

## Install dependencies

### Node.js packages
`snarkjs`: A JavaScript library to perform ZK-SNARK operations like trusted setup, proof generation, and verification. We install it globally to make the snarkjs command available.
```bash
npm install -g snarkjs
```
`node_modules/circomlib`: A library of common Circom circuits and templates (like Poseidon, comparators, Merkle trees). 
```bash
npm install circomlib
```

## Build the Circuit & Generating Keys

### Compile the Circuit
Use the Circom compiler to convert `shielded_tx.circom` file into its arithmetic representation (`.r1cs`), a WebAssembly version for witness generation (`.wasm`) and a symbols file (`.sym`).

1. Clean up previous build (operational)
```bash
rm -rf build/ # clean up
mkdir -p build
```
2. Compile `shielded_tx.circom`:
```bash
circom -l node_modules/circomlib/circuits circuits/shielded_tx.circom --r1cs --wasm --sym -o build
```

### Trusted Setup: Powers of Tau (Phase 1)
This is the universal setup phase needed for any Groth16 circuit. We are using a power of 15.

1. Phase 1 Powers-of-Tau ceremony (universal SRS)
```bash
snarkjs powersoftau new bn128 15 build/pot15_0000.ptau -v
```
2. Contribute to the ceremony:
```bash
snarkjs powersoftau contribute build/pot15_0000.ptau build/pot15_0001.ptau --name="First contribution" -v
```
3. Prepare Phase 2:
This finalizes the `.ptau` file, making it ready for circuit-specific setups
```bash
snarkjs powersoftau prepare phase2 build/pot15_0001.ptau build/pot15_final.ptau -v
```

### Circuit-Specific Setup & Key Generation (Phase 2 - Groth16)
This phase uses the `.ptau` file from Phase 1 and the circuit's `.r1cs` file to generate the proving key (`.zkey`) and verification key.

1. Groth16 Setup (create initial proving key):
This links the specific circuit (`shielded_tx.r1cs`) with the universal powers of tau to create an initial, "toxic" proving key
```bash
snarkjs groth16 setup build/shielded_tx.r1cs build/pot15_final.ptau build/shielded_tx_0000.zkey
```

2. Contribute to the Circuit-Specific ZKey (Remove the "toxic" waste):
This step is important for security. It involves adding more randomness to make the proving key safe to use. 
```bash
snarkjs zkey contribute build/shielded_tx_0000.zkey build/shielded_tx_final.zkey --name="shielded contrib" -v
```
This produces `build/shielded_tx_final.zkey` which is your final proving key.

3. Export the Verification Key:
Extract the verification key into a JSON format, which can be used by `snarkjs` for local verification and to generate a Solidity verifier.
```bash
snarkjs zkey export verificationkey build/shielded_tx_final.zkey build/shielded_tx_verification_key.json
```

### Summary of Key Files Generated in `build/`
After completing these steps, your `build` directory should contain:
- `shielded_tx.r1cs` (Constraint system)
- `shielded_tx_js/shielded_tx.wasm` (Witness calculator)
- `shielded_tx_js/generate_wintess.js` (Helper for witness calculation)
- `pot15_final.ptau` (Powers of Tau file used)
- `shielded_tx_final.zkey` (Proving key)
- `shielded_tx_verificaiton_key.json` (Verification Key)
We should now be ready to generate proofs for this circuit.

## Demo Flow: Depositing and Withdrawing a Note (CLI)

This demonstration uses command-line scripts to simulate a confidential deposit and withdrawal.

**1. Initialize/Clear Previous State:**
Before starting, ensure a clean state for commitments:
```bash
echo "[]" > build/commitments.json
rm -f build/tree.json # Remove old tree if it exists
```

**2. Make a Deposit:**
Run the deposit script, providing an amount. This script will:
*   Generate a private blinding factor and a secret.
*   Compute a Poseidon commitment to the amount and blinding.
*   Add the commitment to `build/commitments.json`.
*   Rebuild the Merkle tree and output the new Merkle root.
*   **It will print the `amount`, `blinding_hex`, `secret_hex`, and `leaf_index`. You MUST save these details to use for withdrawal.**

    Example:
    ```bash
    python deposit_cli.py --amount 100
    ```
**3. (Optional) Make a Second Deposit:**
To see the Merkle tree handle multiple items:
```bash
python deposit_cli.py --amount 50
```

**4. Perform a Withdrawal:**
Run the withdrawal script using the details saved from a previous deposit. This script will:
*   Reconstruct the commitment.
*   Fetch the Merkle proof (path elements) and current Merkle root.
*   Prepare inputs for the ZK circuit.
*   Use `snarkjs` to generate a witness and a ZK proof.
*   Use `snarkjs` to verify the proof locally using `shielded_tx_verification_key.json`.
*   Output the result of the verification and the public signals from the proof (which include the output commitment and nullifier).

    Example (using details from the deposit of 100):
    ```bash
    python withdraw_cli.py --amount 100 --blinding_hex <SAVED_BLINDING_HEX> --secret_hex <SAVED_SECRET_HEX> --leaf_index <SAVED_LEAF_INDEX>
    ```
    Look for the "Proof VERIFIED successfully locally! OK." message.

This flow demonstrates the core mechanics: creating a commitment, proving its existence in the Merkle tree (though the circuit's internal check is bypassed for this demo version), and generating a nullifier to conceptually prevent double-spending, all while the ZK proof attests to the validity of these operations without revealing private inputs.

# Future Work and Limitations
1. Secure Poseidon Hash Implementation in Python:
The current Python scripts (`deposit_cli.py, withdraw_cli.py, scripts/merkle_tree.py`) utilize a placeholder/mock hash function for Poseidon operations. For a secure system, a Python implementation of the Poseidon hash algorithm is required that is precisely compatible with the parameters (BN254 scalar field, t-width, S-Box, round constants, MDS matrix, number of rounds) used by the `Poseidon` component in `circomlib` and compiled into the ZK-SNARK circuit. This is critical for ensuring that commitments, nullifiers, and Merkle tree hashes generated off-chain match the cryptographic assumptions and calculations within the on-chain verifier and the circuit itself.

2. Full On-Chain Smart Contract Integration (ShieldedPool.sol):
The ShieldedPool.sol smart contract, designed to manage the Merkle root, track spent nullifiers, and verify ZK proofs on-chain, was outlined. The next step involves deploying this contract to a blockchain testnet. The `withdraw_cli.py` script would then need to be extended using a library like `web3.py` to:
    - Connect to the deployed smart contract.
    - Format the generated ZK proof and the specific public signals as expected by the contract's `withdraw` function.
    - Submit the withdrawal transaction to the smart contract and handle the response
This would complete the end-to-end flow, with the smart contract serving as the trust anchor of transaction validity.

3. Reinstatement and Debugging of Circuit Constraints:
For the purposes of the demo and due to encountering potential component-specific issues, the amount range proof (`MIN < amount < MAX`) and the Merkle proof verification within the `SMTVerifier` component were temporarily bypassed in the `shielded_tx.circom` circuit. Future work would involve an investigation into the assertion failures ancountered with these components when using standard parameters (eg. `MAX = 2**32-1`). This may require deeper analysis of the `circomlib LessThan` and `SMTVerifier` components or exploring different Circom compilerversions. Once these constraints are re-enabled, we can make sure there is full transaction validity as defined by the circuit.

4. Advanced Transaction Structures (Join-Splits):
Beyond simple deposit and withdrawal of individual notes, a more advanced system could implement "join-split" style transactions. This would allow users to combine the value from multiple input notes (e.g. notes of 3 and 5) to create one or more new output notes (e.g., a new note of 8, or notes of 7 and 1 if change is required), or split a single larger note into multiple smaller ones. This requires a more complex circuit design to handle multiple input commitments/nullifiers and multiple output commitments, along with balancing equations, but significantly improves transaction flexibility and privacy by obscuring the flow of funds even further.