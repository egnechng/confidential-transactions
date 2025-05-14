# Field prime for BN254 scalar field
P_BN254 = 21888242871839275222246405745257275088548364400416034343698204186575808495617

def bn254_add(a, b):
    return (a + b) % P_BN254

def bn254_mul(a, b):
    return (a * b) % P_BN254

def bn254_pow(base, exp):
    return pow(base, exp, P_BN254)

def poseidon_hash_inputs(inputs_arr):
    """
    Placeholder for a circomlib-compatible Poseidon hash function.
    This function should take an array of 2 integer inputs (field elements)
    and return a single integer output (the hash result as a field element).
    """
    if len(inputs_arr) != 2:
        raise ValueError("Poseidon hash function expects 2 inputs for this application.")

    # This is NOT a real Poseidon hash, using very basic arithmetic combination as a stand-in.
    val1 = int(inputs_arr[0])
    val2 = int(inputs_arr[1])

    # A simple combination for placeholder purposes: (val1^2 + val2^2 + val1*val2 + some_constant) % P
    ph_c1 = 12345678901234567890
    ph_c2 = 98765432109876543210
    
    term1 = bn254_mul(val1, val1) # val1^2
    term2 = bn254_mul(val2, val2) # val2^2
    term3 = bn254_mul(val1, val2) # val1*val2
    
    res = bn254_add(term1, term2)
    res = bn254_add(res, term3)
    res = bn254_add(res, ph_c1) # Add some constant
    res = bn254_add(res, bn254_mul(val2, ph_c2)) # Another term for order variation placeholder
    return res

def poseidon_hash_hex_strings(hex_strings_arr):
    if len(hex_strings_arr) != 2:
        raise ValueError("Poseidon hash (hex) function expects 2 hex string inputs.")
    
    int_inputs = [int(s, 16) for s in hex_strings_arr]
    hash_int = poseidon_hash_inputs(int_inputs)
    return format(hash_int, 'x').zfill(64)

if __name__ == '__main__':
    # Example Usage
    input1_int = 123
    input2_int = 456
    hash_res_int = poseidon_hash_inputs([input1_int, input2_int])
    print(f"Poseidon hash of [{input1_int}, {input2_int}] is: {hash_res_int} (int)")
    print(f"Hex: {format(hash_res_int, 'x').zfill(64)}")

    input1_hex = "1a2b3c"
    input2_hex = "d4e5f6"
    val1 = int(input1_hex, 16)
    val2 = int(input2_hex, 16)
    hash_res_int_from_hex = poseidon_hash_inputs([val1, val2])
    print(f"Poseidon hash of (int values of [{input1_hex}, {input2_hex}]) is: {hash_res_int_from_hex} (int)")
    print(f"Hex: {format(hash_res_int_from_hex, 'x').zfill(64)}")

    hash_res_hex_direct = poseidon_hash_hex_strings([input1_hex.zfill(64), input2_hex.zfill(64)])
    print(f"Poseidon hash of [{input1_hex.zfill(64)}, {input2_hex.zfill(64)}] using hex wrapper is: {hash_res_hex_direct} (hex)")

    amount = 100
    blinding = int("abc123def456", 16)
    commitment_hash_int = poseidon_hash_inputs([amount, blinding])
    commitment_hash_hex = format(commitment_hash_int, 'x').zfill(64)
    print(f"Calculated commitment for amount={amount}, blinding={hex(blinding)} is: {commitment_hash_hex}") 