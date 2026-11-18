import streamlit as st
import sqlite3, urllib.parse, os, time, base64, shutil
from datetime import datetime
from PIL import Image

st.set_page_config(page_title="Catálogo Multi-Lojas Pro", page_icon="🛍️", layout="wide")
DB_PATH = "catalogo_vendas_v3.db"

def get_senha_mestre():
    if os.path.exists("senha_mestre_catalogo.txt"):
        with open("senha_mestre_catalogo.txt", "r", encoding="utf-8") as f:
            s = f.read().strip()
            if s: return s
    return "fracisco2003"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS lojas (
        slug TEXT PRIMARY KEY, nome_loja TEXT, whatsapp TEXT, senha_lojista TEXT,
        localizacao TEXT DEFAULT '', horario TEXT DEFAULT '08:00 - 18:00',
        loja_aberta INTEGER DEFAULT 1, zonas_entrega TEXT DEFAULT 'Levantar na Loja:0, Marracuene:100, Maputo:250',
        cupom_codigo TEXT DEFAULT '', cupom_desc INTEGER DEFAULT 0, fundo_img TEXT DEFAULT '',
        plano_status TEXT DEFAULT 'Ativa', expira_em REAL DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS produtos_catalogo (
        id INTEGER PRIMARY KEY AUTOINCREMENT, loja_slug TEXT, nome TEXT, categoria TEXT,
        descricao TEXT DEFAULT '', preco_antigo REAL DEFAULT 0, preco_un REAL,
        preco_grosso REAL, qtd_min_grosso INTEGER DEFAULT 6, cores TEXT DEFAULT 'Padrão',
        stock INTEGER DEFAULT 10, esgotado INTEGER DEFAULT 0, destaque INTEGER DEFAULT 0, imagem_path TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS avaliacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, loja_slug TEXT, cliente TEXT,
        estrelas INTEGER DEFAULT 5, comentario TEXT, data TEXT
    )""")
    conn.commit()
    return conn

conn = get_conn()
os.makedirs("imagens_catalogo", exist_ok=True)
if "carrinho" not in st.session_state: st.session_state["carrinho"] = []

qtd_lojas, = conn.execute("SELECT COUNT(*) FROM lojas").fetchone()
if qtd_lojas == 0:
    conn.execute("INSERT INTO lojas (slug, nome_loja, whatsapp, senha_lojista, localizacao, plano_status, expira_em) VALUES (?,?,?,?,?,?,?)",
                 ("loja-oficial-mz", "Vitrine Oficial Moçambique", "258879707294", "1234", "Marracuene & Maputo", "Ativa", time.time() + 365*86400))
    conn.execute("INSERT INTO produtos_catalogo (loja_slug, nome, categoria, descricao, preco_antigo, preco_un, preco_grosso, qtd_min_grosso, cores, stock, esgotado, destaque) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                 ("loja-oficial-mz", "Smartphone Android 128GB", "Eletrónicos", "Novo na caixa com garantia", 9500.0, 8200.0, 7500.0, 3, "Preto, Azul, Dourado", 15, 0, 1))
    conn.commit()

with st.sidebar:
    st.title("🛍️ Catálogo Pro")
    lojas_rows = conn.execute("SELECT slug, nome_loja, whatsapp, senha_lojista, localizacao, horario, loja_aberta, zonas_entrega, cupom_codigo, cupom_desc, fundo_img, plano_status, expira_em FROM lojas").fetchall()
    loja_atual = None
    if lojas_rows:
        mapa = {f"{nome} (@{slug})": (slug, nome, wa, pw, loc, hor, ab, zon, cupc, cupd, fimg, st_p, exp) for (slug, nome, wa, pw, loc, hor, ab, zon, cupc, cupd, fimg, st_p, exp) in lojas_rows}
        esc = st.selectbox("🏪 Escolher Loja:", list(mapa.keys()))
        loja_atual = mapa[esc]

    st.divider()
    with st.expander("👑 Painel Mestre (Dono)"):
        if st.text_input("Senha Mestre:", type="password") == get_senha_mestre():
            st.success("Modo Mestre Ativo")
            if st.button("💾 Guardar Backup Total"):
                os.makedirs("Backups_Catalogo", exist_ok=True)
                shutil.copy2(DB_PATH, f"Backups_Catalogo/backup_{int(time.time())}.db")
                st.success("Backup guardado!")
            for (s_lj, n_lj, _, _, _, _, _, _, _, _, _, st_lj, exp_lj) in lojas_rows:
                dias = max(0, int((float(exp_lj) - time.time()) / 86400))
                st.write(f"**{n_lj}** - {st_lj} ({dias}d)")
                c1, c2, c3 = st.columns(3)
                if c1.button("✅ +30d", key=f"at_{s_lj}"):
                    conn.execute("UPDATE lojas SET plano_status='Ativa', expira_em=? WHERE slug=?", (max(time.time(), float(exp_lj)) + 30*86400, s_lj))
                    conn.commit(); st.rerun()
                if c2.button("🚫 Bloq", key=f"bl_{s_lj}"):
                    conn.execute("UPDATE lojas SET plano_status='Bloqueada' WHERE slug=?", (s_lj,))
                    conn.commit(); st.rerun()
                if c3.button("🗑️ Del", key=f"dl_{s_lj}"):
                    conn.execute("DELETE FROM produtos_catalogo WHERE loja_slug=?", (s_lj,))
                    conn.execute("DELETE FROM lojas WHERE slug=?", (s_lj,))
                    conn.commit(); st.rerun()
            ns = st.text_input("Nova Senha Mestre:", type="password")
            if st.button("🔐 Alterar Senha Mestre") and len(ns.strip()) >= 4:
                with open("senha_mestre_catalogo.txt", "w", encoding="utf-8") as f: f.write(ns.strip())
                st.success("Senha alterada!")

if loja_atual:
    _, _, _, _, _, _, _, _, _, _, fundo_atual, _, _ = loja_atual
    if fundo_atual and os.path.exists(fundo_atual):
        with open(fundo_atual, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(f"<style>.stApp {{ background: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.75)), url('data:image/png;base64,{b64}') center/cover fixed; }}</style>", unsafe_allow_html=True)

t1, t2, t3, t4 = st.tabs(["🏬 Vitrine", f"🛒 Carrinho ({len(st.session_state['carrinho'])})", "⭐ Avaliações", "🏪 Área do Lojista"])

with t1:
    if loja_atual:
        sg, ng, wg, _, lg, horg, abg, zong, cupc, cupd, _, stg, expg = loja_atual
        st.subheader(f"✅ {ng} ({'ABERTA' if abg==1 else 'FECHADA'})")
        st.caption(f"⏰ {horg} | 📍 {lg} | Pagamento: M-Pesa / e-Mola / Cash")
        st.link_button("🏪 Quero abrir a minha loja aqui", "https://wa.me.")
        if stg != "Ativa" or (expg > 0 and time.time() > expg):
            st.error("🔒 Loja temporariamente suspensa.")
        else:
            prods = conn.execute("SELECT id, nome, categoria, descricao, preco_antigo, preco_un, preco_grosso, qtd_min_grosso, cores, stock, esgotado, destaque, imagem_path FROM produtos_catalogo WHERE loja_slug=? ORDER BY destaque DESC, id DESC", (sg,)).fetchall()
            cols = st.columns(3)
            for i, (pid, pnome, pcat, pdesc, pant, pun, pgr, qmin, pcores, pstock, pesg, pdest, pimg) in enumerate(prods):
                with cols[i % 3]:
                    with st.container(border=True):
                        if pimg and os.path.exists(pimg): st.image(pimg, use_container_width=True)
                        st.markdown(f"### {pnome}")
                        st.caption(f"{pcat} | {pdesc}")
                        if pesg == 1 or pstock <= 0: st.error("🚫 ESGOTADO")
                        else: st.success(f"✅ Stock: {pstock} un")
                        if pant > pun: st.markdown(f"~~{pant:,.2f} MT~~")
                        st.write(f"Retalho: **{pun:,.2f} MT** | Grosso (≥{qmin}): **{pgr:,.2f} MT**")
                        cor = st.selectbox("Cor:", [c.strip() for c in pcores.split(",") if c.strip()] or ["Padrão"], key=f"c_{pid}")
                        qtd = st.number_input("Qtd:", min_value=1, max_value=max(1, int(pstock)), value=1, key=f"q_{pid}")
                        pu = pgr if qtd >= qmin else pun
                        tot = pu * qtd
                        if st.button(f"🛒 Adicionar ({tot:,.2f} MT)", key=f"add_{pid}", disabled=(pesg == 1 or pstock <= 0)):
                            st.session_state["carrinho"].append({"wa": wg, "produto": pnome, "cor": cor, "qtd": qtd, "total": tot})
                            st.rerun()

with t2:
    if not st.session_state["carrinho"]:
        st.info("O carrinho está vazio.")
    else:
        tot_i = sum(it["total"] for it in st.session_state["carrinho"])
        wa_dest = ""
        for it in st.session_state["carrinho"]:
            wa_dest = it["wa"]
            st.write(f"- {it['qtd']}x **{it['produto']}** ({it['cor']}): {it['total']:,.2f} MT")
        zonas = {"Levantar na Loja": 0.0}
        if loja_atual:
            _, _, _, _, _, _, _, z_str, c_cod, c_dsc, _, _, _ = loja_atual
            for z in z_str.split(","):
                if ":" in z:
                    k, v = z.split(":", 1)
                    try: zonas[k.strip()] = float(v.strip())
                    except: pass
        z_sel = st.selectbox("🚚 Zona de Entrega:", list(zonas.keys()))
        frete = zonas[z_sel]
        cup = st.text_input("🎟️ Cupão:").strip().upper()
        desc = tot_i * (c_dsc / 100.0) if (loja_atual and cup and cup == c_cod.strip().upper()) else 0.0
        tot_f = max(0.0, tot_i - desc) + frete
        st.metric("Total Final", f"{tot_f:,.2f} MT")
        cli = st.text_input("Seu Nome:")
        end = st.text_input("Morada / Link GPS:")
        pg = st.selectbox("Pagamento:", ["M-Pesa", "e-Mola", "Cash"])
        if st.button("🗑️ Limpar Carrinho"):
            st.session_state["carrinho"] = []; st.rerun()
        wa = "".join(filter(str.isdigit, str(wa_dest)))
        if len(wa) == 9: wa = "258" + wa
        itens_m = "\n".join([f"- {it['qtd']}x {it['produto']} ({it['cor']}): {it['total']:,.2f} MT" for it in st.session_state["carrinho"]])
        msg = f"Ola! Novo pedido:\n\n{itens_m}\n\nEntrega ({z_sel}): {frete:,.2f} MT\nTotal: {tot_f:,.2f} MT\nCliente: {cli}\nMorada: {end}\nPagamento: {pg}"
        st.link_button("📲 ENVIAR NO WHATSAPP AGORA", f"https://wa.me{wa}?text={urllib.parse.quote(msg)}")

with t3:
    if loja_atual:
        sg, _, _, _, _, _, _, _, _, _, _, _, _ = loja_atual
        na = st.text_input("Seu Nome:", key="av_n")
        es = st.selectbox("Estrelas:", list(range(5, 0, -1)), key="av_e")
        co = st.text_input("Comentário:", key="av_c")
        if st.button("Enviar Avaliação") and na and co:
