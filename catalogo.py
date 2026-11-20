import streamlit as st
import sqlite3, urllib.parse, os, time, base64, shutil
from datetime import datetime
from PIL import Image

st.set_page_config(page_title="CatÃ¡logo Multi-Lojas Pro", page_icon="ðŸ›ï¸", layout="wide")
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
        preco_grosso REAL, qtd_min_grosso INTEGER DEFAULT 6, cores TEXT DEFAULT 'PadrÃ£o',
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
                 ("loja-oficial-mz", "Vitrine Oficial MoÃ§ambique", "258879707294", "1234", "Marracuene & Maputo", "Ativa", time.time() + 365*86400))
    conn.execute("INSERT INTO produtos_catalogo (loja_slug, nome, categoria, descricao, preco_antigo, preco_un, preco_grosso, qtd_min_grosso, cores, stock, esgotado, destaque) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                 ("loja-oficial-mz", "Smartphone Android 128GB", "EletrÃ³nicos", "Novo na caixa com garantia", 9500.0, 8200.0, 7500.0, 3, "Preto, Azul, Dourado", 15, 0, 1))
    conn.commit()

with st.sidebar:
    st.title("ðŸ›ï¸ CatÃ¡logo Pro")
    lojas_rows = conn.execute("SELECT slug, nome_loja, whatsapp, senha_lojista, localizacao, horario, loja_aberta, zonas_entrega, cupom_codigo, cupom_desc, fundo_img, plano_status, expira_em FROM lojas").fetchall()
    loja_atual = None
    if lojas_rows:
        mapa = {f"{nome} (@{slug})": (slug, nome, wa, pw, loc, hor, ab, zon, cupc, cupd, fimg, st_p, exp) for (slug, nome, wa, pw, loc, hor, ab, zon, cupc, cupd, fimg, st_p, exp) in lojas_rows}
        qp_loja = st.query_params.get("loja", "")
        idx_def = 0
        for idx_k, k_txt in enumerate(mapa.keys()):
            if qp_loja and f"(@{qp_loja})" in k_txt:
                idx_def = idx_k
                break
        esc = st.selectbox("ðŸª Escolher Loja:", list(mapa.keys()), index=idx_def)
        loja_atual = mapa[esc]

    st.divider()
    with st.expander("ðŸ‘‘ Painel Mestre (Dono)"):
        if st.text_input("Senha Mestre:", type="password") == get_senha_mestre():
            st.success("Modo Mestre Ativo")
            if st.button("ðŸ’¾ Guardar Backup Total"):
                os.makedirs("Backups_Catalogo", exist_ok=True)
                shutil.copy2(DB_PATH, f"Backups_Catalogo/backup_{int(time.time())}.db")
                st.success("Backup guardado!")
            for (s_lj, n_lj, _, _, _, _, _, _, _, _, _, st_lj, exp_lj) in lojas_rows:
                dias = max(0, int((float(exp_lj) - time.time()) / 86400))
                st.write(f"**{n_lj}** - {st_lj} ({dias}d)")
                c1, c2, c3 = st.columns(3)
                if c1.button("âœ… +30d", key=f"at_{s_lj}"):
                    conn.execute("UPDATE lojas SET plano_status='Ativa', expira_em=? WHERE slug=?", (max(time.time(), float(exp_lj)) + 30*86400, s_lj))
                    conn.commit(); st.rerun()
                if c2.button("ðŸš« Bloq", key=f"bl_{s_lj}"):
                    conn.execute("UPDATE lojas SET plano_status='Bloqueada' WHERE slug=?", (s_lj,))
                    conn.commit(); st.rerun()
                if c3.button("ðŸ—‘ï¸ Del", key=f"dl_{s_lj}"):
                    conn.execute("DELETE FROM produtos_catalogo WHERE loja_slug=?", (s_lj,))
                    conn.execute("DELETE FROM lojas WHERE slug=?", (s_lj,))
                    conn.commit(); st.rerun()
            ns = st.text_input("Nova Senha Mestre:", type="password")
            if st.button("ðŸ” Alterar Senha Mestre") and len(ns.strip()) >= 4:
                with open("senha_mestre_catalogo.txt", "w", encoding="utf-8") as f: f.write(ns.strip())
                st.success("Senha alterada!")

if loja_atual:
    _, _, _, _, _, _, _, _, _, _, fundo_atual, _, _ = loja_atual
    if fundo_atual and os.path.exists(fundo_atual):
        with open(fundo_atual, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(f"<style>.stApp {{ background: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.75)), url('data:image/png;base64,{b64}') center/cover fixed; }}</style>", unsafe_allow_html=True)

t1, t2, t3, t4 = st.tabs(["ðŸ¬ Vitrine", f"ðŸ›’ Carrinho ({len(st.session_state['carrinho'])})", "â­ AvaliaÃ§Ãµes", "ðŸª Ãrea do Lojista"])

with t1:
    if loja_atual:
        sg, ng, wg, _, lg, horg, abg, zong, cupc, cupd, _, stg, expg = loja_atual
        st.subheader(f"âœ… {ng} ({'ABERTA' if abg==1 else 'FECHADA'})")
        st.caption(f"â° {horg} | ðŸ“ {lg} | Pagamento: M-Pesa / e-Mola / Cash")
        st.link_button("ðŸª Quero abrir a minha loja aqui", "https://wa.me.")
        if stg != "Ativa" or (expg > 0 and time.time() > expg):
            st.error("ðŸ”’ Loja temporariamente suspensa.")
        else:
            prods = conn.execute("SELECT id, nome, categoria, descricao, preco_antigo, preco_un, preco_grosso, qtd_min_grosso, cores, stock, esgotado, destaque, imagem_path FROM produtos_catalogo WHERE loja_slug=? ORDER BY destaque DESC, id DESC", (sg,)).fetchall()
            cols = st.columns(3)
            for i, (pid, pnome, pcat, pdesc, pant, pun, pgr, qmin, pcores, pstock, pesg, pdest, pimg) in enumerate(prods):
                with cols[i % 3]:
                    with st.container(border=True):
                        if pimg:
                            midias = [m.strip() for m in pimg.split("|") if m.strip() and os.path.exists(m.strip())]
                            fotos_p = [m for m in midias if not m.lower().endswith((".mp4", ".mov", ".webm"))]
                            videos_p = [m for m in midias if m.lower().endswith((".mp4", ".mov", ".webm"))]
                            if fotos_p:
                                st.image(fotos_p.pop(0), use_container_width=True)
                                if fotos_p:
                                    with st.expander(f"ðŸ“¸ Ver mais {len(fotos_p)} foto(s)"):
                                        for f_ex in fotos_p:
                                            st.image(f_ex, use_container_width=True)
                            for v_ex in videos_p:
                                st.video(v_ex)
                        st.markdown(f"### {pnome}")
                        st.caption(f"{pcat} | {pdesc}")
                        if pesg == 1 or pstock <= 0: st.error("ðŸš« ESGOTADO")
                        else: st.success(f"âœ… Stock: {pstock} un")
                        if pant > pun: st.markdown(f"~~{pant:,.2f} MT~~")
                        st.write(f"Retalho: **{pun:,.2f} MT** | Grosso (â‰¥{qmin}): **{pgr:,.2f} MT**")
                        cor = st.selectbox("Cor:", [c.strip() for c in pcores.split(",") if c.strip()] or ["PadrÃ£o"], key=f"c_{pid}")
                        qtd = st.number_input("Qtd:", min_value=1, max_value=max(1, int(pstock)), value=1, key=f"q_{pid}")
                        pu = pgr if qtd >= qmin else pun
                        tot = pu * qtd
                        if st.button(f"ðŸ›’ Adicionar ({tot:,.2f} MT)", key=f"add_{pid}", disabled=(pesg == 1 or pstock <= 0)):
                            st.session_state["carrinho"].append({"wa": wg, "produto": pnome, "cor": cor, "qtd": qtd, "total": tot})
                            st.rerun()

with t2:
    if not st.session_state["carrinho"]:
        st.info("O carrinho estÃ¡ vazio.")
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
        z_sel = st.selectbox("ðŸšš Zona de Entrega:", list(zonas.keys()))
        frete = zonas[z_sel]
        cup = st.text_input("ðŸŽŸï¸ CupÃ£o:").strip().upper()
        desc = tot_i * (c_dsc / 100.0) if (loja_atual and cup and cup == c_cod.strip().upper()) else 0.0
        tot_f = max(0.0, tot_i - desc) + frete
        st.metric("Total Final", f"{tot_f:,.2f} MT")
        cli = st.text_input("Seu Nome:")
        end = st.text_input("Morada / Link GPS:")
        pg = st.selectbox("Pagamento:", ["M-Pesa", "e-Mola", "Cash"])
        if st.button("ðŸ—‘ï¸ Limpar Carrinho"):
            st.session_state["carrinho"] = []; st.rerun()
        wa = "".join(filter(str.isdigit, str(wa_dest)))
        if len(wa) == 9: wa = "258" + wa
        itens_m = "\n".join([f"- {it['qtd']}x {it['produto']} ({it['cor']}): {it['total']:,.2f} MT" for it in st.session_state["carrinho"]])
        msg = f"Ola! Novo pedido:\n\n{itens_m}\n\nEntrega ({z_sel}): {frete:,.2f} MT\nTotal: {tot_f:,.2f} MT\nCliente: {cli}\nMorada: {end}\nPagamento: {pg}"
        st.link_button("ðŸ“² ENVIAR NO WHATSAPP AGORA", f"https://wa.me{wa}?text={urllib.parse.quote(msg)}")

with t3:
    if loja_atual:
        sg, _, _, _, _, _, _, _, _, _, _, _, _ = loja_atual
        na = st.text_input("Seu Nome:", key="av_n")
        es = st.selectbox("Estrelas:", list(range(5, 0, -1)), key="av_e")
        co = st.text_input("ComentÃ¡rio:", key="av_c")
        if st.button("Enviar AvaliaÃ§Ã£o") and na and co:
            conn.execute("INSERT INTO avaliacoes (loja_slug, cliente, estrelas, comentario, data) VALUES (?,?,?,?,?)", (sg, na, es, co, datetime.now().strftime("%Y-%m-%d")))
            conn.commit(); st.rerun()
        for (c_av, e_av, com_av, d_av) in conn.execute("SELECT cliente, estrelas, comentario, data FROM avaliacoes WHERE loja_slug=? ORDER BY id DESC", (sg,)).fetchall():
            st.write(f"{'â­'*int(e_av)} **{c_av}** ({d_av}): {com_av}")

with t4:
    st.subheader("ðŸª GestÃ£o da Loja")
    sub1, sub2 = st.tabs(["âš™ï¸ Gerir Minha Loja", "ðŸ†• Criar Loja (Admin)"])
    with sub1:
        if loja_atual:
            sg, ng, wg, pwg, lg, horg, abg, zong, cupc, cupd, fg_img, _, _ = loja_atual
            st.info(f"Loja: **{ng}** | Link Direto: `https://streamlit.app{sg}`")
            if st.text_input("Senha do Lojista:", type="password", key="pw_l") == pwg:
                st.success("Painel Desbloqueado!")
                fotos = st.file_uploader("ðŸ“¸ Fotos do Produto (Pode escolher vÃ¡rias):", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
                video_p = st.file_uploader("ðŸŽ¥ VÃ­deo Curto do Produto (Opcional - MP4/MOV):", type=["mp4", "mov", "webm"])
                nome_auto = os.path.splitext(fotos.name).replace("_", " ").title() if fotos else ""
                pn = st.text_input("Nome do Produto:", value=nome_auto)
                pc = st.text_input("Categoria:", value="Geral")
                pd = st.text_input("DescriÃ§Ã£o:")
                c1, c2, c3 = st.columns(3)
                pa = c1.number_input("PreÃ§o Antigo:", min_value=0.0, value=0.0)
                pu = c2.number_input("PreÃ§o Retalho (MT):", min_value=1.0, value=100.0)
                pg_v = c3.number_input("PreÃ§o Grosso (MT):", min_value=1.0, value=80.0)
                pco = st.text_input("Cores (vÃ­rgula):", value="Preto, Branco")
                pst = st.number_input("Stock:", min_value=0, value=10)
                if st.button("ðŸ’¾ Publicar Produto") and pn:
                    caminhos = []
                    if fotos:
                        for idx_f, ft in enumerate(fotos):
                            cf = os.path.join("imagens_catalogo", f"{sg}_{int(time.time())}_{idx_f}_{ft.name}")
                            with open(cf, "wb") as fo: fo.write(ft.getbuffer())
                            caminhos.append(cf)
                    if video_p:
                        cv = os.path.join("imagens_catalogo", f"{sg}_{int(time.time())}_{video_p.name}")
                        with open(cv, "wb") as fv: fv.write(video_p.getbuffer())
                        caminhos.append(cv)
                    ci = "|".join(caminhos)
                    conn.execute("INSERT INTO produtos_catalogo (loja_slug, nome, categoria, descricao, preco_antigo, preco_un, preco_grosso, cores, stock, imagem_path) VALUES (?,?,?,?,?,?,?,?,?,?)", (sg, pn, pc, pd, pa, pu, pg_v, pco, pst, ci))
                    conn.commit(); st.success("Publicado com fotos e vÃ­deo!"); st.rerun()
                st.divider()
                for (id_p, nm_p, st_p, es_p) in conn.execute("SELECT id, nome, stock, esgotado FROM produtos_catalogo WHERE loja_slug=?", (sg,)).fetchall():
                    ca, cb, cc = st.columns(3)
                    ca.write(f"**{nm_p}** ({'Esgotado' if es_p==1 else f'{st_p} un'})")
                    if cb.button("Esgotado", key=f"e_{id_p}"):
                        conn.execute("UPDATE produtos_catalogo SET esgotado=? WHERE id=?", (0 if es_p==1 else 1, id_p)); conn.commit(); st.rerun()
                    if cc.button("ðŸ—‘ï¸", key=f"d_{id_p}"):
                        conn.execute("DELETE FROM produtos_catalogo WHERE id=?", (id_p,)); conn.commit(); st.rerun()
                st.divider()
                st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://streamlit.app{sg}", caption="QR Code da Loja")
                f_bg = st.file_uploader("ðŸ–¼ï¸ Foto de Fundo da Loja:", type=["png", "jpg", "jpeg"])
                if f_bg and st.button("Aplicar Fundo"):
                    p_bg = os.path.join("imagens_catalogo", f"bg_{sg}.png")
                    with open(p_bg, "wb") as fb: fb.write(f_bg.getbuffer())
                    conn.execute("UPDATE lojas SET fundo_img=? WHERE slug=?", (p_bg, sg)); conn.commit(); st.rerun()
                npw = st.text_input("Nova Senha da Loja:", type="password")
                if st.button("Alterar Senha") and len(npw) >= 4:
                    conn.execute("UPDATE lojas SET senha_lojista=? WHERE slug=?", (npw, sg)); conn.commit(); st.success("Senha alterada!")
    with sub2:
        if st.text_input("Senha do Dono (Admin):", type="password", key="pw_adm") == get_senha_mestre():
            nn = st.text_input("Nome da Nova Loja:")
            ns = st.text_input("CÃ³digo Ãšnico:").strip().lower().replace(" ", "-")
            nw = st.text_input("WhatsApp:")
            nl = st.text_input("LocalizaÃ§Ã£o:")
            np = st.text_input("Senha Lojista:", type="password")
            if st.button("ðŸš€ Criar Loja") and nn and ns and nw and len(np) >= 4:
                conn.execute("INSERT INTO lojas (slug, nome_loja, whatsapp, senha_lojista, localizacao, plano_status, expira_em) VALUES (?,?,?,?,?,'Ativa',?)", (ns, nn, nw, np, nl, time.time() + 30*86400))
                conn.commit(); st.success("Loja criada!"); st.rerun()

st.divider()
st.caption("CatÃ¡logo Multi-Lojas Pro â€¢ Leonardo Jacinto Francisco â€¢ AdSense: ca-pub-7971514992716083 â€¢ Contacto: +258 87 970 7294")
