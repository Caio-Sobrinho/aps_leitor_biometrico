import os
import base64
import hashlib

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv

load_dotenv()


def obter_chave():
    chave_base64 = os.getenv('BIOMETRIA_CHAVE_BASE64')
    if not chave_base64:
        raise ValueError('Chave de criptografia não encontrada no .env.')
    try:
        chave = base64.b64decode(chave_base64, validate=True)
    except (ValueError, base64.binascii.Error) as erro:
        raise ValueError('A chave de criptografia não está em Base64 válido.') from erro
    if len(chave) != 32:
        raise ValueError('A chave AES-256 deve possuir exatamente 32 bytes.')
    return chave


def criptografar_dados(dados):
    if not isinstance(dados, bytes):
        raise TypeError('Os dados para criptografia devem ser bytes.')
    if not dados:
        raise ValueError('Não é permitido criptografar conteúdo vazio.')
    nonce = os.urandom(12)
    arquivo_criptografado = nonce + AESGCM(obter_chave()).encrypt(nonce, dados, None)
    return arquivo_criptografado, hashlib.sha256(arquivo_criptografado).hexdigest()


def descriptografar_dados(arquivo_criptografado):
    if not isinstance(arquivo_criptografado, bytes):
        raise TypeError('O conteúdo criptografado deve ser bytes.')
    if len(arquivo_criptografado) < 29:
        raise ValueError('Arquivo criptografado inválido ou incompleto.')
    nonce = arquivo_criptografado[:12]
    try:
        return AESGCM(obter_chave()).decrypt(nonce, arquivo_criptografado[12:], None)
    except InvalidTag as erro:
        raise ValueError('Falha na autenticação dos dados criptografados: chave incorreta ou arquivo adulterado.') from erro
