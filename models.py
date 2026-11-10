from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone #timezone gerencia a informação de fuso horário
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    #unique garante que não exista dois registros com o mesmo valor nesta coluna
    #index cria um indice para que o banco ache a informação mais rápido
    #nullable define que o campo não pode ser nulo
    #default evita que a coluna fique vazia
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False) 
    senha = Column(String, nullable=False)
    ativo = Column(Boolean, default=True)
    admin = Column(Boolean, default=False)

    #relacionamento: um usuario pode ter vários pedidos
    pedidos = relationship("Pedido", back_populates="cliente")

class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String, nullable=False)
    preco = Column(Float, nullable=False)
    estoque = Column(Integer, default=0)

class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    #chave estrangeira: vincula o pedido diretamente ao id do usuario logado
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    valor_total = Column(Float, nullable=False, default=0.0)
    status = Column(String, default="pendente") #pendente, pago, cancelado
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    #relacionamento para acessar o objeto do usuario direto pelo pedido
    cliente = relationship("Usuario", back_populates="pedidos")
