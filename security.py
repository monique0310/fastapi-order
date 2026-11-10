from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from pwdlib import PasswordHash
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import pegar_sessao
import models
import os
from dotenv import load_dotenv

# Carrega as variáveis definidas no ficheiro .env
load_dotenv()

# Lê as variáveis de ambiente com valores de contingência (fallback)
SECRET_KEY = os.getenv("SECRET_KEY", "chave_padrao_caso_nao_encontre")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
#Instância da PWdlib usando Argon2 para criar os Hashes das senhas

password_hash = PasswordHash.recommended()

#Configurações do JWT
SECRET_KEY = "sua_chave_secreta_super_segura_para_estudos"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

#FUNÇÕES DE SENHA
def gerar_hash_senha(senha_plana: str) -> str:
    """Transforma a senha em texto puro em um Hash seguro"""
    return password_hash.hash(senha_plana)

def verificar_senha(senha_plana: str, senha_hashed:str ) -> bool:
    """Verifica se a senha enviada no login bate com o Hash salvo no banco"""
    return password_hash.verify(senha_plana, senha_hashed)

#funções de token JWT
def criar_token(dados:dict, tempo_expiracao: timedelta) -> str:
    """Função utilitária que assina o JWT com Header, Payload e Signature"""
    dados_token = dados.copy()
    agora = datetime.now(timezone.utc)
    expiracao = agora + tempo_expiracao


    dados_token.update({
        "iat": agora,
        "exp": expiracao
    })

    #Codifica o JWT assinado com a nossa SECRET_KEY
    token_jwt = jwt.encode(dados_token, SECRET_KEY, algorithm=ALGORITHM)
    return token_jwt

def criar_access_token(dados: dict) -> str:
    return criar_token(dados, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

def criar_refresh_token(dados:dict) -> str:
    return criar_token(dados, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

def pegar_usuario_atual(
        token: str = Depends(oauth2_scheme),
        session: Session = Depends(pegar_sessao)
) -> models.Usuario:
    credenciais_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi poss´vel validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try: 
        #decodifica o token usando a chave secreta
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str=payload.get("sub")
        if email is None:
            raise credenciais_exception
    except JWTError:
        raise credenciais_exception


    #busca o usuario no banco de dados

    usuario = session.query(models.Usuario).filter(models.Usuario.email == email).first()
    if usuario is None:
        raise credenciais_exception

    return usuario