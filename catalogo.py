import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse

# 1. CONFIGURAÇÃO DO BANCO DE DADOS (SQLite)
def iniciar_db():
    conn = sqlite3.connect('catalogo_vendas.db')
    cursor = conn.cursor()
    
    # Criar a tabela de produtos com todas as colunas necessárias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT EXISTS,
            preco REAL,
            categoria TEXT,
            imagem TEXT
        )
    ''')
    
    # Criar a tabela de lojas para guardar as configurações da loja
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lojas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            nome_loja TEXT,
            whatsapp_numero TEXT
        )
    ''')
    
    # Inserir dados de teste padrão caso o banco esteja vazio
    cursor.execute("SELECT COUNT(*) FROM produtos")
    if cursor.fetchone() == 0:
        produtos_inicial = [
            ('Samsung A32', 15000.0, 'Smartphones', 'https://placeholder.com'),
            ('Película de Vidro', 250.0, 'Acessórios', 'https://placeholder.com'),
            ('Capa Anti-choque', 450.0, 'Acessórios', 'https://placeholder.com')
        ]
        cursor.executemany("INSERT INTO produtos (nome, preco, categoria, imagem) VALUES (?, ?, ?, ?)", produtos_inicial)
        
    cursor.execute("SELECT COUNT(*) FROM lojas")
    if cursor.fetchone() == 0:
        # Cadastra a loja padrão (Substitua o número de exemplo pelo seu número real com código de Moçambique 258)
        cursor.execute("INSERT INTO lojas (usuario, nome_loja, whatsapp_numero) VALUES (?, ?, ?)", 
                       ('merceariatonny', 'Cellshop Leoprice', '258840000000'))
        
    conn.commit()
    conn.close()

# Inicializar o banco ao correr o ficheiro
iniciar_db()

# 2. FUNÇÃO PARA CARREGAR PRODUTOS
def carregar_produtos():
    conn = sqlite3.connect('catalogo_vendas.db')
    df = pd.read_sql_query("SELECT * FROM produtos", conn)
    conn.close()
    return df

df_produtos = carregar_produtos()

# 3. INTERFACE PRINCIPAL (Streamlit)
st.set_page_config(page_title="Catálogo Comercial", page_icon="🛍️", layout="wide")

# Buscar configurações da loja no banco de dados
conn = sqlite3.connect('catalogo_vendas.db')
cursor = conn.cursor()
cursor.execute("SELECT nome_loja, whatsapp_numero FROM lojas LIMIT 1")
loja_dados = cursor.fetchone()
conn.close()

if loja_dados:
    nome_da_loja = loja_dados[0]
    whatsapp_loja = loja_dados[1]
else:
    nome_da_loja = "Minha Loja"
    whatsapp_loja = "258840000000" # Fallback caso falhe

st.title(f"🏪 {nome_da_loja}")
st.subheader("Selecione os produtos e faça a sua encomenda direta pelo WhatsApp!")

# 4. CONFIGURAÇÃO DO MENU LATERAL (Filtros e Redes Sociais)
st.sidebar.header("Filtros de Busca")

if not df_produtos.empty and 'categoria' in df_produtos.columns:
    categorias_disponiveis = ["Todos"] + list(df_produtos["categoria"].unique())
    categoria_selecionada = st.sidebar.selectbox("Escolha uma categoria:", categorias_disponiveis)
else:
    categoria_selecionada = "Todos"
    st.sidebar.warning("A carregar categorias...")

# Filtrar produtos com base na seleção
if categoria_selecionada != "Todos" and not df_produtos.empty:
    df_filtrado = df_produtos[df_produtos["categoria"] == categoria_selecionada]
else:
    df_filtrado = df_produtos

# 5. EXIBIÇÃO DE PRODUTOS E INTEGRAÇÃO DO BOTÃO WHATSAPP
if df_filtrado.empty:
    st.info("Nenhum produto disponível de momento neste catálogo.")
else:
    # Criar uma grelha visual de 3 colunas para os produtos
    cols = st.columns(3)
    for index, row in df_filtrado.iterrows():
        with cols[index % 3]:
            # Imagem do Produto
            st.image(row["imagem"], use_container_width=True)
            st.subheader(row["nome"])
            st.write(f"**Preço:** {row['preco']:.2f} MT")
            
            if 'categoria' in row:
                st.caption(f"Categoria: {row['categoria']}")
            
            # --- CONEXÃO WHATSAPP COM LINK DIRETO ---
            # Monta o texto que o cliente vai enviar de forma automática
            mensagem_cliente = f"Olá! Quero encomendar o produto: *{row['nome']}* no valor de *{row['preco']:.2f} MT*. Vou efetuar o pagamento via M-Pesa/e-Mola!"
            
            # Codifica a mensagem para o formato aceito em URLs (substitui espaços por %20, etc.)
            texto_url = urllib.parse.quote(mensagem_cliente)
            
            # Gera o link final api/wa.me associado ao número da loja cadastrado
            link_whatsapp_final = f"https://wa.me{whatsapp_loja}?text={texto_url}"
            
            # Botão interativo que abre o WhatsApp com a mensagem pronta
            st.link_button('🛍️ Encomendar via WhatsApp', link_whatsapp_final)
            st.markdown('---')

# Redes Sociais no Menu Lateral
st.sidebar.markdown('---')
st.sidebar.caption('**Seguir nas Redes Sociais:**')
st.sidebar.caption('• Facebook | • TikTok')
