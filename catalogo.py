import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse
import os

# Nome do ficheiro da base de dados
DB_NAME = 'catalogo_vendas.db'

# 1. CONFIGURAÇÃO E POPULAÇÃO DO BANCO DE DADOS
def iniciar_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Criar tabelas necessárias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL,
            categoria TEXT,
            imagem TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lojas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            nome_loja TEXT,
            whatsapp_numero TEXT
        )
    ''')
    
    # Limpar e reinserir dados iniciais para garantir a exibição na web
    cursor.execute("SELECT COUNT(*) FROM produtos")
    if cursor.fetchone()[0] == 0:
        produtos_inicial = [
            ('Samsung A32', 15000.0, 'Smartphones', 'https://unsplash.com'),
            ('Película de Vidro', 250.0, 'Acessórios', 'https://unsplash.com'),
            ('Capa Anti-choque', 450.0, 'Acessórios', 'https://unsplash.com')
        ]
        cursor.executemany("INSERT INTO produtos (nome, preco, categoria, imagem) VALUES (?, ?, ?, ?)", produtos_inicial)
        
    cursor.execute("SELECT COUNT(*) FROM lojas")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO lojas (usuario, nome_loja, whatsapp_numero) VALUES (?, ?, ?)", 
                       ('merceariatonny', 'Cellshop Leoprice', '258840000000')) # Substitua pelo seu número real
        
    conn.commit()
    conn.close()

# Inicializar o banco de dados antes de carregar a página
iniciar_db()

# 2. FUNÇÃO PARA CARREGAR PRODUTOS (COM FALLBACK SE FALHAR O BANCO)
def carregar_produtos():
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query("SELECT * FROM produtos", conn)
        conn.close()
        if not df.empty:
            return df
    except Exception:
        pass
    
    # Lista de emergência caso o SQLite sofra bloqueio de escrita no Streamlit Cloud
    dados_fallback = {
        "nome": ['Samsung A32', 'Película de Vidro', 'Capa Anti-choque'],
        "preco": [15000.0, 250.0, 450.0],
        "categoria": ['Smartphones', 'Acessórios', 'Acessórios'],
        "imagem": [
            'https://unsplash.com',
            'https://unsplash.com',
            'https://unsplash.com'
        ]
    }
    return pd.DataFrame(dados_fallback)

df_produtos = carregar_produtos()

# 3. INTERFACE PRINCIPAL (Streamlit)
st.set_page_config(page_title="Catálogo Comercial", page_icon="🛍️", layout="wide")

nome_da_loja = "Cellshop Leoprice"
whatsapp_loja = "258840000000" # Mude para o seu número do WhatsApp de Moçambique

st.title(f"🏪 {nome_da_loja}")
st.subheader("Selecione os produtos e faça a sua encomenda direta pelo WhatsApp!")

# 4. CONFIGURAÇÃO DO MENU LATERAL
st.sidebar.header("Filtros de Busca")

if 'categoria' in df_produtos.columns and not df_produtos.empty:
    categorias_disponiveis = ["Todos"] + list(df_produtos["categoria"].unique())
    categoria_selecionada = st.sidebar.selectbox("Escolha uma categoria:", categorias_disponiveis)
else:
    categoria_selecionada = "Todos"

# Filtrar produtos
if categoria_selecionada != "Todos":
    df_filtrado = df_produtos[df_produtos["categoria"] == categoria_selecionada]
else:
    df_filtrado = df_produtos

# 5. EXIBIÇÃO DE PRODUTOS E BOTÃO WHATSAPP
if df_filtrado.empty:
    st.info("Nenhum produto disponível de momento neste catálogo.")
else:
    cols = st.columns(3)
    for index, row in df_filtrado.reset_index().iterrows():
        with cols[index % 3]:
            st.image(row["imagem"], use_container_width=True)
            st.subheader(row["nome"])
            st.write(f"**Preço:** {row['preco']:.2f} MT")
            st.caption(f"Categoria: {row['categoria']}")
            
            # Link de Encomenda para o WhatsApp (M-Pesa/e-Mola)
            mensagem_cliente = f"Olá! Quero encomendar o produto: *{row['nome']}* no valor de *{row['preco']:.2f} MT*. Vou efetuar o pagamento via M-Pesa/e-Mola!"
            texto_url = urllib.parse.quote(mensagem_cliente)
            link_whatsapp_final = f"https://wa.me{whatsapp_loja}?text={texto_url}"
            
            st.link_button('🛍️ Encomendar via WhatsApp', link_whatsapp_final)
            st.markdown('---')

st.sidebar.markdown('---')
st.sidebar.caption('**Seguir nas Redes Sociais:**')
st.sidebar.caption('• Facebook | • TikTok')
