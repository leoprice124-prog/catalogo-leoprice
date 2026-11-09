import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse

# 1. CONFIGURAÇÃO VISUAL DA PÁGINA
st.set_page_config(page_title="Cellshop Leoprice", page_icon="📱", layout="wide")

# 2. BASE DE DADOS SEGURA E DIRETA
def iniciar_db():
    conn = sqlite3.connect('catalogo_vendas.db')
    cursor = conn.cursor()
    
    # Criar a tabela garantindo que a coluna 'categoria' e 'descricao' existem
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL,
            categoria TEXT,
            imagem TEXT,
            descricao TEXT
        )
    ''')
    
    # Inserir os produtos padrão se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM produtos")
    if cursor.fetchone() == 0:
        produtos_oficiais = [
            ('Samsung Galaxy A32', 15000.0, 'Smartphones', 'https://unsplash.com', '128GB Armazenamento, 4GB RAM, Tela Super AMOLED de 6.4".'),
            ('Película de Vidro 3D', 250.0, 'Acessórios', 'https://unsplash.com', 'Proteção máxima contra quedas e riscos para o ecrã.'),
            ('Capa Antichoque Militar', 450.0, 'Acessórios', 'https://unsplash.com', 'Bordas reforçadas em silicone de alta resistência.'),
            ('Carregador Rápido 25W', 1200.0, 'Carregadores', 'https://unsplash.com', 'Carregamento turbo compatível com a linha Samsung.'),
            ('Auriculares Bluetooth Pro', 2500.0, 'Áudio', 'https://unsplash.com', 'Som de alta fidelidade com cancelamento de ruído.')
        ]
        cursor.executemany("INSERT INTO produtos (nome, preco, categoria, imagem, descricao) VALUES (?, ?, ?, ?, ?)", produtos_oficiais)
        
    conn.commit()
    conn.close()

# Inicializar o banco de dados
iniciar_db()

# 3. CARREGAR PRODUTOS
def carregar_produtos():
    conn = sqlite3.connect('catalogo_vendas.db')
    df = pd.read_sql_query("SELECT * FROM produtos", conn)
    conn.close()
    return df

df_produtos = carregar_produtos()

# Inicializar o carrinho de compras na sessão
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = {}

# 4. INTERFACE PRINCIPAL
st.title("🏪 Loja de celulares Leoprice")
st.subheader("Selecione os produtos de seguida e monte a sua encomenda direta para o WhatsApp!")

# Contacto de WhatsApp da sua loja em Moçambique
whatsapp_loja = "258840000000"  # Insira o seu número real aqui

# 5. MENU LATERAL (Filtros e Dados)
st.sidebar.header("⚙️ Painel de Filtros")
if not df_produtos.empty:
    categorias_disponiveis = ["Todos"] + list(df_produtos["categoria"].unique())
    categoria_selecionada = st.sidebar.selectbox("Escolha uma categoria:", categorias_disponiveis)
else:
    categoria_selecionada = "Todos"

# Filtrar o DataFrame com base na seleção
if categoria_selecionada != "Todos" and not df_produtos.empty:
    df_filtrado = df_produtos[df_produtos["categoria"] == categoria_selecionada]
else:
    df_filtrado = df_produtos

st.sidebar.markdown("---")
st.sidebar.header("👤 Dados do Cliente")
nome_cliente = st.sidebar.text_input("O seu Nome:", placeholder="Ex: Leonardo Francisco")
opcao_pagamento = st.sidebar.selectbox("Método de Pagamento Preferido:", ["M-Pesa", "e-Mola", "Dinheiro em Mão"])

# 6. EXIBIÇÃO DOS PRODUTOS EM COLUNAS
if df_filtrado.empty:
    st.info("Nenhum produto disponível de momento.")
else:
    cols = st.columns(3)
    for index, row in df_filtrado.reset_index().iterrows():
        with cols[index % 3]:
            st.image(row["imagem"], use_container_width=True)
            st.subheader(row["nome"])
            st.write(f"*{row['descricao']}*")
            st.markdown(f"### **{row['preco']:.2f} MT**")
            st.caption(f"📁 Categoria: {row['categoria']}")
            
            # Controlo de Quantidade Simples por botões
            prod_id = str(row["id"])
            qtd_atual = st.session_state.carrinho.get(prod_id, 0)
            
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("➖", key=f"sub_{prod_id}"):
                    st.session_state.carrinho[prod_id] = max(0, qtd_atual - 1)
                    st.rerun()
            with c2:
                st.markdown(f"<h4 style='text-align: center; margin-top: 5px;'>{qtd_atual}</h4>", unsafe_allow_html=True)
            with c3:
                if st.button("➕", key=f"add_{prod_id}"):
                    st.session_state.carrinho[prod_id] = qtd_atual + 1
                    st.rerun()
            st.markdown('---')

# 7. RESUMO DO PEDIDO E CONEXÃO WHATSAPP
st.markdown("---")
st.header("🛒 Resumo do seu Pedido Atual")

carrinho_ativo = {k: v for k, v in st.session_state.carrinho.items() if v > 0}

if not carrinho_ativo:
    st.info("O seu carrinho está vazio. Adicione itens clicando no botão ➕ dos produtos acima.")
else:
    linhas_resumo = []
    total_geral = 0.0
    
    texto_mensagem = f"Olá, Loja Leoprice! Gostaria de fazer uma encomenda.\n\n"
    if nome_cliente:
        texto_mensagem += f"👤 *Cliente:* {nome_cliente}\n"
    texto_mensagem += f"💳 *Forma de Pagamento:* {opcao_pagamento}\n"
    texto_mensagem += "-----------------------------------------\n"
    
    for p_id, qtd in carrinho_ativo.items():
        prod_info = df_produtos[df_produtos["id"] == int(p_id)].iloc[0]
        subtotal = prod_info["preco"] * qtd
        total_geral += subtotal
        
        linhas_resumo.append({
            "Produto": prod_info["nome"],
            "Preço Unitário": f"{prod_info['preco']:.2f} MT",
            "Quantidade": qtd,
            "Subtotal": f"{subtotal:.2f} MT"
        })
        texto_mensagem += f"• {qtd}x *{prod_info['nome']}* -> Subtotal: *{subtotal:.2f} MT*\n"
        
    texto_mensagem += "-----------------------------------------\n"
    texto_mensagem += f"💰 *TOTAL DA ENCOMENDA:* {total_geral:.2f} MT\n\n"
    texto_mensagem += "Por favor, confirmem a disponibilidade para eu efetuar o envio via M-Pesa/e-Mola!"

    st.table(pd.DataFrame(linhas_resumo))
    st.markdown(f"## **Total: {total_geral:.2f} MT**")
    
    texto_codificado = urllib.parse.quote(texto_mensagem)
    link_whatsapp_final = f"https://wa.me{whatsapp_loja}?text={texto_codificado}"
    st.link_button("🚀 Enviar Encomenda Pronta para o WhatsApp", link_whatsapp_final)

# Rodapé simples
st.sidebar.markdown('---')
st.sidebar.caption('**Seguir nas Redes Sociais:**')
st.sidebar.caption('• Facebook | • TikTok')
