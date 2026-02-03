import re


def only_digits(value: str) -> str:
    return re.sub(r"\D+", "", value or "")


def is_valid_cpf(cpf: str) -> bool:
    cpf = only_digits(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = (soma * 10) % 11
    d1 = 0 if d1 == 10 else d1
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = (soma * 10) % 11
    d2 = 0 if d2 == 10 else d2
    return cpf[-2:] == f"{d1}{d2}"


def is_valid_cnpj(cnpj: str) -> bool:
    cnpj = only_digits(cnpj)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
    d1 = 11 - (soma % 11)
    d1 = 0 if d1 >= 10 else d1
    soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
    d2 = 11 - (soma % 11)
    d2 = 0 if d2 >= 10 else d2
    return cnpj[-2:] == f"{d1}{d2}"


def format_cpf(cpf: str) -> str:
    digits = only_digits(cpf)
    if len(digits) != 11:
        return cpf or ""
    return f"{digits[0:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:11]}"


def format_cnpj(cnpj: str) -> str:
    digits = only_digits(cnpj)
    if len(digits) != 14:
        return cnpj or ""
    return (
        f"{digits[0:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"
    )
