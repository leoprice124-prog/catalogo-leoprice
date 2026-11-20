import streamlit as st
import sqlite3, urllib.parse, os, time, base64, shutil
from datetime import datetime
from PIL import Image

st.set_page_config(page_title="Catálogo Multi-Lojas Pro", page_icon="🛍️", layout="wide")
DB_PATH = "catalogo_vendas_v3.db"

TEXTOS = {
    "🇵🇹 Português": {
        "loja": "🏪 Escolher Loja:",
        "mestre": "👑 Painel Mestre (Dono)",
        "senha_m": "Senha Mestre:",
        "tabs": ["🏬 Vitrine", "🛒 Carrinho", "⭐ Avaliações", "🏪 Área do Lojista"],
        "aberta": "ABERTA",
        "fechada": "FECHADA",
        "pag": "Pagamento: M-Pesa / e-Mola / Cash",
        "abrir_btn": "🏪 Quero abrir a minha loja aqui",
        "suspensa": "🔒 Loja temporariamente suspensa.",
        "esgotado": "🚫 ESGOTADO",
        "stock": "✅ Stock:",
        "retalho": "Retalho:",
        "grosso": "Grosso",
        "cor": "Cor:",
        "qtd": "Qtd:",
        "add": "🛒 Adicionar",
        "vazio": "O carrinho está vazio.",
        "zona": "🚚 Zona de Entrega:",
        "cupao": "🎟️ Cupão:",
        "total": "Total Final",
        "nome": "Seu Nome:",
        "morada": "Morada / Link GPS:",
        "forma_pg": "Pagamento:",
        "limpar": "🗑️ Limpar Carrinho",
        "enviar_wa": "📲 ENVIAR NO WHATSAPP AGORA",
        "estrelas": "Estrelas:",
        "coment": "Comentário:",
        "env_av": "Enviar Avaliação",
        "gestao": "🏪 Gestão da Loja",
        "sub_tabs": ["⚙️ Gerir Minha Loja", "🆕 Criar Loja (Admin)"],
        "senha_l": "Senha do Lojista:",
        "fotos": "📸 Fotos do Produto (Pode escolher várias):",
        "video": "🎥 Vídeo Curto do Produto (MP4/MOV):",
        "publicar": "💾 Publicar Produto"
    },
    "🇬🇧 English": {
        "loja": "🏪 Select Store:",
        "mestre": "👑 Master Panel (Owner)",
        "senha_m": "Master Password:",
        "tabs": ["🏬 Storefront", "🛒 Cart", "⭐ Reviews", "🏪 Merchant Area"],
        "aberta": "OPEN",
        "fechada": "CLOSED",
        "pag": "Payment: M-Pesa / e-Mola / Cash",
        "abrir_btn": "🏪 I want to open my store here",
        "suspensa": "🔒 Store temporarily suspended.",
        "esgotado": "🚫 OUT OF STOCK",
        "stock": "✅ In Stock:",
        "retalho": "Retail:",
        "grosso": "Wholesale",
        "cor": "Color:",
        "qtd": "Qty:",
        "add": "🛒 Add to Cart",
        "vazio": "Your cart is empty.",
        "zona": "🚚 Delivery Zone:",
        "cupao": "🎟️ Promo Code:",
        "total": "Final Total",
        "nome": "Your Name:",
        "morada": "Address / GPS Link:",
        "forma_pg": "Payment Method:",
        "limpar": "🗑️ Clear Cart",
        "enviar_wa": "📲 ORDER ON WHATSAPP NOW",
        "estrelas": "Rating:",
        "coment": "Review:",
        "env_av": "Submit Review",
        "gestao": "🏪 Store Management",
        "sub_tabs": ["⚙️ Manage My Store", "🆕 Create Store (Admin)"],
        "senha_l": "Merchant Password:",
        "fotos": "📸 Product Photos (Multiple allowed):",
        "video": "🎥 Short Product Video (MP4/MOV):",
        "publicar": "💾 Publish Product"
    },
    "🇪🇸 Español": {
        "loja": "🏪 Elegir Tienda:",
        "mestre": "👑 Panel Maestro (Dueño)",
        "senha_m": "Contraseña Maestra:",
        "tabs": ["🏬 Vitrina", "🛒 Carrito", "⭐ Reseñas", "🏪 Área del Comerciante"],
        "aberta": "ABIERTA",
        "fechada": "CERRADA",
        "pag": "Pago: M-Pesa / e-Mola / Efectivo",
        "abrir_btn": "🏪 Quiero abrir mi tienda aquí",
        "suspensa": "🔒 Tienda suspendida temporalmente.",
        "esgotado": "🚫 AGOTADO",
        "stock": "✅ Disponible:",
        "retalho": "Detalle:",
        "grosso": "Por Mayor",
        "cor": "Color:",
        "qtd": "Cant:",
        "add": "🛒 Añadir",
        "vazio": "El carrito está vacío.",
        "zona": "🚚 Zona de Entrega:",
        "cupao": "🎟️ Cupón:",
        "total": "Total Final",
        "nome": "Tu Nombre:",
        "morada": "Dirección / Enlace GPS:",
        "forma_pg": "Método de Pago:",
        "limpar": "🗑️ Vaciar Carrito",
        "enviar_wa": "📲 ENVIAR PEDIDO POR WHATSAPP",
        "estrelas": "Estrellas:",
        "coment": "Comentario:",
        "env_av": "Enviar Reseña",
        "gestao": "🏪 Gestión de la Tienda",
        "sub_tabs": ["⚙️ Gestionar Mi Tienda", "🆕 Crear Tienda (Admin)"],
        "senha_l": "Contraseña del Comerciante:",
        "fotos": "📸 Fotos del Producto (Varias):",
        "video": "🎥 Video Corto del Producto (MP4/MOV):",
        "publicar": "💾 Publicar Producto"
    },
    "🇫🇷 Français": {
        "loja": "🏪 Choisir Boutique:",
        "mestre": "👑 Panneau Maître (Propriétaire)",
        "senha_m": "Mot de Passe Maître:",
        "tabs": ["🏬 Vitrine", "🛒 Panier", "⭐ Avis", "🏪 Espace Vendeur"],
        "aberta": "OUVERTE",
        "fechada": "FERMÉE",
        "pag": "Paiement: M-Pesa / e-Mola / Espèces",
        "abrir_btn": "🏪 Je veux ouvrir ma boutique ici",
        "suspensa": "🔒 Boutique temporairement suspendue.",
        "esgotado": "🚫 ÉPUISÉ",
        "stock": "✅ En Stock:",
        "retalho": "Détail:",
        "grosso": "Gros",
        "cor": "Couleur:",
        "qtd": "Qté:",
        "add": "🛒 Ajouter",
        "vazio": "Votre panier est vide.",
        "zona": "🚚 Zone de Livraison:",
        "cupao": "🎟️ Code Promo:",
        "total": "Total Final",
        "nome": "Votre Nom:",
        "morada": "Adresse / Lien GPS:",
        "forma_pg": "Paiement:",
        "limpar": "🗑️ Vider le Panier",
        "enviar_wa": "📲 COMMANDER SUR WHATSAPP",
        "estrelas": "Étoiles:",
        "coment": "Commentaire:",
        "env_av": "Envoyer l'Avis",
        "gestao": "🏪 Gestion de la Boutique",
        "sub_tabs": ["⚙️ Gérer Ma Boutique", "🆕 Créer Boutique (Admin)"],
        "senha_l": "Mot de Passe Vendeur:",
        "fotos": "📸 Photos du Produit (Plusieurs):",
        "video": "🎥 Courte Vidéo Produit (MP4/MOV):",
        "publicar": "💾 Publier le Produit"
    }
}

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
    idioma = st.selectbox("🌍 Idioma / Language:", list(TEXTOS.keys()))
    T = TEXTOS[idioma]
    st.title("🛍️ Catálogo Pro")
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
        esc = st.selectbox(T["loja"], list(mapa.keys()), index=idx_def)
        loja_atual = mapa[esc]

    st.divider()
    with st.expander(T["mestre"]):
        if st.text_input(T["senha_m"], type="password") == get_senha_mestre():
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

t1, t2, t3, t4 = st.tabs([T["tabs"].pop(0), f"{T['tabs'].pop(0)} ({len(st.session_state['carrinho'])})", T["tabs"].pop(0), T["tabs"].pop(0)])

with t1:
    if loja_atual:
        sg, ng, wg, _, lg, horg, abg, zong, cupc, cupd, _, stg, expg = loja_atual
        st.subheader(f"✅ {ng} ({T['aberta'] if abg==1 else T['fechada']})")
        st.caption(f"⏰ {horg} | 📍 {lg} | {T['pag']}")
        st.link_button(T["abrir_btn"], "https://wa.me.")
        if stg != "Ativa" or (expg > 0 and time.time() > expg):
            st.error(T["suspensa"])
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
                                    with st.expander(f"📸 +{len(fotos_p)}"):
                                        for f_ex in fotos_p:
                                            st.image(f_ex, use_container_width=True)
                            for v_ex in videos_p:
                                st.video(v_ex)
                        st.markdown(f"### {pnome}")
                        st.caption(f"{pcat} | {pdesc}")
                        if pesg == 1 or pstock <= 0: st.error(T["esgotado"])
                        else: st.success(f"{T['stock']} {pstock} un")
                        if pant > pun: st.markdown(f"~~{pant:,.2f} MT~~")
                        st.write(f"{T['retalho']} **{pun:,.2f} MT** | {T['grosso']} (≥{qmin}): **{pgr:,.2f} MT**")
                        cor = st.selectbox(T["cor"], [c.strip() for c in pcores.split(",") if c.strip()] or ["Padrão"], key=f"c_{pid}")
                        qtd = st.number_input(T["qtd"], min_value=1, max_value=max(1, int(pstock)), value=1, key=f"q_{pid}")
                        pu = pgr if qtd >= qmin else pun
                        tot = pu * qtd
                        if st.button(f"{T['add']} ({tot:,.2f} MT)", key=f"add_{pid}", disabled=(pesg == 1 or pstock <= 0)):
                            st.session_state["carrinho"].append({"wa": wg, "produto": pnome, "cor": cor, "qtd": qtd, "total": tot})
                            st.rerun()

with t2:
    if not st.session_state["carrinho"]:
        st.info(T["vazio"])
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
        z_sel = st.selectbox(T["zona"], list(zonas.keys()))
        frete = zonas[z_sel]
        cup = st.text_input(T["cupao"]).strip().upper()
        desc = tot_i * (c_dsc / 100.0) if (loja_atual and cup and cup == c_cod.strip().upper()) else 0.0
        tot_f = max(0.0, tot_i - desc) + frete
        st.metric(T["total"], f"{tot_f:,.2f} MT")
        cli = st.text_input(T["nome"])
        end = st.text_input(T["morada"])
        pg = st.selectbox(T["forma_pg"], ["M-Pesa", "e-Mola", "Cash"])
        if st.button(T["limpar"]):
            st.session_state["carrinho"] = []; st.rerun()
        wa = "".join(filter(str.isdigit, str(wa_dest)))
        if len(wa) == 9: wa = "258" + wa
        itens_m = "\n".join([f"- {it['qtd']}x {it['produto']} ({it['cor']}): {it['total']:,.2f} MT" for it in st.session_state["carrinho"]])
        msg = f"Ola! Novo pedido:\n\n{itens_m}\n\nEntrega ({z_sel}): {frete:,.2f} MT\nTotal: {tot_f:,.2f} MT\nCliente: {cli}\nMorada: {end}\nPagamento: {pg}"
        st.link_button(T["enviar_wa"], f"https://wa.me{wa}?text={urllib.parse.quote(msg)}")

with t3:
    if loja_atual:
        sg, _, _, _, _, _, _, _, _, _, _, _, _ = loja_atual
        na = st.text_input(T["nome"], key="av_n")
        es = st.selectbox(T["estrelas"], list(range(5, 0, -1)), key="av_e")
        co = st.text_input(T["coment"], key="av_c")
        if st.button(T["env_av"]) and na and co:
            conn.execute("INSERT INTO avaliacoes (loja_slug, cliente, estrelas, comentario, data) VALUES (?,?,?,?,?)", (sg, na, es, co, datetime.now().strftime("%Y-%m-%d")))
            conn.commit(); st.rerun()
        for (c_av, e_av, com_av, d_av) in conn.execute("SELECT cliente, estrelas, comentario, data FROM avaliacoes WHERE loja_slug=? ORDER BY id DESC", (sg,)).fetchall():
            st.write(f"{'⭐'*int(e_av)} **{c_av}** ({d_av}): {com_av}")

with t4:
    st.subheader(T["gestao"])
    sub1, sub2 = st.tabs(T["sub_tabs"])
    with sub1:
        if loja_atual:
            sg, ng, wg, pwg, lg, horg, abg, zong, cupc, cupd, fg_img, _, _ = loja_atual
            st.info(f"**{ng}** | Link: `https://streamlit.app{sg}`")
            if st.text_input(T["senha_l"], type="password", key="pw_l") == pwg:
                st.success("✅")
                fotos = st.file_uploader(T["fotos"], type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
                video_p = st.file_uploader(T["video"], type=["mp4", "mov", "webm"])
                nome_auto = os.path.splitext(fotos.name).replace("_", " ").title() if fotos else ""
                pn = st.text_input("Nome / Name:", value=nome_auto)
                pc = st.text_input("Categoria / Category:", value="Geral")
                pd = st.text_input("Descrição / Description:")
                c1, c2, c3 = st.columns(3)
                pa = c1.number_input("Preço Antigo:", min_value=0.0, value=0.0)
                pu = c2.number_input("Preço Retalho (MT):", min_value=1.0, value=100.0)
                pg_v = c3.number_input("Preço Grosso (MT):", min_value=1.0, value=80.0)
                pco = st.text_input("Cores / Colors:", value="Preto, Branco")
                pst = st.number_input("Stock:", min_value=0, value=10)
                if st.button(T["publicar"]) and pn:
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
                    conn.commit(); st.success("✅"); st.rerun()
                st.divider()
                for (id_p, nm_p, st_p, es_p) in conn.execute("SELECT id, nome, stock, esgotado FROM produtos_catalogo WHERE loja_slug=?", (sg,)).fetchall():
                    ca, cb, cc = st.columns(3)
                    ca.write(f"**{nm_p}** ({'Esgotado' if es_p==1 else f'{st_p} un'})")
                    if cb.button("Esgotado", key=f"e_{id_p}"):
                        conn.execute("UPDATE produtos_catalogo SET esgotado=? WHERE id=?", (0 if es_p==1 else 1, id_p)); conn.commit(); st.rerun()
                    if cc.button("🗑️", key=f"d_{id_p}"):
                        conn.execute("DELETE FROM produtos_catalogo WHERE id=?", (id_p,)); conn.commit(); st.rerun()
                st.divider()
                st.image(f"https://qrserver.com{sg}", caption="QR Code")
                f_bg = st.file_uploader("🖼️ Fundo / Background:", type=["png", "jpg", "jpeg"])
                if f_bg and st.button("Aplicar / Apply"):
                    p_bg = os.path.join("imagens_catalogo", f"bg_{sg}.png")
                    with open(p_bg, "wb") as fb: fb.write(f_bg.getbuffer())
                    conn.execute("UPDATE lojas SET fundo_img=? WHERE slug=?", (p_bg, sg)); conn.commit(); st.rerun()
                npw = st.text_input("Nova Senha / New Password:", type="password")
                if st.button("Alterar / Save") and len(npw) >= 4:
                    conn.execute("UPDATE lojas SET senha_lojista=? WHERE slug=?", (npw, sg)); conn.commit(); st.success("✅")
    with sub2:
        if st.text_input(T["senha_m"], type="password", key="pw_adm") == get_senha_mestre():
            nn = st.text_input("Nome da Nova Loja:")
            ns = st.text_input("Código Único:").strip().lower().replace(" ", "-")
            nw = st.text_input("WhatsApp:")
            nl = st.text_input("Localização:")
            np = st.text_input("Senha Lojista:", type="password")
            if st.button("🚀 Criar Loja") and nn and ns and nw and len(np) >= 4:
                conn.execute("INSERT INTO lojas (slug, nome_loja, whatsapp, senha_lojista, localizacao, plano_status, expira_em) VALUES (?,?,?,?,?,'Ativa',?)", (ns, nn, nw, np, nl, time.time() + 30*86400))
                conn.commit(); st.success("✅"); st.rerun()

st.divider()
st.caption("Catálogo Multi-Lojas Pro • Leonardo Jacinto Francisco • AdSense: ca-pub-7971514992716083 • Contacto: +258 87 970 7294")
