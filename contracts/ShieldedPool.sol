// Not used in the project, was messing around with it to see if it could work.
pragma solidity ^0.8.0;

import "./Verifier.sol";

contract ShieldedPool is Verifier {
    bytes32 public merkleRoot;
    mapping(bytes32 => bool) public spentNullifiers;

    event Deposit(bytes32 indexed commitment, uint leafIndex, bytes32 newRoot);
    event Withdraw(bytes32 indexed nullifier, address to, bytes32 merkleRootUsed);

    function updateRoot(bytes32 _newRoot) external {
        merkleRoot = _newRoot;
    }

    function deposit(bytes32 _commitment, uint _leafIndex, bytes32 _newRoot) external {
        emit Deposit(_commitment, _leafIndex, _newRoot);
        merkleRoot = _newRoot;
    }

    function withdraw(
        uint[2] calldata pi_a,
        uint[2][2] calldata pi_b,
        uint[2] calldata pi_c,
        bytes32 _merkleRootUsedInProof,
        uint[2] calldata proofPublicSignals
    ) external {
        bytes32 _proofOutNullifier = bytes32(proofPublicSignals[1]);

        require(!spentNullifiers[_proofOutNullifier], "Nullifier already spent");
        require(_merkleRootUsedInProof == merkleRoot, "Merkle root mismatch");
        
        bool proofVerified = verifyProof(pi_a, pi_b, pi_c, proofPublicSignals);
        require(proofVerified, "Invalid ZK proof");

        spentNullifiers[_proofOutNullifier] = true;
        
        emit Withdraw(_proofOutNullifier, msg.sender, _merkleRootUsedInProof);
    }
}
