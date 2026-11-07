import math
import os
import secrets

from Crypto.Util.number import getStrongPrime


E_A = 3 * 65537
E_B = 3 * 65539
FLAG = os.environ.get("FLAG", "katagaitai-CTF{dummy_flag}")
MENU = """
1. 暗号化装置Aから暗号文を取得する
2. 暗号化装置Bから暗号文を取得する
3. 機密情報を送信する
4. 終了する
"""


def generate_instance():
    while True:
        p = getStrongPrime(1024)
        q = getStrongPrime(1024)
        phi = (p - 1) * (q - 1)
        if p != q and math.gcd(E_A * E_B, phi) == 1:
            break

    modulus = p * q
    recovery_code = int.from_bytes(secrets.token_bytes(32), "big")
    while (
        recovery_code == 0
        or math.gcd(recovery_code, modulus) != 1
        or recovery_code**3 >= modulus
    ):
        recovery_code = int.from_bytes(secrets.token_bytes(32), "big")

    return (
        modulus,
        recovery_code,
        pow(recovery_code, E_A, modulus),
        pow(recovery_code, E_B, modulus),
    )


def main():
    modulus, recovery_code, ciphertext_a, ciphertext_b = generate_instance()

    print("=== RSA秘密情報保管庫：ステージ2 ===")
    print("暗号化装置は改修されましたが、2台とも同じ機密情報を保護しています。")
    print(f"n = {modulus}")
    print(f"e_a = {E_A}")
    print(f"e_b = {E_B}")
    print("機密情報のサイズ = 32 bytes")

    for _ in range(12):
        print(MENU)
        choice = input("choice> ").strip()

        if choice == "1":
            print(f"ciphertext_a = {ciphertext_a}")
        elif choice == "2":
            print(f"ciphertext_b = {ciphertext_b}")
        elif choice == "3":
            candidate_text = input("機密情報（16進数）> ").strip()
            try:
                candidate = int(candidate_text, 16)
            except ValueError:
                print("16進数として解釈できません。")
                continue
            if candidate == recovery_code:
                print("機密情報を確認しました。")
                print(f"FLAG: {FLAG}")
                return
            print("機密情報が違います。")
        elif choice == "4":
            print("終了します。")
            return
        else:
            print("1から4のいずれかを入力してください。")

    print("操作回数の上限に達しました。")


if __name__ == "__main__":
    main()

