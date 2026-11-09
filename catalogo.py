import streamlit as st
import pandas as pd
import sqlite3
import urllib.parse
import qrcode
from io import BytesIO
from PIL import Image

# 1. CONFIGURAÇÃO DA PÁGINA E DESIGN SYSTEM
st.set_page_config(page_title="Sistema Comercial V5 Máxima", page_icon="🛍️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    .product-box { padding: 20px; border-radius: 12px; background-color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 25px; border: 1px solid #eef2f5; }
    .shop-header { padding: 20px; border-radius: 10px; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; margin-bottom: 25px; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. BANCO DE DADOS INTEGRADO (PRODUTOS, LOJAS E CONFIGURAÇÕES)
def iniciar_banco_completo():
    conn = sqlite3.connect('sistema_comercial_v5.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lojas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_loja TEXT,
            whatsapp TEXT,
            mpesa_conta TEXT,
            emola_conta TEXT,
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
    
    # Inserir dados padrão da loja se estiver vazio
    cursor.execute("SELECT COUNT(*) FROM lojas")
    if cursor.fetchone() == 0:
        cursor.execute('''
            INSERT INTO lojas (nome_loja, whatsapp, mpesa_conta, emola_conta, facebook, tiktok)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('Cellshop Leoprice', '258840000000', '841234567', '861234567', 'Cellshop_Leoprice', 'cellshop_leoprice'))
        
    conn.commit()
    conn.close()

iniciar_banco_completo()

# 3. FUNÇÕES DE SUPORTE PARA DADOS
def obter_dados_loja():
    conn = sqlite3.connect('sistema_comercial_v5.db')
    df = pd.read_sql_query("SELECT * FROM lojas LIMIT 1", conn)
    conn.close()
    return df.iloc[0] if not df.empty else None

def carregar_produtos():
    conn = sqlite3.connect('sistema_comercial_v5.db')
    df = pd.read_sql_query("SELECT * FROM produtos", conn)
    conn.close()
    return df

# 4. GESTÃO DE NAVEGAÇÃO (Abas entre Catálogo e Painel Administrador)
aba1, aba2 = st.tabs(["🛒 Catálogo da Loja", "⚙️ Painel de Gestão da Loja"])

dados_loja = obter_dados_loja()
whatsapp_loja = dados_loja['whatsapp'] if dados_loja is not None else "258840000000"
nome_loja = dados_loja['nome_loja'] if dados_loja is not None else "Minha Loja"

# Inicializar carrinho de compras no estado da sessão
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = {}

# ==========================================
# ABA 1: INTERFACE DO CATÁLOGO COMERCIAL
# ==========================================
with aba1:
    st.markdown(f"""
        <div class='shop-header'>
            <h1 style='margin:0;'>🏪 {nome_loja}</h1>
            <p style='margin:5px 0 0 0;'>Monte as suas compras e finalize diretamente pelo WhatsApp!</p>
        </div>
    """, unsafe_allow_html=True)
    
    df_prods = carregar_produtos()
    
    # Filtro Lateral de Categorias
    st.sidebar.header("🔍 Filtros de Busca")
    if not df_prods.empty:
        cats = ["Todos"] + list(df_prods['categoria'].unique())
        categoria_sel = st.sidebar.selectbox("Escolha uma categoria:", cats)
        if categoria_sel != "Todos":
            df_prods = df_prods[df_prods['categoria'] == categoria_sel]
    else:
        st.sidebar.info("Nenhum produto cadastrado no momento.")
        
    st.sidebar.markdown("---")
    st.sidebar.header("👤 Informações do Cliente")
    nome_cliente = st.sidebar.text_input("Introduza o seu Nome:", placeholder="Ex: Leonardo Francisco")
    pagamento_sel = st.sidebar.selectbox("Forma de Pagamento Desejada:", ["M-Pesa", "e-Mola", "Dinheiro"])

    if df_prods.empty:
        st.info("Nenhum produto em exibição de momento. Acesse a aba administrativa para adicionar os primeiros produtos através da sua galeria.")
    else:
        # Grelha de exibição de produtos (3 por linha)
        cols = st.columns(3)
        for idx, row in df_prods.reset_index().iterrows():
            with cols[idx % 3]:
                st.markdown("<div class='product-box'>", unsafe_allow_html=True)
                
                # Exibição de Imagem da Galeria (BLOB) ou padrão
                if row['imagem']:
                    st.image(row['imagem'], use_container_width=True)
                else:
                    st.image("https://placeholder.com", use_container_width=True)
                    
                st.subheader(row['nome'])
                st.write(f"*{row['descricao']}*")
                st.markdown(f"### **{row['preco']:.2f} MT**")
                st.caption(f"📁 Categoria: {row['categoria']}")
                
                # Controlo de quantidades interno
                pid = str(row['id'])
                qtd_atual = st.session_state.carrinho.get(pid, 0)
                
                c_menos, c_qtd, c_mais = st.columns(3)
                with c_menos:
                    if st.button("➖", key=f"btn_sub_{pid}"):
                        st.session_state.carrinho[pid] = max(0, qtd_atual - 1)
                        if st.session_state.carrinho[pid] == 0 and pid in st.session_state.carrinho:
                            del st.session_state.carrinho[pid]
                        st.rerun()
                with c_qtd:
                    st.markdown(f"<h4 style='text-align:center; margin-top:5px;'>{qtd_atual}</h4>", unsafe_allow_html=True)
                with c_mais:
                    if st.button("➕", key=f"btn_add_{pid}"):
                        st.session_state.carrinho[pid] = qtd_atual + 1
                        st.rerun()
                        
                st.markdown("</div>", unsafe_allow_html=True)

    # Resumo da Encomenda e Fecho de Carrinho
    st.markdown("---")
    st.header("🛒 Resumo da sua Encomenda")
    
    # Filtrar chaves vazias ou com valor zero
    carrinho_ativo = {k: v for k, v in st.session_state.carrinho.items() if v > 0}
    
    if not carrinho_ativo:
        st.info("O seu carrinho de compras está atualmente vazio.")
    else:
        lista_resumo = []
        total_pagar = 0.0
        
        texto_wa = f"Olá, {nome_loja}! Nova encomenda gerada pelo catálogo:\n\n"
        if nome_cliente:
            texto_wa += f"👤 *Cliente:* {nome_cliente}\n"
        texto_wa += f"💳 *Método de Pagamento Escolhido:* {pagamento_sel}\n"
        texto_wa += "-----------------------------------------\n"
        
        for pid, qtd in carrinho_ativo.items():
            info_p = df_prods[df_prods['id'] == int(pid)].iloc[0]
            sub = info_p['preco'] * qtd
            total_pagar += sub
            
            lista_resumo.append({
                "Produto": info_p['nome'],
                "Preço Unitário": f"{info_p['preco']:.2f} MT",
                "Quantidade": qtd,
                "Subtotal": f"{sub:.2f} MT"
            })
            texto_wa += f"• {qtd}x *{info_p['nome']}* -> *{sub:.2f} MT*\n"
            
        texto_wa += "-----------------------------------------\n"
        texto_wa += f"💰 *VALOR TOTAL:* {total_pagar:.2f} MT\n\n"
        
        if pagamento_sel == "M-Pesa" and dados_loja is not None:
            texto_wa += f"📌 Por favor envie o valor para a conta M-Pesa: *{dados_loja['mpesa_conta']}*\n"
        elif pagamento_sel == "e-Mola" and dados_loja is not None:
            texto_wa += f"📌 Por favor envie o valor para a conta e-Mola: *{dados_loja['emola_conta']}*\n"
            
        st.table(pd.DataFrame(lista_resumo))
        st.markdown(f"## **Total Final: {total_pagar:.2f} MT**")
        
        # Geração dinâmica do QR Code de Pagamento
        st.markdown("### 📱 QR Code para Pagamento Rápido")
        info_qr = f"Pagamento para {nome_loja}. Total: {total_pagar:.2f} MT. Conta: " + (dados_loja['mpesa_conta'] if pagamento_sel == "M-Pesa" else dados_loja['emola_conta'])
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(info_qr)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        
        buf = BytesIO()
        img_qr.save(buf, format="PNG")
        st.image(buf.getvalue(), caption="Aponte a câmera para validar os dados da transferência móvel.", width=250)
        
        texto_codificado = urllib.parse.quote(texto_wa)
        st.link_button("🚀 Concluir Pedido e Enviar via WhatsApp", f"https://wa.me{whatsapp_loja}?text={texto_codificado}")

# ==========================================
# ABA 2: PAINEL ADMINISTRATIVO (GESTÃO DA LOJA)
# ==========================================
with aba2:
    st.header("⚙️ Painel de Configurações Administrativas")
    
    # 1. Configurações de Identidade da Loja e Contas Móveis
    with st.expander("🏬 Editar Dados da Loja e Contas de Pagamento", expanded=False):
        if dados_loja is not None:
            novo_nome = st.text_input("Nome Comercial da Loja:", value=dados_loja['nome_loja'])
            novo_wa = st.text_input("Contacto de WhatsApp (Com código do país, ex: 258...):", value=dados_loja['whatsapp'])
            novo_mpesa = st.text_input("Número de Conta M-Pesa para Recebimento:", value=dados_loja['mpesa_conta'])
            novo_emola = st.text_input("Número de Conta e-Mola para Recebimento:", value=dados_loja['emola_conta'])
            novo_fb = st.text_input("Link do Facebook da Loja:", value=dados_loja['facebook'])
            novo_tk = st.text_input("Link do TikTok da Loja:", value=dados_loja['tiktok'])
            
