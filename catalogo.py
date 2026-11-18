import streamlit as st
import sqlite3
import urllib.parse
import os
import time
import base64
from datetime import datetime
from PIL import Image

st.set_page_config(page_title="Catálogo Multi-Lojas Pro", page_icon="🛍️", layout="wide")

DB_PATH = "catalogo_vendas_v2.db"
import shutil

def get_senha_mestre():
    arq = "senha_mestre_catalogo.txt"
    if os.path.exists(arq):
        with open(arq, "r", encoding="utf-8") as f:
            s = f.read().strip()
            if s: return s
    return "fracisco2003"
SENHA_MESTRE = get_senha_mestre()

TEMAS = {
    "Escuro Luxo Ouro": {"bg": "#09090b", "card": "#18181b", "txt": "#f4f4f5", "cor": "#f59e0b"},
    "Claro Moderno": {"bg": "#f8fafc", "card": "#ffffff", "txt": "#0f172a", "cor": "#2563eb"},
    "Verde Esmeralda": {"bg": "#042f2e", "card": "#115e59", "txt": "#f0fdfa", "cor": "#10b981"},
    "Rosa Boutique": {"bg": "#4c0519", "card": "#881337", "txt": "#fff1f2", "cor": "#f43f5e"},
    "Azul Executivo": {"bg": "#0f172a", "card": "#1e293b", "txt": "#f8fafc", "cor": "#38bdf8"},
}

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS lojas (
        slug TEXT PRIMARY KEY,
        nome_loja TEXT NOT NULL,
        whatsapp TEXT NOT NULL,
        senha_lojista TEXT NOT NULL,
        localizacao TEXT DEFAULT '',
        maps_url TEXT DEFAULT '',
        facebook_url TEXT DEFAULT '',
        tiktok_url TEXT DEFAULT '',
        horario TEXT DEFAULT '08:00 - 18:00',
        loja_aberta INTEGER DEFAULT 1,
        zonas_entrega TEXT DEFAULT 'Levantar na Loja:0, Marracuene Sede:100, Maputo Cidade:250',
        cupom_codigo TEXT DEFAULT '',
        cupom_desc INTEGER DEFAULT 0,
        tema TEXT DEFAULT 'Escuro Luxo Ouro',
        fundo_img TEXT DEFAULT '',
        plano_status TEXT DEFAULT 'Ativa',
        expira_em REAL DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS produtos_catalogo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loja_slug TEXT NOT NULL,
        nome TEXT NOT NULL,
        categoria TEXT NOT NULL,
        descricao TEXT DEFAULT '',
        preco_antigo REAL DEFAULT 0,
        preco_un REAL NOT NULL,
        preco_grosso REAL NOT NULL,
        qtd_min_grosso INTEGER DEFAULT 6,
        cores TEXT DEFAULT 'Padrão',
        stock INTEGER DEFAULT 10,
        esgotado INTEGER DEFAULT 0,
        destaque INTEGER DEFAULT 0,
        imagem_path TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loja_slug TEXT NOT NULL,
        cliente TEXT NOT NULL,
        bairro TEXT NOT NULL,
        itens_txt TEXT NOT NULL,
        itens_raw TEXT NOT NULL,
        total REAL NOT NULL,
        pagamento TEXT NOT NULL,
        data TEXT NOT NULL,
        status TEXT DEFAULT 'Pendente'
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS avaliacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        loja_slug TEXT NOT NULL,
        cliente TEXT NOT NULL,
        estrelas INTEGER DEFAULT 5,
        comentario TEXT NOT NULL,
        data TEXT NOT NULL
    )""")
    conn.commit()
    return conn

def reconhecer_imagem(uploaded_file):
    nome_limpo = os.path.splitext(uploaded_file.name)[0].replace("_", " ").replace("-", " ").title()
    img = Image.open(uploaded_file).convert("RGB").resize((50, 50))
    pixels = list(img.getdata())
    r = sum(p[0] for p in pixels) // len(pixels)
    g = sum(p[0] for p in pixels) // len(pixels)
    b = sum(p[0] for p in pixels) // len(pixels)
    if r > 200 and g > 200 and b > 200: cor = "Branco"
    elif r < 60 and g < 60 and b < 60: cor = "Preto"
    elif r > g + 40 and r > b + 40: cor = "Vermelho"
    elif b > r + 40 and b > g + 40: cor = "Azul"
    elif g > r + 30 and g > b + 30: cor = "Verde"
    elif r > 180 and g > 150 and b < 90: cor = "Dourado / Amarelo"
    else: cor = "Multicolor / Neutro"

    nl = nome_limpo.lower()
    if any(k in nl for k in ["iphone", "samsung", "galaxy", "redmi", "celular", "fone"]): cat = "Eletrónicos"
    elif any(k in nl for k in ["tenis", "sapato", "nike", "camisa", "vestido", "bolsa"]): cat = "Moda & Calçados"
    elif any(k in nl for k in ["perfume", "creme", "unha", "cabelo"]): cat = "Beleza"
    else: cat = "Geral"
    return nome_limpo, cat, cor

def aplicar_visual(tema_nome, fundo_path):
    t = TEMAS.get(tema_nome, TEMAS["Escuro Luxo Ouro"])
    bg_css = f"background-color: {t['bg']};"
    if fundo_path and os.path.exists(fundo_path):
        with open(fundo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        bg_css = f"background: linear-gradient(rgba(0,0,0,0.70), rgba(0,0,0,0.70)), url('data:image/png;base64,{b64}') center/cover fixed;"
    st.markdown(f"""<style>
        .stApp {{ {bg_css} color: {t['txt']}; }}
        h1, h2, h3 {{ color: {t['cor']} !important; }}
    </style>""", unsafe_allow_html=True)

conn = get_conn()
os.makedirs("imagens_catalogo", exist_ok=True)
if "carrinho" not in st.session_state: st.session_state["carrinho"] = []
loja_url = st.query_params.get("loja", "").strip().lower()

with st.sidebar:
    st.title("🛍️ Catálogo Pro")
    lojas_rows = conn.execute("SELECT * FROM lojas").fetchall()
    loja_atual = None
    if lojas_rows:
        mapa = {f"{r[1]} (@{r[0]})": r for r in lojas_rows}
        ops = list(mapa.keys())
        idx_def = next((i for i, r in enumerate(lojas_rows) if r[0] == loja_url), 0)
        esc = st.selectbox("🏪 Selecionar Loja:", ops, index=idx_def)
        loja_atual = mapa[esc]
    else:
        st.info("Crie a primeira loja na aba 'Área do Lojista'.")

    st.divider()
    with st.expander("👑 Painel Mestre (Dono)"):
        sm = st.text_input("Senha Mestre:", type="password", key="sm_in")
        if sm == SENHA_MESTRE:
            st.success("Modo Mestre Ativo")
            st.divider()
            if st.button("💾 Guardar Backup Completo (.db + Fotos)", use_container_width=True):
                os.makedirs("Backups_Catalogo", exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                if os.path.exists(DB_PATH):
                    shutil.copy2(DB_PATH, f"Backups_Catalogo/backup_{ts}.db")
                if os.path.exists("imagens_catalogo"):
                    shutil.make_archive(f"Backups_Catalogo/fotos_{ts}", "zip", "imagens_catalogo")
                st.success(f"✅ Backup guardado em Backups_Catalogo ({ts})!")

            with st.expander("🔐 Alterar Senha Mestre"):
                ns_m1 = st.text_input("Nova Senha Mestre:", type="password", key="ns_m1")
                ns_m2 = st.text_input("Confirmar Nova Senha:", type="password", key="ns_m2")
                if st.button("Guardar Nova Senha Mestre"):
                    if len(ns_m1.strip()) >= 4 and ns_m1 == ns_m2:
                        with open("senha_mestre_catalogo.txt", "w", encoding="utf-8") as f:
                            f.write(ns_m1.strip())
                        st.success("✅ Senha Mestre alterada! Recarregue a página.")
                    else:
                        st.error("❌ Senhas não coincidem ou têm menos de 4 caracteres.")
            for lj in lojas_rows:
                dias = max(0, int((lj[16] - time.time()) / 86400)) if lj[16] > 0 else 0
                st.write(f"**{lj[1]}** (`@{lj[0]}`) — {lj[15]} ({dias}d)")
                c1, c2, c3 = st.columns(3)
                if c1.button("✅ +30d", key=f"m_at_{lj[0]}"):
                    conn.execute("UPDATE lojas SET plano_status='Ativa', expira_em=? WHERE slug=?", (max(time.time(), lj[16]) + 30*86400, lj[0]))
                    conn.commit(); st.rerun()
                if c2.button("🚫 Bloq", key=f"m_bl_{lj[0]}"):
                    conn.execute("UPDATE lojas SET plano_status='Bloqueada' WHERE slug=?", (lj[0],))
                    conn.commit(); st.rerun()
                if c3.button("🗑️ Del", key=f"m_dl_{lj[0]}"):
                    conn.execute("DELETE FROM produtos_catalogo WHERE loja_slug=?", (lj[0],))
                    conn.execute("DELETE FROM lojas WHERE slug=?", (lj[0],))
                    conn.commit(); st.rerun()

if loja_atual:
    aplicar_visual(loja_atual[13], loja_atual[14])

aba_vitrine, aba_carrinho, aba_aval, aba_lojista = st.tabs([
    "🏬 Vitrine da Loja",
    f"🛒 Carrinho ({len(st.session_state['carrinho'])})",
    "⭐ Avaliações",
    "🏪 Área do Lojista"
])

with aba_vitrine:
    if not loja_atual:
        st.warning("👈 Crie a primeira loja na aba **Área do Lojista**.")
    else:
        slug_a, nome_a, wa_a, _, loc_a, maps_a, fb_a, tk_a, hor_a, aberta_a, zonas_a, cup_cod, cup_desc, tema_a, fundo_a, stat_a, exp_a = loja_atual
        avs = conn.execute("SELECT AVG(estrelas), COUNT(*) FROM avaliacoes WHERE loja_slug=?", (slug_a,)).fetchone()
        media_est = round(avs[0], 1) if avs and avs[0] else 5.0
        tot_av = avs[1] if avs else 0
        st.markdown(f"""<div style="background:linear-gradient(90deg,#18181b,#27272a);border:1px solid #f59e0b;border-radius:12px;padding:14px 18px;margin-bottom:14px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
            <div><span style="background:#10b981;color:#000;padding:3px 8px;border-radius:6px;font-size:11px;font-weight:bold;">✅ LOJA VERIFICADA</span> <b style="font-size:18px;margin-left:6px;">{nome_a}</b><br><span style="font-size:12px;color:#d4d4d8;">⭐ {media_est}/5.0 ({tot_av} avaliações) • Pagamento Seguro M-Pesa / e-Mola</span></div>
            <a href="https://wa.me." target="_blank" style="background:#f59e0b;color:#000;padding:8px 14px;border-radius:8px;font-weight:bold;text-decoration:none;font-size:12px;">🏪 Quero uma Loja Igual</a>
        </div>""", unsafe_allow_html=True)
        st.write(f"{'🟢 ABERTA AGORA' if aberta_a==1 else '🔴 FECHADA NO MOMENTO'} • ⏰ Horário: **{hor_a}**" + (f" • 📍 {loc_a}" if loc_a else ""))
        c_links = st.columns(3)
        if maps_a: c_links.link_button("🗺️ Google Maps", maps_a)
        if fb_a: c_links.link_button("📘 Facebook", fb_a)
        if tk_a: c_links.link_button("🎵 TikTok", tk_a)

        if stat_a != "Ativa" or (exp_a > 0 and time.time() > exp_a):
            st.error("🔒 Loja temporariamente suspensa. Contacte o administrador para renovar a assinatura.")
        else:
            prods = conn.execute(
                "SELECT id, nome, categoria, descricao, preco_antigo, preco_un, preco_grosso, qtd_min_grosso, cores, stock, esgotado, destaque, imagem_path FROM produtos_catalogo WHERE loja_slug=? ORDER BY destaque DESC, id DESC",
                (slug_a,)
            ).fetchall()
            if not prods:
                st.info("Esta loja ainda não publicou produtos.")
            else:
                cats = ["Todas"] + sorted(list(set(p[2] for p in prods)))
                f_cat = st.selectbox("Filtrar Categoria:", cats)
                busca = st.text_input("🔍 Pesquisar produto:")
                filtrados = [p for p in prods if (f_cat == "Todas" or p[2] == f_cat) and (busca.lower() in p[1].lower())]
                cols = st.columns(3)
                for idx, p in enumerate(filtrados):
                    pid, pnome, pcat, pdesc, pant, pun, pgr, qmin, pcores, pstock, pesg, pdest, pimg = p
                    with cols[idx % 3]:
                        with st.container(border=True):
                            if pdest == 1:
                                st.markdown("⭐ **DESTAQUE**")
                            if pimg and os.path.exists(pimg):
                                st.image(pimg, use_container_width=True)
                            st.subheader(pnome)
                            st.caption(f"{pcat} • {pdesc}")
                            if pesg == 1 or pstock <= 0:
                                st.error("🚫 ESGOTADO")
                            else:
                                st.success(f"✅ Em Stock: {pstock} un")
                            if pant and pant > pun:
                                off = int(((pant - pun) / pant) * 100)
                                st.markdown(f"~~{pant:,.2f} MT~~ 🔥 **-{off}% OFF**")
                            st.write(f"💵 Retalho: **{pun:,.2f} MT**")
                            st.write(f"📦 Grosso (≥{qmin} un): **{pgr:,.2f} MT/un**")
                            lista_c = [c.strip() for c in pcores.split(",") if c.strip()] or ["Padrão"]
                            cor_esc = st.selectbox("Cor / Modelo:", lista_c, key=f"cor_{pid}")
                            qk = f"qty_{pid}"
                            if qk not in st.session_state: st.session_state[qk] = 1
                            b1, b2, b3 = st.columns([1, 2, 1])
                            if b1.button("➖", key=f"m_{pid}") and st.session_state[qk] > 1:
                                st.session_state[qk] -= 1; st.rerun()
                            b2.markdown(f"<div style='text-align:center;font-weight:bold;padding-top:6px;'>{st.session_state[qk]} un</div>", unsafe_allow_html=True)
                            if b3.button("➕", key=f"p_{pid}") and st.session_state[qk] < max(1, pstock):
                                st.session_state[qk] += 1; st.rerun()
                            qa = st.session_state[qk]
                            p_ap = pgr if qa >= qmin else pun
                            sub = p_ap * qa
                            st.info(f"Subtotal: **{sub:,.2f} MT**")
                            if st.button("🛒 Adicionar ao Carrinho", key=f"add_{pid}", disabled=(pesg == 1 or pstock <= 0), use_container_width=True):
                                st.session_state["carrinho"].append({
                                    "id": pid, "slug": slug_a, "loja": nome_a, "wa": wa_a,
                                    "produto": pnome, "cor": cor_esc, "qtd": qa, "unit": p_ap, "total": sub
                                })
                                st.toast(f"✅ {pnome} adicionado!"); st.rerun()

with aba_carrinho:
    st.header("🛒 Meu Carrinho de Encomenda")
    if not st.session_state["carrinho"]:
        st.info("O carrinho está vazio.")
    else:
        tot_itens = 0.0
        linhas = []
        raw_list = []
        wa_d = st.session_state["carrinho"][0]["wa"]
        lj_d = st.session_state["carrinho"][0]["loja"]
        sl_d = st.session_state["carrinho"][0]["slug"]
        for i, it in enumerate(st.session_state["carrinho"]):
            st.write(f"**{i+1}. {it['produto']}** | Cor: {it['cor']} | {it['qtd']}x {it['unit']:,.2f} MT = **{it['total']:,.2f} MT**")
            tot_itens += it["total"]
            linhas.append(f"- {it['qtd']}x {it['produto']} ({it['cor']}): {it['total']:,.2f} MT")
            raw_list.append(f"{it['id']}:{it['qtd']}")

        mapa_zonas = {}
        if loja_atual and loja_atual[10]:
            for z in loja_atual[10].split(","):
                if ":" in z:
                    zn, zv = z.split(":", 1)
                    try: mapa_zonas[zn.strip()] = float(zv.strip())
                    except: pass
        if not mapa_zonas: mapa_zonas = {"Levantar na Loja": 0.0}
        zona_esc = st.selectbox("🚚 Zona / Taxa de Entrega:", list(mapa_zonas.keys()))
        taxa_ent = mapa_zonas[zona_esc]

        cup_in = st.text_input("🎟️ Cupão de Desconto (Opcional):").strip().upper()
        desc_val = 0.0
        if loja_atual and cup_in and cup_in == loja_atual[11].strip().upper() and loja_atual[12] > 0:
            desc_val = tot_itens * (loja_atual[12] / 100.0)
            st.success(f"🎉 Cupão aplicado: -{loja_atual[12]}% (-{desc_val:,.2f} MT)")

        tot_final = max(0.0, tot_itens - desc_val) + taxa_ent
        st.metric("Total Final a Pagar", f"{tot_final:,.2f} MT", delta=f"Entrega: +{taxa_ent:,.2f} MT")
        cli_n = st.text_input("Seu Nome:")
        cli_b = st.text_input("Referência / Morada Exata:")
        import streamlit.components.v1 as components
        gps_url = st.query_params.get("gps", "")
        if gps_url:
            st.success(f"📍 Localização GPS capturada com sucesso!")
            cli_b = f"https://google.com{gps_url} ({cli_b})"
        components.html("""
            <button onclick="navigator.geolocation.getCurrentPosition(function(pos){
                const url = new URL(window.parent.location.href);
                url.searchParams.set('gps', pos.coords.latitude + ',' + pos.coords.longitude);
                window.parent.location.href = url.toString();
            }, function(){ alert('Ative o GPS / Localização no telemóvel e tente novamente.'); });"
            style="width:100%;padding:10px;background:#2563eb;color:#fff;border:none;border-radius:8px;font-weight:bold;cursor:pointer;margin-bottom:8px;">
            📍 Capturar Minha Localização Exata (GPS)
            </button>
        """, height=52)
        pg_op = st.selectbox("Pagamento:", ["📱 M-Pesa", "🟠 e-Mola", "💵 Dinheiro na Entrega"])

        c_b1, c_b2 = st.columns(2)
        if c_b1.button("🗑️ Limpar Carrinho", use_container_width=True):
            st.session_state["carrinho"] = []; st.rerun()

        if c_b2.button("✅ Registar Pedido & Abrir WhatsApp", use_container_width=True):
            conn.execute("INSERT INTO pedidos (loja_slug, cliente, bairro, itens_txt, itens_raw, total, pagamento, data, status) VALUES (?,?,?,?,?,?,?,?,'Pendente')",
                         (sl_d, cli_n or "Cliente", f"{zona_esc} ({cli_b})", "\n".join(linhas), ",".join(raw_list), tot_final, pg_op, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            n_wa = "".join(filter(str.isdigit, str(wa_d)))
            if len(n_wa) == 9: n_wa = "258" + n_wa
            msg_wa = f"Olá *{lj_d}*! Novo pedido:\n\n" + "\n".join(linhas) + f"\n\nEntrega ({zona_esc}): {taxa_ent:,.2f} MT\nDesconto: -{desc_val:,.2f} MT\n*TOTAL: {tot_final:,.2f} MT*\nCliente: {cli_n}\nMorada: {cli_b}\nPagamento: {pg_op}"
            st.link_button("📲 CLICAR AQUI PARA ENVIAR NO WHATSAPP", f"https://wa.me{n_wa}?text={urllib.parse.quote(msg_wa)}", use_container_width=True)

with aba_aval:
    st.header("⭐ Avaliações de Clientes")
    if loja_atual:
        sl_av = loja_atual[0]
        av_nome = st.text_input("Seu Nome:", key="av_n")
        av_est = st.selectbox("Classificação:", [5, 4, 3, 2, 1], format_func=lambda x: "⭐" * x)
        av_com = st.text_input("Seu Comentário sobre a loja/produtos:", key="av_c")
        if st.button("Enviar Avaliação") and av_nome and av_com:
            conn.execute("INSERT INTO avaliacoes (loja_slug, cliente, estrelas, comentario, data) VALUES (?,?,?,?,?)",
                         (sl_av, av_nome.strip(), av_est, av_com.strip(), datetime.now().strftime("%Y-%m-%d")))
            conn.commit(); st.success("✅ Obrigado pela avaliação!"); st.rerun()
        st.divider()
        for av in conn.execute("SELECT cliente, estrelas, comentario, data FROM avaliacoes WHERE loja_slug=? ORDER BY id DESC", (sl_av,)).fetchall():
            st.write(f"{'⭐'*av} **{av}** ({av}): _{av}_")

with aba_lojista:
    st.header("🏪 Área do Lojista")
    t1, t2 = st.tabs(["🆕 Criar Nova Loja", "⚙️ Gerir Minha Loja"])
    with t1:
        pw_dono_c = st.text_input("🔑 Senha do Administrador da Plataforma:", type="password", key="pw_dono_criar")
        if pw_dono_c != get_senha_mestre():
            st.warning("🔒 Área restrita ao proprietário da plataforma. Para abrir a sua loja aqui, contacte o administrador.")
            st.link_button("📲 Pedir Abertura da Minha Loja no WhatsApp", "https://wa.me.")
        else:
            nn = st.text_input("Nome da Loja:")
            ns = st.text_input("Código Único (ex: boutique-maputo):").strip().lower().replace(" ", "-")
            nw = st.text_input("WhatsApp da Loja (ex: 845707294):")
            nl = st.text_input("Localização / Bairro:")
            npw = st.text_input("Senha do Lojista:", type="password")
            dias_ini = st.number_input("Dias de Licença Inicial:", min_value=1, value=30)
            if st.button("🚀 Criar e Ativar Loja Agora", use_container_width=True):
                if nn and ns and nw and len(npw) >= 4:
                    if conn.execute("SELECT slug FROM lojas WHERE slug=?", (ns,)).fetchone():
                        st.error("❌ Código já existe.")
                    else:
                        conn.execute("INSERT INTO lojas (slug, nome_loja, whatsapp, senha_lojista, localizacao, plano_status, expira_em) VALUES (?,?,?,?,?,'Ativa',?)",
                                     (ns, nn.strip(), nw.strip(), npw.strip(), nl.strip(), time.time() + dias_ini*86400))
                        conn.commit(); st.success(f"✅ Loja ativada por {dias_ini} dias!"); st.rerun()
    with t2:
        if loja_atual:
            sg, ng, wg, pwg, lg, mg, fg, tg, horg, abg, zong, cupc, cupd, temag, fundog, _, _ = loja_atual
            s_in = st.text_input("Senha desta Loja:", type="password", key="pw_loj_g")
            if s_in == pwg:
                st.success("🔓 Painel Desbloqueado!")
                sub_p, sub_ped, sub_v, sub_qr = st.tabs(["📦 Produtos & Promoções", "📋 Pedidos & Faturação", "🎨 Visual, Entrega & Cupões", "📲 QR Code & Senha"])

                with sub_p:
                    foto = st.file_uploader("📸 Foto da Galeria (Reconhecimento Automático):", type=["png", "jpg", "jpeg", "webp"])
                    sn, sc, scor = reconhecer_imagem(foto) if foto else ("", "Geral", "Preto, Branco")
                    if foto: st.info(f"🤖 Detetado: **{sn}** | **{sc}** | Cor: **{scor}**")
                    pn = st.text_input("Nome do Produto:", value=sn)
                    pc = st.text_input("Categoria:", value=sc)
                    pd_txt = st.text_input("Descrição Curta:")
                    c1, c2, c3, c4 = st.columns(4)
                    pant_in = c1.number_input("Preço Antigo (Riscado):", min_value=0.0, value=0.0)
                    pun = c2.number_input("Preço Retalho (MT):", min_value=1.0, value=100.0)
                    pgr = c3.number_input("Preço Grosso (MT):", min_value=1.0, value=80.0)
                    qmn = c4.number_input("Qtd Mín Grosso:", min_value=2, value=6)
                    pco = st.text_input("Cores / Modelos:", value=scor)
                    pst = st.number_input("Stock Inicial:", min_value=0, value=20)
                    pdest_in = st.checkbox("⭐ Colocar em Destaque no Topo")
                    if st.button("💾 Publicar Produto", use_container_width=True) and pn:
                        c_img = ""
                        if foto:
                            c_img = os.path.join("imagens_catalogo", f"{sg}_{int(time.time())}_{foto.name}")
                            with open(c_img, "wb") as fo: fo.write(foto.getbuffer())
                        conn.execute("INSERT INTO produtos_catalogo (loja_slug, nome, categoria, descricao, preco_antigo, preco_un, preco_grosso, qtd_min_grosso, cores, stock, esgotado, destaque, imagem_path) VALUES (?,?,?,?,?,?,?,?,?,?,0,?,?)",
                                     (sg, pn.strip(), pc.strip(), pd_txt.strip(), pant_in, pun, pgr, qmn, pco.strip(), pst, 1 if pdest_in else 0, c_img))
                        conn.commit(); st.success("✅ Publicado!"); st.rerun()
                    st.divider()
                    for mp in conn.execute("SELECT id, nome, stock, esgotado FROM produtos_catalogo WHERE loja_slug=?", (sg,)).fetchall():
                        ca, cb, cc, cd = st.columns([3, 2, 1, 1])
                        ca.write(f"**{mp[1]}** ({'🚫 Esgotado' if mp[3]==1 else f'✅ {mp[2]} un'})")
                        nst = cb.number_input("Stock", min_value=0, value=int(mp[2]), key=f"st_{mp[0]}", label_visibility="collapsed")
                        if cb.button("Atualizar", key=f"up_{mp[0]}"):
                            conn.execute("UPDATE produtos_catalogo SET stock=? WHERE id=?", (nst, mp[0])); conn.commit(); st.rerun()
                        if cc.button("Esgotado", key=f"es_{mp[0]}"):
                            conn.execute("UPDATE produtos_catalogo SET esgotado=? WHERE id=?", (0 if mp[3]==1 else 1, mp[0])); conn.commit(); st.rerun()
                        if cd.button("🗑️", key=f"dl_{mp[0]}"):
                            conn.execute("DELETE FROM produtos_catalogo WHERE id=?", (mp[0],)); conn.commit(); st.rerun()

                with sub_ped:
                    peds = conn.execute("SELECT id, cliente, bairro, itens_txt, itens_raw, total, pagamento, data, status FROM pedidos WHERE loja_slug=? ORDER BY id DESC", (sg,)).fetchall()
                    tot_fat = sum(p[5] for p in peds if p[8] == "Pago")
                    st.metric("💰 Total Faturado (Pedidos Pagos)", f"{tot_fat:,.2f} MT")
                    for pd_row in peds:
                        with st.container(border=True):
                            st.write(f"**Pedido #{pd_row[0]}** ({pd_row[7]}) — **{pd_row[1]}** | {pd_row[2]} | **{pd_row[5]:,.2f} MT** ({pd_row[6]}) — Status: **{pd_row[8]}**")
                            st.text(pd_row[3])
                            if pd_row[8] != "Pago" and st.button("✅ Confirmar Pagamento & Abater Stock", key=f"pg_{pd_row[0]}"):
                                for pair in pd_row[4].split(","):
                                    if ":" in pair:
                                        pid_s, q_s = pair.split(":")
                                        conn.execute("UPDATE produtos_catalogo SET stock = MAX(0, stock - ?) WHERE id=?", (int(q_s), int(pid_s)))
                                conn.execute("UPDATE pedidos SET status='Pago' WHERE id=?", (pd_row[0],))
                                conn.commit(); st.success("✅ Pago e stock abatido!"); st.rerun()

                with sub_v:
                    aberta_in = st.checkbox("🟢 Loja Aberta Agora", value=(abg == 1))
                    hor_in = st.text_input("⏰ Horário:", value=horg)
                    zon_in = st.text_input("🚚 Taxas de Entrega (Formato: Zona:Valor, Zona2:Valor):", value=zong)
                    c_cp1, c_cp2 = st.columns(2)
                    cup_c_in = c_cp1.text_input("🎟️ Código do Cupão (ex: PROMO10):", value=cupc)
                    cup_d_in = c_cp2.number_input("Desconto do Cupão (%):", min_value=0, max_value=90, value=int(cupd))
                    novo_tema = st.selectbox("🎨 Tema:", list(TEMAS.keys()), index=list(TEMAS.keys()).index(temag) if temag in TEMAS else 0)
                    foto_fundo = st.file_uploader("🖼️ Foto de Fundo da Loja:", type=["png", "jpg", "jpeg"])
                    n_loc = st.text_input("📍 Localização:", value=lg)
                    n_maps = st.text_input("🗺️ Link Google Maps:", value=mg)
                    n_fb = st.text_input("📘 Facebook:", value=fg)
                    n_tk = st.text_input("🎵 TikTok:", value=tg)
                    if st.button("💾 Guardar Todas as Configurações", use_container_width=True):
                        cf = fundog
                        if foto_fundo:
                            cf = os.path.join("imagens_catalogo", f"fundo_{sg}_{int(time.time())}.png")
                            with open(cf, "wb") as ff: ff.write(foto_fundo.getbuffer())
                        conn.execute("UPDATE lojas SET loja_aberta=?, horario=?, zonas_entrega=?, cupom_codigo=?, cupom_desc=?, tema=?, fundo_img=?, localizacao=?, maps_url=?, facebook_url=?, tiktok_url=? WHERE slug=?",
                                     (1 if aberta_in else 0, hor_in, zon_in, cup_c_in.strip().upper(), cup_d_in, novo_tema, cf, n_loc, n_maps, n_fb, n_tk, sg))
                        conn.commit(); st.success("✅ Configurações guardadas!"); st.rerun()

                with sub_qr:
                    url_base = st.text_input("Link online:", value=f"https://streamlit.app{sg}")
                    st.image(f"https://qrserver.com{urllib.parse.quote(url_base)}", caption="QR Code Oficial")
                    nova_pw = st.text_input("Nova Senha:", type="password")
                    if st.button("🔐 Alterar Senha") and len(nova_pw.strip()) >= 4:
                        conn.execute("UPDATE lojas SET senha_lojista=? WHERE slug=?", (nova_pw.strip(), sg))
                        conn.commit(); st.success("✅ Senha alterada!")







