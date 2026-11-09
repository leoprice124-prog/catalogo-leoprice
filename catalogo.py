import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse
import base64

# 1. CONFIGURAÇÃO VISUAL DA PÁGINA
st.set_page_config(page_title="Sistema Comercial Leoprice", page_icon="📱", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    .product-box { padding: 20px; border-radius: 12px; background-color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 25px; border: 1px solid #eef2f5; }
    .shop-header { padding: 20px; border-radius: 10px; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; margin-bottom: 25px; }
    </style>
""", unsafe_allow_html=True)

# 2. BANCO DE DADOS INTEGRADO (LOJAS COM LOCALIZAÇÃO E PRODUTOS)
def iniciar_banco():
    conn = sqlite3.connect('banco_leoprice_sistema_v5.db')
    cursor = conn.cursor()
    
    # Criar a tabela de lojas incluindo o campo de localização
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lojas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_loja TEXT UNIQUE,
            whatsapp TEXT,
            mpesa TEXT,
            emola TEXT,
            localizacao TEXT
        )
    ''')
    
    # Verificar se a coluna localizacao existe (caso a tabela já tenha sido criada antes)
    try:
        cursor.execute("ALTER TABLE lojas ADD COLUMN localizacao TEXT")
    except sqlite3.OperationalError:
        pass  # A coluna já existe
        
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loja_id INTEGER,
            nome TEXT NOT NULL,
            preco REAL,
            categoria TEXT,
            imagem_base64 TEXT,
            descricao TEXT,
            FOREIGN KEY (loja_id) REFERENCES lojas(id)
        )
    ''')
    
    # Criar a loja padrão se não existir nenhuma
    cursor.execute("SELECT COUNT(*) FROM lojas")
    if cursor.fetchone() == 0:
        cursor.execute('''
            INSERT INTO lojas (nome_loja, whatsapp, mpesa, emola, localizacao)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Cellshop Leoprice', '258840000000', '840000000', '860000000', 'Maputo, Moçambique'))
        loja_id = cursor.lastrowid
        
        # Inserir produtos de demonstração iniciais
        produtos_inicial = [
            (loja_id, 'Samsung Galaxy A32', 15000.0, 'Smartphones', '', '128GB Armazenamento, 4GB RAM.'),
            (loja_id, 'Película de Vidro 3D', 250.0, 'Acessórios', '', 'Proteção contra quedas.'),
            (loja_id, 'Capa Antichoque', 450.0, 'Acessórios', '', 'Silicone reforçado.')
        ]
        cursor.executemany('INSERT INTO produtos (loja_id, nome, preco, categoria, imagem_base64, descricao) VALUES (?, ?, ?, ?, ?, ?)', produtos_inicial)
        
    conn.commit()
    conn.close()

iniciar_banco()

# 3. FUNÇÕES DE ACESSO AOS DADOS
def listar_lojas():
    conn = sqlite3.connect('banco_leoprice_sistema_v5.db')
    df = pd.read_sql_query("SELECT * FROM lojas", conn)
    conn.close()
    return df

def carregar_produtos_loja(loja_id):
    conn = sqlite3.connect('banco_leoprice_sistema_v5.db')
    df = pd.read_sql_query("SELECT * FROM produtos WHERE loja_id = ?", conn, params=(int(loja_id),))
    conn.close()
    return df

# 4. GESTÃO E ALTERNÂNCIA DE LOJAS ATIVAS
df_lojas_todas = listar_lojas()
st.sidebar.header("🏪 Seleção de Estabelecimento")
loja_selecionada_nome = st.sidebar.selectbox("Aceder à Loja:", df_lojas_todas['nome_loja'].tolist())

# Obter dados da loja ativa selecionada
loja_dados = df_lojas_todas[df_lojas_todas['nome_loja'] == loja_selecionada_nome].iloc
loja_id_atual = int(loja_dados['id'])
nome_loja_atual = loja_dados['nome_loja']
whatsapp_atual = loja_dados['whatsapp']
mpesa_atual = loja_dados['mpesa']
emola_atual = loja_dados['emola']
localizacao_atual = loja_dados['localizacao'] if 'localizacao' in loja_dados and loja_dados['localizacao'] else "Não informada"

# Inicializar o carrinho de compras se necessário
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = {}

# 5. CONTROLO DE NAVEGAÇÃO POR ABAS
aba_catalogo, aba_painel = st.tabs(["🛒 Catálogo Comercial (Clientes)", "🔒 Painel de Gestão Comercial"])

# ==========================================
# ABA 1: RENDERIZAÇÃO DO CATÁLOGO PARA CLIENTES
# ==========================================
with aba_catalogo:
    st.markdown(f"""
        <div class='shop-header'>
            <h1 style='margin:0;color:white;'>🏪 {nome_loja_atual}</h1>
            <p style='margin:5px 0 0 0;color:white;'>📍 <b>Localização:</b> {localizacao_atual}</p>
            <p style='margin:5px 0 0 0;color:white;'>Monte as suas compras e envie o pedido diretamente para o WhatsApp da loja!</p>
        </div>
    """, unsafe_allow_html=True)
    
    df_produtos = carregar_produtos_loja(loja_id_atual)
    
    # Painel lateral do cliente
    st.sidebar.markdown("---")
    st.sidebar.header("👤 Dados de Envio da Encomenda")
    nome_cliente = st.sidebar.text_input("O seu Nome:", placeholder="Ex: Leonardo Francisco")
    metodo_pago = st.sidebar.selectbox("Efetuar Pagamento por:", ["M-Pesa", "e-Mola", "Dinheiro"])
    
    if not df_produtos.empty:
        st.sidebar.markdown("---")
        st.sidebar.header("🔍 Filtrar Itens")
        categorias = ["Todos"] + list(df_produtos['categoria'].unique())
        cat_selecionada = st.sidebar.selectbox("Escolha a categoria:", categories)
        if cat_selecionada != "Todos":
            df_produtos = df_produtos[df_produtos['categoria'] == cat_selecionada]

    if df_produtos.empty:
        st.info("De momento, esta loja não tem produtos cadastrados no catálogo.")
    else:
        cols = st.columns(3)
        for idx, row in df_produtos.reset_index().iterrows():
            with cols[idx % 3]:
                st.markdown("<div class='product-box'>", unsafe_allow_html=True)
                
                # Exibição inteligente da imagem da galeria (Base64)
                if row['imagem_base64'] and row['imagem_base64'] != "":
                    try:
                        st.image(base64.b64decode(row['imagem_base64']), use_container_width=True)
                    except:
                        st.image("https://placeholder.com", use_container_width=True)
                else:
                    st.image("https://placeholder.com", use_container_width=True)
                    
                st.subheader(row['nome'])
                st.write(f"*{row['descricao']}*")
                st.markdown(f"### **{row['preco']:.2f} MT**")
                st.caption(f"📁 Categoria: {row['categoria']}")
                
                pid = str(row['id'])
                qtd_atual = st.session_state.carrinho.get(pid, 0)
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    # CORREÇÃO VISUAL: Alterado de '模' de volta para o sinal de menos nativo '➖'
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

    # FINALIZAÇÃO DA COMPRA (CARRINHO DE COMPRAS)
    st.markdown("---")
    st.header("🛒 Carrinho de Compras Atual")
    
    carrinho_filtrado = {k: v for k, v in st.session_state.carrinho.items() if v > 0}
    
    if not carrinho_filtrado:
        st.info("O carrinho está vazio. Escolha os itens nos botões ➕ acima.")
    else:
        tabela_dados = []
        total_geral = 0.0
        
        mensagem_whatsapp = f"Olá, {nome_loja_atual}! Gostaria de fechar esta encomenda:\n\n"
        if nome_cliente:
            mensagem_whatsapp += f"👤 *Cliente:* {nome_cliente}\n"
        mensagem_whatsapp += f"💳 *Forma de Pagamento:* {metodo_pago}\n"
        mensagem_whatsapp += f"📍 *Loja Escolhida:* {nome_loja_atual} ({localizacao_atual})\n"
        mensagem_whatsapp += "---------------------------------\n"
        
        df_completo_fecha = carregar_produtos_loja(loja_id_atual)
        for pid, qtd in carrinho_filtrado.items():
            linhas_alvo = df_completo_fecha[df_completo_fecha['id'] == int(pid)]
            if not linhas_alvo.empty:
                prod_row = linhas_alvo.iloc
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
        mensagem_whatsapp += f"💰 *TOTAL DO PEDIDO:* {total_geral:.2f} MT\n\n"
        
        if metodo_pago == "M-Pesa":
            mensagem_whatsapp += f"📌 Enviar valor para M-Pesa: *{mpesa_atual}*\n"
        elif metodo_pago == "e-Mola":
            mensagem_whatsapp += f"📌 Enviar valor para e-Mola: *{emola_atual}*\n"
            
        st.table(pd.DataFrame(tabela_dados))
        st.markdown(f"## **Total Líquido: {total_geral:.2f} MT**")
        
        texto_final = urllib.parse.quote(mensagem_whatsapp)
        st.link_button("🚀 Enviar Encomenda Pronta para o WhatsApp", f"https://wa.me{whatsapp_atual}?text={texto_final}")

# ==========================================
# ABA 2: PAINEL ADMINISTRATIVO COM PROTEÇÃO DE SENHA
# ==========================================
with aba_painel:
    st.header("🔒 Acesso Restrito ao Administrador")
    
