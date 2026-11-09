import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse

# 1. CONFIGURAÇÃO VISUAL DA PÁGINA
st.set_page_config(page_title="Loja Leoprice V5", page_icon="📱", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    .product-box { padding: 20px; border-radius: 12px; background-color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 25px; border: 1px solid #eef2f5; }
    .shop-header { padding: 20px; border-radius: 10px; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; margin-bottom: 25px; }
    </style>
""", unsafe_allow_html=True)

# 2. BANCO DE DADOS INTEGRADO
def iniciar_banco():
    conn = sqlite3.connect('banco_leoprice_completo.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_loja TEXT,
            whatsapp TEXT,
            mpesa TEXT,
            emola TEXT
        )
    ''')
    
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
    
    cursor.execute("SELECT COUNT(*) FROM configuracao")
    if cursor.fetchone() == 0:
        cursor.execute('''
            INSERT INTO configuracao (nome_loja, whatsapp, mpesa, emola)
            VALUES (?, ?, ?, ?)
        ''', ('Loja de celulares Leoprice', '258840000000', '840000000', '860000000'))
        
    cursor.execute("SELECT COUNT(*) FROM produtos")
    if cursor.fetchone() == 0:
        produtos_inicial = [
            ('Samsung Galaxy A32', 15000.0, 'Smartphones', 'https://unsplash.com', '128GB Armazenamento, 4GB RAM.'),
            ('Película de Vidro 3D', 250.0, 'Acessórios', 'https://unsplash.com', 'Proteção máxima contra riscos.'),
            ('Capa Antichoque', 450.0, 'Acessórios', 'https://unsplash.com', 'Silicone de alta resistência.')
        ]
        cursor.executemany('INSERT INTO produtos (nome, preco, categoria, imagem, descricao) VALUES (?, ?, ?, ?, ?)', produtos_inicial)
        
    conn.commit()
    conn.close()

iniciar_banco()

# 3. FUNÇÕES DE LEITURA E ESCRITA
def obter_config():
    conn = sqlite3.connect('banco_leoprice_completo.db')
    df = pd.read_sql_query("SELECT * FROM configuracao LIMIT 1", conn)
    conn.close()
    if not df.empty:
        return df.iloc[0]
    return None

def carregar_produtos():
    conn = sqlite3.connect('banco_leoprice_completo.db')
    df = pd.read_sql_query("SELECT * FROM produtos", conn)
    conn.close()
    return df

# 4. CONTROLO DE ABAS
aba_catalogo, aba_painel = st.tabs(["🛒 Catálogo de Vendas (Clientes)", "⚙️ Painel de Registo de Produtos"])

config = obter_config()
if config is not None:
    nome_loja_atual = config['nome_loja']
    whatsapp_atual = config['whatsapp']
    mpesa_atual = config['mpesa']
    emola_atual = config['emola']
else:
    nome_loja_atual = "Loja de celulares Leoprice"
    whatsapp_atual = "258840000000"
    mpesa_atual = "840000000"
    emola_atual = "860000000"

if 'carrinho' not in st.session_state:
    st.session_state.carrinho = {}

# ==========================================
# ABA 1: CLIENTES (CATÁLOGO DE VENDAS)
# ==========================================
with aba_catalogo:
    st.markdown(f"""
        <div class='shop-header'>
            <h1 style='margin:0;color:white;'>🏪 {nome_loja_atual}</h1>
            <p style='margin:5px 0 0 0;color:white;'>Escolha os produtos abaixo e envie o pedido direto para o nosso WhatsApp!</p>
        </div>
    """, unsafe_allow_html=True)
    
    df_produtos = carregar_produtos()
    
    # Menu Lateral para o Cliente
    st.sidebar.header("👤 Dados da Encomenda")
    nome_cliente = st.sidebar.text_input("O seu Nome:", placeholder="Ex: Leonardo Francisco")
    metodo_pago = st.sidebar.selectbox("Pagar via:", ["M-Pesa", "e-Mola", "Dinheiro"])
    
    if not df_produtos.empty:
        st.sidebar.markdown("---")
        st.sidebar.header("🔍 Categorias")
        categorias = ["Todos"] + list(df_produtos['categoria'].unique())
        cat_selecionada = st.sidebar.selectbox("Filtrar:", categories)
        if cat_selecionada != "Todos":
            df_produtos = df_produtos[df_produtos['categoria'] == cat_selecionada]

    if df_produtos.empty:
        st.info("Nenhum produto em exibição de momento.")
    else:
        cols = st.columns(3)
        for idx, row in df_produtos.reset_index().iterrows():
            with cols[idx % 3]:
                st.markdown("<div class='product-box'>", unsafe_allow_html=True)
                
                link_imagem = row['imagem'] if row['imagem'] else "https://placeholder.com"
                st.image(link_imagem, use_container_width=True)
                    
                st.subheader(row['nome'])
                st.write(f"*{row['descricao']}*")
                st.markdown(f"### **{row['preco']:.2f} MT**")
                st.caption(f"📁 Categoria: {row['categoria']}")
                
                pid = str(row['id'])
                qtd_atual = st.session_state.carrinho.get(pid, 0)
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("➖", key=f"sub_{pid}"):
                        st.session_state.carrinho[pid] = max(0, qtd_atual - 1)
                        st.rerun()
                with c2:
                    st.markdown(f"<h4 style='text-align:center;margin-top:5px;'>{qtd_atual}</h4>", unsafe_allow_html=True)
                with c3:
                    if st.button("➕", key=f"add_{pid}"):
                        st.session_state.carrinho[pid] = qtd_atual + 1
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    # RESUMO DO PEDIDO DO CLIENTE
    st.markdown("---")
    st.header("🛒 Carrinho de Compras")
    
    carrinho_filtrado = {k: v for k, v in st.session_state.carrinho.items() if v > 0}
    
    if not carrinho_filtrado:
        st.info("O carrinho está vazio. Adicione itens acima clicando no botão ➕.")
    else:
        tabela_dados = []
        total_geral = 0.0
        
        mensagem_whatsapp = f"Olá, {nome_loja_atual}! Gostaria de fazer uma encomenda:\n\n"
        if nome_cliente:
            mensagem_whatsapp += f"👤 *Cliente:* {nome_cliente}\n"
        mensagem_whatsapp += f"💳 *Forma de Pagamento:* {metodo_pago}\n"
        mensagem_whatsapp += "---------------------------------\n"
        
        df_completo = carregar_produtos()
        for pid, qtd in carrinho_filtrado.items():
            prod_row = df_completo[df_completo['id'] == int(pid)].iloc[0]
            subtotal = prod_row['preco'] * qtd
            total_geral += subtotal
            
            tabela_dados.append({
                "Produto": prod_row['nome'],
                "Preço": f"{prod_row['preco']:.2f} MT",
                "Quantidade": qtd,
                "Subtotal": f"{subtotal:.2f} MT"
            })
            mensagem_whatsapp += f"• {qtd}x *{prod_row['nome']}* -> *{subtotal:.2f} MT*\n"
            
        mensagem_whatsapp += "---------------------------------\n"
        mensagem_whatsapp += f"💰 *TOTAL A PAGAR:* {total_geral:.2f} MT\n\n"
        
        if metodo_pago == "M-Pesa":
            mensagem_whatsapp += f"📌 Conta M-Pesa para envio: *{mpesa_atual}*\n"
        elif metodo_pago == "e-Mola":
            mensagem_whatsapp += f"📌 Conta e-Mola para envio: *{emola_atual}*\n"
            
        st.table(pd.DataFrame(tabela_dados))
        st.markdown(f"## **Total Geral: {total_geral:.2f} MT**")
        
        texto_final = urllib.parse.quote(mensagem_whatsapp)
        st.link_button("🚀 Finalizar Encomenda via WhatsApp", f"https://wa.me{whatsapp_atual}?text={texto_final}")

# ==========================================
# ABA 2: ADMINISTRADOR (INTERFACE PLANA E DIRETA)
# ==========================================
with aba_painel:
    st.header("⚙️ Painel de Gestão e Configuração")
    
    st.markdown("### 🏬 Atualizar Contactos e Contas da Loja")
    n_nome = st.text_input("Nome de Exibição da Loja:", value=nome_loja_atual)
    n_wa = st.text_input("WhatsApp de Atendimento (ex: 258...):", value=whatsapp_atual)
    n_mpesa = st.text_input("Número M-Pesa da Loja:", value=mpesa_atual)
    n_emola = st.text_input("Número e-Mola da Loja:", value=emola_atual)
    
    if st.button("💾 Guardar Definições da Loja"):
        conn = sqlite3.connect('banco_leoprice_completo.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE configuracao SET nome_loja=?, whatsapp=?, mpesa=?, emola=? WHERE id=1', (n_nome, n_wa, n_mpesa, n_emola))
        conn.commit()
        conn.close()
        st.success("Configurações atualizadas com sucesso!")
        st.rerun()

    st.markdown("---")
    st.markdown("### ➕ Registar Novo Produto no Catálogo")
    p_nome = st.text_input("Nome do Smartphone ou Acessório:")
    p_preco = st.number_input("Preço de Venda (MT):", min_value=0.0, step=50.0)
    p_cat = st.selectbox("Categoria:", ["Smartphones", "Acessórios", "Carregadores", "Outros"])
    p_desc = st.text_area("Descrição do Item:")
    p_foto_link = st.text_input("Link da Imagem (URL da foto na internet):")
    
    if st.button("📦 Guardar e Publicar Produto"):
        if p_nome and p_preco > 0:
            conn = sqlite3.connect('banco_leoprice_completo.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO produtos (nome, preco, categoria, imagem, descricao) VALUES (?, ?, ?, ?, ?)', (p_nome, p_preco, p_cat, p_foto_link, p_desc))
            conn.commit()
            conn.close()
            st.success(f"O produto '{p_nome}' foi registado com sucesso!")
