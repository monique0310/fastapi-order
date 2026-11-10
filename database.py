from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


#1. definimos o caminho do arquivo do banco SQLite
SQLALCHEMY_DATABASE_URL =  "sqlite:///./banco.db"

#2. Criamos o Engine (o motor de conexão com o banco) // ele traduz as operações do python para comandos SQL reais
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} #Necessário apenas para o SQLite no FastAPI
)


#3. Criamos a fábrica de sessões (SessionLocal) // usada para evitar abrir e fechas sessões manualmente a todo momento
#após as alterações, ao final, executa o session.commit() para salvar tudo de uma vez ou session.rollback() se algo der errado
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#4. definimos a classe Base que todos os nossos Models vão herdar
Base = declarative_base() #quando a classe herda esta base o slqalchemy passa a rastrear a classe e entende
#que ela representa uma tabela no banco

#5. Função geradora (Dependency) para gerenciar o ciclo de vida da Sessão
def pegar_sessao():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()