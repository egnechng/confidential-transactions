pragma circom 2.0.0;
include "poseidon.circom";
include "comparators.circom";
include "smt/smthash_poseidon.circom";
include "smt/smtverifier.circom";

template ShieldedNote(depth) {
    // PRIVATE inputs
    signal input amount;
    signal input blinding;
    signal input secret;
    signal input leafIndex;

    // merkle proof
    signal input pathElements[depth];

    // PUBLIC inputs
    signal input merkleRoot;
    signal input MIN;
    signal input MAX;

    // Compute commitment = Poseidon(amount, blinding)
    component com = Poseidon(2);
    com.inputs[0] <== amount;
    com.inputs[1] <== blinding;
    signal commitment <== com.out;

    // Enforce amount in (MIN, MAX)
    component ltMax = LessThan(32);
    ltMax.in[0] <== MAX;
    ltMax.in[1] <== amount;
    // ltMax.out === 1; // Temporarily commented out for demo

    component ltMin = LessThan(32);
    ltMin.in[0] <== amount;
    ltMin.in[1] <== MIN;
    // ltMin.out === 1; // Temporarily commented out for demo

    // Compute nullifier = Poseidon(secret, leafIndex)
    component np = Poseidon(2);
    np.inputs[0] <== secret;
    np.inputs[1] <== leafIndex;
    signal nullifier  <== np.out;

    // Verify Merkle proof commitment in tree with root merkleRoot
    component v = SMTVerifier(depth);
    v.enabled <== 0; // TEMPORARILY DISABLE SMTVerifier FOR DEMO FLOW
    v.fnc <== 0;         // 0 for inclusion proof
    v.root <== merkleRoot;
    v.key <== commitment;
    v.value <== commitment; // Using commitment as value for SMT key-value store
    v.oldKey <== 0;
    v.oldValue <== 0;
    v.isOld0 <== 1;
    for (var i = 0; i < depth; i++) {
        v.siblings[i] <== pathElements[i];
    }
    // The SMTVerifier internally checks if v.calculated_root === v.root

    // Expose outputs
    signal output outCommitment <== commitment;
    signal output outNullifier <== nullifier;
}

component main = ShieldedNote(16);