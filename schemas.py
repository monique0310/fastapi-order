from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, List
from datetime import datetime

#Schema para receber os dados ao criar um usuario
class UsuarioCriarSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nome: str
    email: EmailStr #valida se o texto realmente é um e-mail valido(contém @ e dominio)
    senha: str = Field(min_length=6, description="A senha deve ter no minimo 6 caracteres")
    ativo: Optional[bool] = True


#schema para resposta do usuario (sem retornar a senha hashed)
class UsuarioResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True) #converte obj do sqlalchemy para respostas em formato json

    id: int
    nome: str
    email: EmailStr
    ativo: bool

#Schema para o formulário de Login
class LoginSchema(BaseModel):
    email: EmailStr
    senha: str

#Schema para a resposta do Token de Acesso
class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

#Schemas de produtos
class ProdutoCriarSchema(BaseModel):
    nome: str
    preco: float = Field(gt=0, description="O preço deve ser maior que zero")
    estoque: int = Field(ge=0, description="O estoque não pode ser negativo")

class ProdutoResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    preco: float
    estoque: int

#schemas de item e pedido
class ItemPedidoSchema(BaseModel):
    produto_id: int
    #field adiciona regras de validação extras
    quantidade: int = Field(gt=0, description="a quantidade deve ser pelo menos 1")

class PedidoCriarSchema(BaseModel):
    itens: List[ItemPedidoSchema]

class PedidoResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    valor_total: float
    status: str
    criado_em: datetime