import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse

# 1. CONFIGURAÇÃO VISUAL DA PÁGINA
st.set_page_config(page_title="Cellshop Leoprice - V5 Máxima", page_icon="📱", layout="wide")

# Estilização profissional via CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #25D366; color: white; font-weight: bold; }
    .stButton>button:hover { background-color: #128C7E; color: white; }
    .product-box { padding: 15px; border-radius: 10px; background-color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# 2. BASE DE DADOS COMPLETA DA VERSÃO V5 MÁXIMA
def iniciar_db_maxima():
    conn = sqlite3.connect('catalogo_vendas.db')
    cursor = conn.cursor()
    
    # Criar a tabela base se não existir
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
    
    # CORREÇÃO CRÍTICA: Se a tabela já existia sem a coluna 'descricao', adiciona-a agora
    try:
        cursor.execute("ALTER TABLE produtos ADD COLUMN descricao TEXT")
    except sqlite3.OperationalError:
        pass  # A coluna já existe, não faz nada
        
    # Verificar se precisamos de preencher com a lista oficial completa
    cursor.execute("SELECT COUNT(*) FROM produtos")
    if cursor.fetchone() == 0:
        produtos_v5 = [
            ('Samsung Galaxy A32', 15000.0, 'Smartphones', 'https://unsplash.com', '128GB Armazenamento, 4GB RAM, Tela Super AMOLED de 6.4".'),
            ('Película de Vidro 3D', 250.0, 'Acessórios', 'https://unsplash.com', 'Proteção máxima contra quedas e riscos para o ecrã.'),
            ('Capa Antichoque Militar', 450.0, 'Acessórios', 'https://unsplash.com', 'Bordas reforçadas em silicone de alta resistência.'),
            ('Carregador Rápido Tipo-C 25W', 1200.0, 'Carregadores', 'https://unsplash.com', 'Carregamento turbo compatível com a linha Samsung.'),
            ('Auriculares Bluetooth Pro', 2500.0, 'Áudio', 'https://unsplash.com', 'Som de alta fidelidade com cancelamento de ruído passivo.'),
            ('Cabo USB-C Reforçado 2m', 350.0, 'Acessórios', 'https://unsplash.com', 'Cabo em nylon trançado super resistente para dados e carga.')
        ]
        cursor.executemany("INSERT INTO produtos (nome, preco, categoria, imagem, descricao) VALUES (?, ?, ?, ?, ?)", produtos_v5)
    
    conn.commit()
    conn.close()

iniciar_db_maxima()

# 3. CARREGAMENTO DOS DADOS COM GARANTIA DE COLUNAS
def carregar_produtos_maxima():
    conn = sqlite3.connect('catalogo_vendas.db')
    df = pd.read_sql_query("SELECT * FROM produtos", conn)
    conn.close()
    
    # Garante que o DataFrame tem a coluna descricao mesmo se o banco falhar
    if 'descricao' not in df.columns:
        df['descricao'] = 'Sem descrição disponível.'
    return df

df_produtos = carregar_produtos_maxima()

# 4. INICIALIZAÇÃO DO CARRINHO DE COMPRAS DINÂMICO
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = {}

# 5. ESTRUTURA DA INTERFACE VISUAL
st.title("🏪 Loja de celulares Leoprice")
st.subheader("Selecione os produtos de seguida e monte a sua encomenda direta para o WhatsApp!")

# Configuração do contacto de destino (Moçambique)
whatsapp_loja = "258840000000"  # Insira o seu número real aqui

# 6. CONFIGURAÇÃO DO MENU LATERAL (Filtros e Informações do Cliente)
st.sidebar.header("⚙️ Painel de Filtros")
if not df_produtos.empty:
    categorias = ["Todos"] + list(df_produtos["categoria"].unique())
    categoria_sel = st.sidebar.selectbox("Escolha uma categoria:", categorias)
else:
    categoria_sel = "Todos"

if categoria_sel != "Todos":
    df_exibicao = df_produtos[df_produtos["categoria"] == categoria_sel]
else:
    df_exibicao = df_produtos

st.sidebar.markdown("---")
st.sidebar.header("👤 Dados da Encomenda")
nome_cliente = st.sidebar.text_input("O seu Nome:", placeholder="Ex: Leonardo Francisco")
opcao_pagamento = st.sidebar.selectbox("Método de Pagamento Preferido:", ["M-Pesa", "e-Mola", "Dinheiro em Mão"])

# 7. EXIBIÇÃO DA GRELHA DE PRODUTOS V5
if df_exibicao.empty:
    st.info("Nenhum produto encontrado nesta categoria.")
else:
    cols = st.columns(3)
    for idx, row in df_exibicao.reset_index().iterrows():
        with cols[idx % 3]:
            st.markdown(f'<div class="product-box">', unsafe_allow_html=True)
            st.image(row["imagem"], use_container_width=True)
            st.subheader(row["nome"])
            
            # Uso seguro do campo descrição
            desc_texto = row.get("descricao", "Sem descrição.")
            st.write(f"*{desc_texto}*")
            
            st.markdown(f"### **{row['preco']:.2f} MT**")
            st.caption(f"📁 Categoria: {row['categoria']}")
            
            # Sistema de Controlo de Quantidade por Item
            prod_id = str(row["id"])
            qtd_atual = st.session_state.carrinho.get(prod_id, 0)
            
            col_menos, col_qtd, col_mais = st.columns()
            with col_menos:
                if st.button("➖", key=f"sub_{prod_id}"):
                    if prod_id in st.session_state.carrinho:
                        st.session_state.carrinho[prod_id] = max(0, st.session_state.carrinho[prod_id] - 1)
                        if st.session_state.carrinho[prod_id] == 0:
                            del st.session_state.carrinho[prod_id]
                        st.rerun()
            with col_qtd:
                st.markdown(f"<h4 style='text-align: center; margin-top: 5px;'>{qtd_atual}</h4>", unsafe_with_html=True)
            with col_mais:
                if st.button("➕", key=f"add_{prod_id}"):
                    st.session_state.carrinho[prod_id] = st.session_state.carrinho.get(prod_id, 0) + 1
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# 8. RESUMO DO CARRINHO DE COMPRAS E GERADOR DO LINK WHATSAPP MÁXIMO
st.markdown("---")
st.header("🛒 Resumo do seu Pedido Atual")

if not st.session_state.carrinho:
    st.info("O seu carrinho está vazio. Adicione itens clicando no botão ➕ dos produtos acima.")
else:
    linhas_resumo = []
    total_geral = 0.0
    texto_mensagem_whatsapp = f"Olá, Cellshop Leoprice! Gostaria de fazer uma encomenda.\n\n"
    
    if nome_cliente:
        texto_mensagem_whatsapp += f"👤 *Cliente:* {nome_cliente}\n"
    texto_mensagem_whatsapp += f"💳 *Forma de Pagamento:* {opcao_pagamento}\n"
    texto_mensagem_whatsapp += "-----------------------------------------\n"
    texto_mensagem_whatsapp += "📦 *Produtos Escolhidos:*\n"

    for p_id, qtd in st.session_state.carrinho.items():
        if qtd > 0:
            prod_info = df_produtos[df_produtos["id"] == int(p_id)].iloc[0]
            subtotal = prod_info["preco"] * qtd
            total_geral += subtotal
            
            linhas_resumo.append({
                "Produto": prod_info["nome"],
                "Preço Unitário": f"{prod_info['preco']:.2f} MT",
                "Quantidade": qtd,
                "Subtotal": f"{subtotal:.2f} MT"
            })
            
            texto_mensagem_whatsapp += f"• {qtd}x *{prod_info['nome']}* ({prod_info['preco']:.2f} MT cada) -> Subtotal: *{subtotal:.2f} MT*\n"

    texto_mensagem_whatsapp += "-----------------------------------------\n"
    texto_mensagem_whatsapp += f"💰 *TOTAL DA ENCOMENDA:* {total_geral:.2f} MT\n\n"
    texto_mensagem_whatsapp += "Por favor, confirmem a disponibilidade para eu efetuar a transferência!"

    # Exibir tabela organizada para o cliente validar
    st.table(pd.DataFrame(linhas_resumo))
    
    col_vazia, col_total = st.columns()
    with col_total:
        st.markdown(f"## **Total: {total_geral:.2f} MT**")
        
        # Codificar o texto estruturado para URL
        texto_codificado = urllib.parse.quote(texto_mensagem_whatsapp)
        link_final_wa = f"https://wa.me{whatsapp_loja}?text={texto_codificado}"
        
        # Botão Máximo de Finalização
        st.link_button("🚀 Enviar Encomenda Pronta para o WhatsApp", link_final_wa)

# Rodapé das Redes Sociais
st.sidebar.markdown('---')
st.sidebar.caption('**Seguir nas Redes Sociais:**')
st.sidebar.caption('• Facebook | • TikTok')
