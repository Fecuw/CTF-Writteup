import math
import os
import secrets

from Crypto.Util.number import getPrime, getStrongPrime, isPrime


FLAG = os.environ.get("FLAG", "katagaitai-CTF{dummy_flag}")
REGISTER_LIMIT = 3
REPRESENTATIVE_LIMIT = 1 << 20
MENU = """
1. 一時資格を登録する
2. 所属証明を検証する
3. 現在のアキュムレータ値を確認する
4. 管理者の所属証明を提出する
5. 終了する
"""


def generate_instance():
    p = getStrongPrime(1024)
    q = getStrongPrime(1024)
    while p == q:
        q = getStrongPrime(1024)
    modulus = p * q

    while True:
        seed = secrets.randbelow(modulus - 3) + 2
        if math.gcd(seed, modulus) != 1:
            continue
        base = pow(seed, 2, modulus)
        if base != 1:
            break

    existing_product = math.prod(getPrime(64) for _ in range(4))
    initial_accumulator = pow(base, existing_product, modulus)

    factors = set()
    while len(factors) < REGISTER_LIMIT:
        factors.add(getPrime(20))
    administrator_representative = math.prod(factors)

    return modulus, base, initial_accumulator, administrator_representative


def main():
    modulus, base, initial_accumulator, administrator_representative = generate_instance()
    accumulator = initial_accumulator
    registered = set()

    print("=== 資格情報登録所 ===")
    print("職員資格はRSAアキュムレータで管理されています。")
    print("一時資格には、2^20未満（最大20ビット）の素数を代表値として登録できます。")
    print(f"n = {modulus}")
    print(f"g = {base}")
    print(f"initial_accumulator = {initial_accumulator}")
    print(f"administrator_representative = {administrator_representative}")

    for _ in range(16):
        print(MENU)
        choice = input("choice> ").strip()

        if choice == "1":
            if len(registered) >= REGISTER_LIMIT:
                print("一時資格の登録上限に達しました。")
                continue

            representative_text = input("登録する代表値> ").strip()
            try:
                representative = int(representative_text)
            except ValueError:
                print("整数として解釈できません。")
                continue

            if not 1 < representative < REPRESENTATIVE_LIMIT:
                print(f"代表値は1より大きく{REPRESENTATIVE_LIMIT}未満にしてください。")
                continue
            if not isPrime(representative):
                print("代表値は素数でなければなりません。")
                continue
            if representative == administrator_representative:
                print("管理者資格は登録できません。")
                continue
            if representative in registered:
                print("その代表値は登録済みです。")
                continue

            membership_witness = accumulator
            registered.add(representative)
            accumulator = pow(accumulator, representative, modulus)
            print("一時資格を登録しました。")
            print(f"representative = {representative}")
            print(f"membership_witness = {membership_witness}")
        elif choice == "2":
            representative_text = input("検証する代表値> ").strip()
            witness_text = input("membership witness> ").strip()
            try:
                representative = int(representative_text)
                witness = int(witness_text)
            except ValueError:
                print("代表値とwitnessは整数で入力してください。")
                continue

            if not 1 < representative or not 0 < witness < modulus:
                print("代表値またはwitnessが範囲外です。")
                continue
            if pow(witness, representative, modulus) == accumulator:
                print("有効な所属証明です。")
            else:
                print("所属証明を確認できませんでした。")
        elif choice == "3":
            print(f"accumulator = {accumulator}")
            print(f"registered_count = {len(registered)}")
        elif choice == "4":
            witness_text = input("管理者のmembership witness> ").strip()
            try:
                witness = int(witness_text)
            except ValueError:
                print("整数として解釈できません。")
                continue

            if not 0 < witness < modulus:
                print("witnessは0より大きくn未満にしてください。")
                continue
            if pow(witness, administrator_representative, modulus) == accumulator:
                print("管理者の所属証明を確認しました。")
                print(f"FLAG: {FLAG}")
                return
            print("所属証明を確認できませんでした。")
        elif choice == "5":
            print("終了します。")
            return
        else:
            print("1から5のいずれかを入力してください。")

    print("操作回数の上限に達しました。")


if __name__ == "__main__":
    main()
