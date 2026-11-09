import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse
import qrcode
from io import BytesIO
from PIL import Image

# 1. CONFIGURAÇÃO VISUAL DA PÁGINA
st.set_page_config(page_title="Loja Leoprice V5", page_icon="📱", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    .product-box { padding: 20px; border-radius: 12px; background-color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 25px; border: 1px solid #eef2f5; }
    .shop-header { padding: 20px; border-radius: 10px; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; margin-bottom: 25px; }
    </style>
""", unsafe_allow_html=True)

# 2. BANCO DE DADOS RECONSTRUÍDO
def iniciar_banco():
    conn = sqlite3.connect('banco_leoprice_v5.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_loja TEXT,
            whatsapp TEXT,
            mpesa TEXT,
            emola TEXT,
            facebook TEXT,
            tiktok TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL,
            categoria TEXT,
            imagem BLOB,
            descricao TEXT
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM configuracao")
    if cursor.fetchone() == 0:
        cursor.execute('''
            INSERT INTO configuracao (nome_loja, whatsapp, mpesa, emola, facebook, tiktok)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('Loja de celulares Leoprice', '258840000000', '840000000', '860000000', 'Leoprice_Facebook', 'Leoprice_TikTok'))
        
    conn.commit()
    conn.close()

iniciar_banco()

# 3. FUNÇÕES DE LEITURA
def obter_config():
    conn = sqlite3.connect('banco_leoprice_v5.db')
    df = pd.read_sql_query("SELECT * FROM configuracao LIMIT 1", conn)
    conn.close()
    return df.iloc if not df.empty else None

def carregar_produtos():
    conn = sqlite3.connect('banco_leoprice_v5.db')
    df = pd.read_sql_query("SELECT * FROM produtos", conn)
    conn.close()
    return df

# 4. CRIAÇÃO DAS ABAS PRINCIPAIS
aba_catalogo, aba_painel = st.tabs(["🛒 Catálogo de Vendas", "⚙️ Painel do Administrador"])

config = obter_config()
nome_loja_atual = config['nome_loja'] if config is not None else "Loja Leoprice"
whatsapp_atual = config['whatsapp'] if config is not None else "258840000000"

if 'carrinho' not in st.session_state:
    st.session_state.carrinho = {}

# ==========================================
# INTERFACE DO CATÁLOGO
# ==========================================
with aba_catalogo:
    st.markdown(f"""
        <div class='shop-header'>
            <h1 style='margin:0;color:white;'>🏪 {nome_loja_atual}</h1>
            <p style='margin:5px 0 0 0;color:white;'>Escolha os seus produtos e pague via M-Pesa ou e-Mola!</p>
        </div>
    """, unsafe_allow_html=True)
    
    df_produtos = carregar_produtos()
    
    # Filtros e dados do cliente no menu lateral
    st.sidebar.header("⚙️ Filtros e Dados")
    if not df_produtos.empty:
        categorias = ["Todos"] + list(df_produtos['categoria'].unique())
        cat_selecionada = st.sidebar.selectbox("Filtrar por Categoria:", categories)
        if cat_selecionada != "Todos":
            df_produtos = df_produtos[df_produtos['categoria'] == cat_selecionada]
            
    st.sidebar.markdown("---")
    nome_cliente = st.sidebar.text_input("O seu Nome:", placeholder="Ex: Leonardo Francisco")
    metodo_pago = st.sidebar.selectbox("Pagar via:", ["M-Pesa", "e-Mola", "Dinheiro"])

    if df_produtos.empty:
        st.info("Nenhum produto cadastrado. Vá à aba 'Painel do Administrador' para adicionar itens da galeria.")
    else:
        cols = st.columns(3)
        for idx, row in df_produtos.reset_index().iterrows():
            with cols[idx % 3]:
                st.markdown("<div class='product-box'>", unsafe_allow_html=True)
                
                if row['imagem']:
                    st.image(row['imagem'], use_container_width=True)
                else:
                    st.image("https://placeholder.com", use_container_width=True)
                    
                st.subheader(row['nome'])
                st.write(f"*{row['descricao']}*")
                st.markdown(f"### **{row['preco']:.2f} MT**")
                
                pid = str(row['id'])
                qtd_atual = st.session_state.carrinho.get(pid, 0)
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("➖", key=f"sub_{pid}"):
                        st.session_state.carrinho[pid] = max(0, qtd_atual - 1)
                        st.rerun()
                with c2:
                    st.markdown(f"<h4 style='text-align:center;'>{qtd_atual}</h4>", unsafe_allow_html=True)
                with c3:
                    if st.button("➕", key=f"add_{pid}"):
                        st.session_state.carrinho[pid] = qtd_atual + 1
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    # RESUMO DA COMPRA
    st.markdown("---")
    st.header("🛒 Resumo da Compra")
    
    carrinho_filtrado = {k: v for k, v in st.session_state.carrinho.items() if v > 0}
    
    if not carrinho_filtrado:
        st.info("O carrinho está vazio.")
    else:
        tabela_dados = []
        total_geral = 0.0
        
        mensagem_whatsapp = f"Olá, {nome_loja_atual}! Gostaria de fazer uma encomenda:\n\n"
        if nome_cliente:
            mensagem_whatsapp += f"👤 *Cliente:* {nome_cliente}\n"
        mensagem_whatsapp += f"💳 *Pagamento por:* {metodo_pago}\n"
        mensagem_whatsapp += "---------------------------------\n"
        
        for pid, qtd in carrinho_filtrado.items():
            prod_row = df_produtos[df_produtos['id'] == int(pid)].iloc[0]
            subtotal = prod_row['preco'] * qtd
            total_geral += subtotal
            
            tabela_dados.append({
                "Item": prod_row['nome'],
                "Preço": f"{prod_row['preco']:.2f} MT",
                "Qtd": qtd,
                "Subtotal": f"{subtotal:.2f} MT"
            })
            mensagem_whatsapp += f"• {qtd}x *{prod_row['nome']}* -> *{subtotal:.2f} MT*\n"
            
        mensagem_whatsapp += "---------------------------------\n"
        mensagem_whatsapp += f"💰 *TOTAL A PAGAR:* {total_geral:.2f} MT\n\n"
        
        if metodo_pago == "M-Pesa" and config is not None:
            mensagem_whatsapp += f"📌 Enviar para o M-Pesa: *{config['mpesa']}*\n"
        elif metodo_pago == "e-Mola" and config is not None:
            mensagem_whatsapp += f"📌 Enviar para o e-Mola: *{config['emola']}*\n"
            
        st.table(pd.DataFrame(tabela_dados))
        st.markdown(f"## **Total: {total_geral:.2f} MT**")
        
        # QR Code Gerado Automaticamente
        qr_data = f"Loja: {nome_loja_atual} | Total: {total_geral:.2f} MT | Conta: " + (config['mpesa'] if metodo_pago == "M-Pesa" else config['emola'])
        qr = qrcode.make(qr_data)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        st.image(buffer.getvalue(), caption="Aponte a câmera para pagar", width=200)
        
        texto_final = urllib.parse.quote(mensagem_whatsapp)
        st.link_button("🚀 Enviar Pedido para o WhatsApp", f"https://wa.me{whatsapp_atual}?text={texto_final}")

# ==========================================
# PAINEL ADMINISTRATIVO
# ==========================================
with aba_painel:
    st.header("⚙️ Gestão de Dados da Loja")
    
    with st.expander("🏬 Configurar Nome e Contas de Pagamento"):
        if config is not None:
            n_nome = st.text_input("Nome da Loja:", value=config['nome_loja'])
            n_wa = st.text_input("WhatsApp (ex: 258...):", value=config['whatsapp'])
            n_mpesa = st.text_input("Número M-Pesa:", value=config['mpesa'])
            n_emola = st.text_input("Número e-Mola:", value=config['emola'])
            n_fb = st.text_input("Facebook link:", value=config['facebook'])
            n_tk = st.text_input("TikTok link:", value=config['tiktok'])
            
            if st.button("Guardar Dados da Loja"):
                conn = sqlite3.connect('banco_leoprice_v5.db')
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE configuracao SET nome_loja=?, whatsapp=?, mpesa=?, emola=?, facebook=?, tiktok=? WHERE id=1
                ''', (n_nome, n_wa, n_mpesa, n_emola, n_fb, n_tk))
                conn.commit()
                conn.close()
                st.success("Dados guardados! Atualize a página.")
                st.rerun()

    with st.expander("➕ Adicionar Novo Produto (Carregar da Galeria)", expanded=True):
        p_nome = st.text_input("Nome do Produto:")
        p_preco = st.number_input("Preço (MT):", min_value=0.0, step=10.0)
        p_cat = st.selectbox("Categoria:", ["Smartphones", "Acessórios", "Outros"])
        p_desc = st.text_area("Descrição do Item:")
        p_foto = st.file_uploader("Escolha a Imagem da Galeria:", type=["jpg", "png", "jpeg"])
        
        if st.button("Cadastrar Produto"):
            if p_nome and p_preco > 0:
                bytes_foto = None
                if p_foto is not None:
                    img = Image.open(p_foto)
                    buf = BytesIO()
                    img.save(buf, format="JPEG")
                    bytes_foto = buf.getvalue()
                    
                conn = sqlite3.connect('banco_leoprice_v5.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO produtos (nome, preco, categoria, imagem, descricao)
                    VALUES (?, ?, ?, ?, ?)
