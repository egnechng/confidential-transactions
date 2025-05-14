// ignore this, it was for learning and testing
pragma circom 2.0.0;
include "../node_modules/circomlib/circuits/comparators.circom";

template TxCheck(nBits) {
    // PRIVATE input:
    signal input amount;
    // PUBLIC inputs:
    signal input threshold;
    // PUBLIC output: 1 if amount > threshold, else 0
    component lt = LessThan(nBits);
    lt.in[0] <== threshold; 
    lt.in[1] <== amount;
    signal output ok;
    ok <== lt.out;
}

component main = TxCheck(32);