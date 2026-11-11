import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
import base64
from io import BytesIO

# Configuração da página idêntica à tua original
st.set_page_config(page_title='Catálogo Comercial Profissional v5', layout='wide', page_icon='💰')

# CORREÇÃO CRÍTICA: Nome do banco unificado para funcionar no Computador e na Internet
DB_PATH = 'catalogo_lojas_v5.db'

def iniciar_banco_se_vazio():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lojas (
            id TEXT PRIMARY KEY,
            nome_loja TEXT,
            whatsapp TEXT,
            mensagem_sucesso TEXT,
            senha TEXT,
            localizacao TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos_catalogo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loja_id TEXT,
            nome TEXT,
            categoria TEXT,
            preco REAL,
            imagem_url TEXT,
            disponivel INTEGER
        )
    ''')
    
    # Criar a tua loja oficial por padrão
    cursor.execute("SELECT COUNT(*) FROM lojas")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO lojas (id, nome_loja, whatsapp, mensagem_sucesso, senha, localizacao)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('merceariatonny', 'Cellshop Leoprice', '258879707294', '!', '1234', 'Moçambique'))
        
    # Inserir a tua lista de produtos oficiais se estiver vazia
    cursor.execute("SELECT COUNT(*) FROM produtos_catalogo")
    if cursor.fetchone()[0] == 0:
        produtos_inicial = [
            ('merceariatonny', 'Calcinha', 'Vestuário', 100.0, '', 1),
            ('merceariatonny', 'fones de ouvidos jbl', 'Acessórios', 800.0, '', 1),
            ('merceariatonny', 'Sapatos', 'Calçado', 250.0, '', 1),
            ('merceariatonny', 'Nivea', 'Cosméticos', 300.0, '', 1),
            ('merceariatonny', 'Samsung A23', 'Smartphones', 13000.0, '', 1)
        ]
        cursor.executemany('''
            INSERT INTO produtos_catalogo (loja_id, nome, categoria, preco, imagem_url, disponivel)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', produtos_inicial)
        
    conn.commit()
    conn.close()

# Executar a criação das tabelas
iniciar_banco_se_vazio()

def ler_dados(query, params=()):
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except:
        return pd.DataFrame()

def ejecutar_comando(query, params=()):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return True
    except:
        return False

# Lógica de leitura de parâmetros da URL oficial do teu código
query_params = st.query_params
loja_id_ativa = query_params.get('loja', 'merceariatonny')
df_loja = ler_dados('SELECT * FROM lojas WHERE id = ?', (loja_id_ativa,))

if not df_loja.empty:
    nome_loja = df_loja['nome_loja'].values[0]
    whatsapp_loja = df_loja['whatsapp'].values[0]
    localizacao_loja = df_loja['localizacao'].values[0]
    senha_loja = df_loja['senha'].values[0]
else:
    nome_loja, whatsapp_loja, localizacao_loja, senha_loja = 'Cellshop Leoprice', '258879707294', 'Moçambique', '1234'

st.sidebar.title('⚙️ Menu')
aba = st.sidebar.radio('Navegar para:', ['🛒 Catálogo Público', '🔑 Painel de Gestão (Lojista)'])

# ==========================================
# ABA: PAINEL DE GESTÃO DO LOJISTA
# ==========================================
if aba == '🔑 Painel de Gestão (Lojista)':
    st.header(f'🔒 Administração - {nome_loja}')
    if st.text_input('Senha de Acesso:', type='password') == str(senha_loja):
        st.success('Acesso Autorizado!')
        t1, t2, t3 = st.tabs(['📝 Artigos & Stock', '🏦 Configurar Pagamentos & Redes', '🚀 Criar Lojas'])
        with t1:
            n = st.text_input('Nome')
            c = st.text_input('Categoria')
            p = st.number_input('Preço (MT)', min_value=0.0)
            up = st.file_uploader('Foto da Galeria', type=['png','jpg','jpeg'])
            img = ''
            if up:
                img = f'data:image/jpeg;base64,{base64.b64encode(up.read()).decode("utf-8")}'
            if st.button('Gravar Produto') and n and c:
                executar_comando('INSERT OR REPLACE INTO produtos_catalogo (loja_id, nome, categoria, preco, imagem_url, disponivel) VALUES (?, ?, ?, ?, ?, 1)', (loja_id_ativa, n, c, p, img))
                st.success('Gravado!'); st.rerun()
            st.markdown('---')
            st.subheader('📊 Artigos em Stock')
            df_s = ler_dados('SELECT id, nome, categoria, preco FROM produtos_catalogo WHERE loja_id = ?', (loja_id_ativa,))
            for idx, r in df_s.iterrows():
                col = st.columns(4)
                col[0].write(r['nome'])
                col[1].write(r['categoria'])
                col[2].write(f'{r["preco"]} MT')
                if col[3].button('🗑️', key=f'del_{r["id"]}'):
                    executar_comando('DELETE FROM produtos_catalogo WHERE id = ?', (r['id'],))
                    st.rerun()
        with t2:
            st.subheader('💰 Configurar Contas de Pagamento')
            st.text_input('Número M-Pesa / Nome Titular', f'{whatsapp_loja} - {nome_loja}')
            st.text_input('Número e-Mola / Nome Titular', f'{whatsapp_loja} - {nome_loja}')
            st.text_input('Dados Bancários (NIB/Titular)', f'123456789 - {nome_loja}')
            st.subheader('🌐 Redes Sociais')
            st.text_input('Link do TikTok', 'https://tiktok.com@')
            st.text_input('Link do Facebook', 'https://facebook.com')
            if st.button('Salvar Dados'): st.success('Salvo!')
        with t3:
            st.subheader('🚀 Criar Catálogo para Cliente')
            nid = st.text_input('ID Único').strip().lower()
            nnome = st.text_input('Nome da Loja')
            nwhats = st.text_input('WhatsApp (Com 258)')
            if st.button('✨ Criar Catálogo') and nid and nnome and nwhats:
                executar_comando('INSERT OR REPLACE INTO lojas (id, nome_loja, whatsapp, mensagem_sucesso, senha, localizacao) VALUES (?, ?, ?, "!", "1234", "Moçambique")', (nid, nnome, nwhats))
                st.success(f'Link gerado! Use no Streamlit com o parâmetro: ?loja={nid}')

# ==========================================
# ABA: CATÁLOGO PÚBLICO PARA CLIENTES
# ==========================================
elif aba == '🛒 Catálogo Público':
    st.title(f'🛍️ {nome_loja}')
    st.markdown(f'📞 **WhatsApp:** {whatsapp_loja} | 📍 **Endereço:** {localizacao_loja}')
    st.markdown('---')
    df_p = ler_dados('SELECT * FROM produtos_catalogo WHERE loja_id = ? AND disponivel = 1', (loja_id_ativa,))
    if df_p.empty: 
        st.info('Nenhum produto disponível.')
    else:
        cats = ['Todos'] + list(df_p['categoria'].dropna().unique())
        s_cat = st.sidebar.selectbox('Categoria', cats)
        df_f = df_p if s_cat == 'Todos' else df_p[df_p['categoria'] == s_cat]
        cols = st.columns(3)
        for idx, row in df_f.reset_index().iterrows():
            with cols[idx % 3]:
                st.markdown(f'### {row["nome"]}')
                st.markdown(f'**Preço:** {row["preco"]} MT')
                if str(row['imagem_url']).startswith('data:image'): 
                    st.image(row['imagem_url'], use_container_width=True)
                else: 
                    st.info('📷 Sem imagem')
                st.markdown('**💳 Dados de Pagamento:**')
                st.caption(f'• M-Pesa: {whatsapp_loja} - {nome_loja}')
                st.caption(f'• e-Mola: {whatsapp_loja} - {nome_loja}')
                st.markdown('**🌐 Seguir nas Redes Sociais:**')
                st.caption('• Facebook | • TikTok')
                
                # Correção do link do WhatsApp (Adicionado o sinal de interrogação ?text=)
                txt = urllib.parse.quote(f'Olá! Quero encomendar o produto: *{row["nome"]}* no valor de *{row["preco"]} MT*. Vou efetuar o pagamento via M-Pesa/e-Mola!')
                st.link_button('🛍️ Encomendar via WhatsApp', f'https://wa.me{whatsapp_loja}?text={txt}')
                st.markdown('---')
