from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session
from database import Base, engine, pegar_sessao 
import models
from schemas import(
     UsuarioCriarSchema, UsuarioResponseSchema, LoginSchema, TokenSchema, ProdutoCriarSchema,
     ProdutoResponseSchema, PedidoCriarSchema, PedidoResponseSchema)

from security import gerar_hash_senha, verificar_senha, criar_access_token, criar_refresh_token
from fastapi.security import OAuth2PasswordRequestForm
from security import(
    gerar_hash_senha,
    verificar_senha,
    criar_access_token,
    criar_refresh_token,
    pegar_usuario_atual
)


#cria as tabelas no banco de dados SQLite caso ainda não existam
Base.metadata.create_all(bind=engine)

#1. instaciando a aplicação FastAPI
app = FastAPI(
    title="Api de gerenciamento de pedidos",
)

#rota protegida: retorna os dados do usuario logado
@app.get("/usuarios/me", response_model=UsuarioResponseSchema)
def ler_usuario_logado(usuario_atual: models.Usuario = Depends(pegar_usuario_atual)):
    return usuario_atual

#. rota post para receber e validar os dados de um novo usuario
@app.post("/usuarios/", response_model=UsuarioResponseSchema, status_code=status.HTTP_201_CREATED)
def criar_usuario(
    usuario_schema: UsuarioCriarSchema,
    session: Session = Depends(pegar_sessao)
):
    #verifica se já existe um usuario cadastrado com este email
    usuario_existente = session.query(models.Usuario).filter(models.Usuario.email == usuario_schema.email).first()
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="já existe um usuário cadastrado com este e-mail"
        )
    senha_criptografada = gerar_hash_senha(usuario_schema.senha)
    #instancia um novo objeto da model Usuario(estado Transient)
    novo_usuario = models.Usuario(
        nome=usuario_schema.nome,
        email=usuario_schema.email,
        senha=senha_criptografada,
        ativo=usuario_schema.ativo
    )
    #Adiciona na sessão e confirma no banco de dados com commit
    session.add(novo_usuario)
    session.commit()
    session.refresh(novo_usuario) #recarrega o obj para obter o id gerado pelo banco

    return novo_usuario
         
# Atualize os parâmetros da rota de login:
@app.post("/login/", response_model=TokenSchema)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),  # Altere de dados_login para form_data
    session: Session = Depends(pegar_sessao)
):
    # 1. O OAuth2PasswordRequestForm usa form_data.username para o e-mail
    usuario = session.query(models.Usuario).filter(models.Usuario.email == form_data.username).first()
    
    # 2. Comparamos a senha digitada (form_data.password) com o hash salvo no banco
    if not usuario or not verificar_senha(form_data.password, usuario.senha):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Se deu tudo certo, geramos os Tokens
    token_payload = {"sub": usuario.email, "usuario_id": usuario.id}
    
    access_token = criar_access_token(dados_token := token_payload)
    refresh_token = criar_refresh_token(dados_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

#rotas de produtos

@app.post("/produtos/", response_model=ProdutoResponseSchema, status_code=status.HTTP_201_CREATED)
def criar_produto(
    produto_schema: ProdutoCriarSchema,
    session: Session = Depends(pegar_sessao),
    usuario_atual: models.Usuario = Depends(pegar_usuario_atual) # Exige autenticação
):
    novo_produto = models.Produto(
        nome=produto_schema.nome,
        preco=produto_schema.preco,
        estoque=produto_schema.estoque
    )
    session.add(novo_produto)
    session.commit()
    session.refresh(novo_produto)
    return novo_produto


@app.get("/produtos/", response_model=list[ProdutoResponseSchema])
def listar_produtos(session: Session = Depends(pegar_sessao)):
    produtos = session.query(models.Produto).all()
    return produtos


# --- ROTAS DE PEDIDOS ---

@app.post("/pedidos/", response_model=PedidoResponseSchema, status_code=status.HTTP_201_CREATED)
def criar_pedido(
    pedido_schema: PedidoCriarSchema,
    session: Session = Depends(pegar_sessao),
    usuario_atual: models.Usuario = Depends(pegar_usuario_atual)
):
    valor_total_pedido = 0.0

    # 1. Validar produtos e checar estoque
    for item in pedido_schema.itens:
        produto = session.query(models.Produto).filter(models.Produto.id == item.produto_id).first()
        
        if not produto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produto ID {item.produto_id} não encontrado."
            )
        
        if produto.estoque < item.quantidade:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estoque insuficiente para o produto '{produto.nome}'. Disponível: {produto.estoque}"
            )
        
        # 2. Calcular o subtotal e atualizar o estoque do produto
        valor_total_pedido += produto.preco * item.quantidade
        produto.estoque -= item.quantidade

    # 3. Instanciar e salvar o novo pedido vinculado ao usuário logado
    novo_pedido = models.Pedido(
        usuario_id=usuario_atual.id, # Pega o ID direto do Token JWT!
        valor_total=valor_total_pedido,
        status="pago"
    )

    session.add(novo_pedido)
    session.commit()
    session.refresh(novo_pedido)

    return novo_pedido


@app.get("/pedidos/meus-pedidos", response_model=list[PedidoResponseSchema])
def listar_meus_pedidos(
    session: Session = Depends(pegar_sessao),
    usuario_atual: models.Usuario = Depends(pegar_usuario_atual)
):
    # Filtra apenas os pedidos pertencentes ao usuário logado
    pedidos = session.query(models.Pedido).filter(models.Pedido.usuario_id == usuario_atual.id).all()
    return pedidos