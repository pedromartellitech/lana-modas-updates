# ====================== Lana Modas - App Completo (ajustado) ======================
from io import BytesIO
import os
import calendar
import tempfile
import time
from datetime import datetime, date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu

# ReportLab (PDF)
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
    LongTable, Table, TableStyle, PageBreak, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as _canvas

# ---------------- Caminhos & I/O seguro ----------------
APP_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
DATA_DIR = os.path.join(APP_DIR, "data")  # será criada automaticamente
os.makedirs(DATA_DIR, exist_ok=True)

ARQ_REGISTROS = os.path.join(DATA_DIR, "registros.csv")
ARQ_DESPESAS  = os.path.join(DATA_DIR, "despesas.csv")

def safe_read_csv(path: str, seps=(",", ";", "\t")) -> pd.DataFrame:
    """Tenta ler CSV com separadores comuns. Retorna DataFrame vazio se não existir."""
    if not os.path.exists(path):
        return pd.DataFrame()
    for s in seps:
        try:
            return pd.read_csv(path, sep=s, encoding="utf-8")
        except Exception:
            continue
    # fallback
    try:
        return pd.read_csv(path, encoding="utf-8")
    except Exception:
        return pd.DataFrame()

def safe_write_csv(df: pd.DataFrame, path: str, max_retries: int = 5, delay: float = 0.4):
    """Escrita atômica com retry (lida com arquivo aberto no Excel/OneDrive)."""
    df = df.copy()
    tmp_fd, tmp_path = tempfile.mkstemp(prefix="tmp_", suffix=".csv", dir=os.path.dirname(path))
    os.close(tmp_fd)
    df.to_csv(tmp_path, index=False, encoding="utf-8")
    last_err = None
    for _ in range(max_retries):
        try:
            os.replace(tmp_path, path)  # atômico
            return
        except PermissionError as e:
            last_err = e
            time.sleep(delay)
    try:
        os.remove(tmp_path)
    except Exception:
        pass
    raise last_err if last_err else RuntimeError("Falha ao gravar CSV.")

def carregar_csv_garantindo_colunas(caminho, colunas):
    """Carrega CSV e garante que todas as colunas existam (em ordem)."""
    df = safe_read_csv(caminho)
    if df.empty:
        df = pd.DataFrame(columns=colunas)
    for c in colunas:
        if c not in df.columns:
            df[c] = None
    df = df[colunas]
    return df

# ---------------- Config da página ----------------
st.set_page_config(page_title="Lana Modas", layout="wide")

# chave para forçar reload quando salvar algo
st.session_state.setdefault("reload_key", 0)

# ---------------- Sidebar Moderno ----------------
with st.sidebar:
    escolha = option_menu(
        menu_title="👗 Lana Modas",
        options=[
            "🏠 Início",
            "📋 Cadastro de Vendas",
            "💸 Despesas",
            "📈 Relatórios",
        ],
        icons=["house", "cart-plus", "cash-stack", "bar-chart-line"],
        menu_icon="shop",
        default_index=0,
        styles={
            "container": {
                "padding": "5px",
                "background-color": "#090909",
                "border-radius": "12px"
            },
            "icon": {"color": "#FF006F", "font-size": "20px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "5px",
                "--hover-color": "#FF006F"
            },
            "nav-link-selected": {
                "background-color": "#FF006F",
                "color": "white",
                "font-weight": "bold"
            },
        }
    )

# ====================== INÍCIO ======================
if escolha == "🏠 Início":
    # ================== CONFIG DE MARKETING ==================
    DEV = {
        "nome": "Pedro Martelli",
        "headline": "Transformo ideias em sistemas úteis e práticos.",
        "sub": "Apps para varejo de moda • Dashboards financeiros • Automação de processos • Streamlit",
        # Coloque seus links se quiser que os botões apareçam
        "whatsapp": "",   # ex: "https://wa.me/55DDDNUMERO?text=Olá%20quero%20saber%20sobre%20o%20Lana%20Modas"
        "instagram": "",
        "linkedin": "",
        "github": "",
        # Métricas para os contadores animados
        "metric_clientes": 42,
        "metric_projetos": 65,
        "metric_satisfacao": 98,     # %
        "metric_resposta_horas": 2   # h
    }

    # Botões dinâmicos (só aparecem se tiver link)
    ctas = []
    if DEV.get("whatsapp"):  ctas.append(f"<a class='btn primary' href='{DEV['whatsapp']}' target='_blank' rel='noopener'>Fale no WhatsApp</a>")
    if DEV.get("instagram"): ctas.append(f"<a class='btn' href='{DEV['instagram']}' target='_blank' rel='noopener'>Instagram</a>")
    if DEV.get("linkedin"):  ctas.append(f"<a class='btn' href='{DEV['linkedin']}' target='_blank' rel='noopener'>LinkedIn</a>")
    if DEV.get("github"):    ctas.append(f"<a class='btn' href='{DEV['github']}' target='_blank' rel='noopener'>GitHub</a>")
    cta_html = "".join(ctas) or "<span class='muted'>Adicione seus links para mostrar os botões aqui.</span>"

    hora = datetime.now().hour
    saudacao = "Bom dia" if hora < 12 else ("Boa tarde" if hora < 18 else "Boa noite")

    # ================== HERO + BENEFÍCIOS (HTML) ==================
    html_inicio = f"""
    <style>
      :root {{
        --bg:#0b0b0e; --panel:#14141a; --text:#fff; --muted:#b7b7c5;
        --brand:#FF006F; --brand2:#ff4d94; --stroke:rgba(255,255,255,.12);
        --ok:#3ddc97; --warn:#ffcc00;
      }}
      *{{box-sizing:border-box}}
      body, .lm-wrap {{ background: transparent; }}
      .lm-wrap {{ padding: 20px 4px 36px; }}

      /* HERO */
      .hero {{
        position:relative; overflow:hidden; border:1px solid var(--stroke);
        border-radius:18px; padding:28px 22px;
        background:
          linear-gradient(135deg, rgba(255,0,111,.08), rgba(41,19,39,.22)),
          linear-gradient(0deg, rgba(255,255,255,.02), rgba(255,255,255,.02));
        isolation:isolate;
      }}
      .hero::before {{
        content:""; position:absolute; inset:-20%;
        background: conic-gradient(from 140deg, #ff4d94, #6a3df5, #18b2b8, #ff4d94);
        filter: blur(28px); opacity: .10; z-index:-1;
      }}
      .badge {{
        display:inline-block; font-size:12px; color:var(--muted);
        background: rgba(255,255,255,.04); border:1px solid var(--stroke);
        padding:6px 10px; border-radius:999px; margin-bottom:10px;
      }}
      .titulo {{ font-size:36px; font-weight:900; margin:0 0 8px; letter-spacing:-.6px; }}
      .highlight {{
        color: var(--brand);
        background: linear-gradient(90deg, rgba(255,0,111,.2), transparent);
        border-radius:8px; padding:0 6px;
      }}
      .sub {{ color:var(--muted); font-size:14px; margin:0; max-width:900px; }}
      .cta {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:12px; align-items:center; }}
      .btn {{
        padding:10px 14px; border-radius:12px; text-decoration:none; color:#fff;
        border:1px solid var(--stroke);
        background: linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.02));
        transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
        font-weight:700; outline: none;
      }}
      .btn.primary {{ background: linear-gradient(180deg, var(--brand), var(--brand2)); border-color: transparent; }}
      .btn:hover, .btn:focus-visible {{ transform: translateY(-1px); box-shadow: 0 10px 24px rgba(0,0,0,.35); border-color: rgba(255,255,255,.25); }}
      .muted {{ color: var(--muted); font-size: 13px; }}

      /* MÉTRICAS */
      .metrics {{ margin-top:16px; display:grid; grid-template-columns: repeat(4,1fr); gap:12px; }}
      .metric {{
        text-align:center; border:1px solid var(--stroke); border-radius:16px; padding:16px;
        background: linear-gradient(180deg, rgba(255,255,255,.05), rgba(255,255,255,.015));
      }}
      .metric .num {{ font-size:28px; font-weight:900; letter-spacing:-.6px; }}
      .metric .lbl {{ color:var(--muted); font-size:12px; }}

      /* BENEFÍCIOS */
      .grid {{ margin-top:16px; display:grid; grid-template-columns: repeat(3,1fr); gap:12px; }}
      .card {{
        background: var(--panel); border:1px solid var(--stroke); border-radius:16px; padding:16px;
        transition: transform .15s ease, border-color .15s ease, background .15s ease;
        position: relative;
      }}
      .card:hover {{ transform: translateY(-3px); border-color: rgba(255,255,255,.18); background: #171721; }}
      .emoji {{ font-size:26px; margin-bottom:6px; }}
      .card-title {{ margin:0 0 4px 0; font-size:16px; font-weight:800; color:#ff77aa; }}
      .card-desc {{ margin:0; color:var(--muted); font-size:13px; }}

      /* PROVAS SOCIAIS / LOGOS */
      .logos {{
        margin:18px 0 0; display:flex; gap:16px; flex-wrap:wrap; align-items:center;
        color:#c9c9d1; font-size:13px;
      }}
      .logo-pill {{ border:1px dashed rgba(255,255,255,.18); border-radius:999px; padding:6px 12px; }}

      /* DIFERENCIAIS */
      .about {{ margin-top:18px; display:grid; grid-template-columns:1.1fr 1fr; gap:12px; }}
      .panel {{ background:var(--panel); border:1px solid var(--stroke); border-radius:16px; padding:16px; }}
      .panel h3 {{ margin:0 0 8px 0; }}
      .bio {{ color:var(--muted); font-size:14px; }}
      .bullets {{ list-style:none; padding-left:0; margin:8px 0 0; }}
      .bullets li {{ margin:8px 0; color:var(--muted); font-size:14px; }}
      .bullets li::before {{ content:"✓"; color:var(--ok); font-weight:900; margin-right:8px; }}

      /* DEPOIMENTOS */
      .quotes {{ margin-top:12px; display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
      .quote {{
        border:1px solid var(--stroke); border-radius:16px; padding:14px;
        background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.01));
        color:var(--muted); font-size:14px;
      }}
      .quote .who {{ color:#fff; margin-top:8px; font-weight:700; }}

      /* FOOTER */
      .footer {{ text-align:center; color:var(--muted); margin-top:16px; font-size:12.5px; }}

      /* RESPONSIVO */
      @media (max-width:1100px) {{
        .grid {{ grid-template-columns:1fr 1fr; }}
        .metrics {{ grid-template-columns:1fr 1fr; }}
        .about {{ grid-template-columns:1fr; }}
        .quotes {{ grid-template-columns:1fr; }}
      }}
      @media (max-width:640px) {{
        .grid {{ grid-template-columns:1fr; }}
        .titulo {{ font-size:28px; }}
      }}

      /* acessibilidade */
      :focus-visible {{ outline: 2px dashed var(--brand2); outline-offset: 2px; }}
      @media (prefers-reduced-motion: reduce) {{
        * {{ animation: none !important; transition: none !important; }}
      }}
    </style>

    <div class="lm-wrap">
      <!-- HERO -->
      <section class="hero" role="banner" aria-label="Apresentação">
        <span class="badge">{saudacao}! 👋 Bem-vindo(a) ao</span>
        <h1 class="titulo"><span class="highlight">Lana Modas</span> — gestão de loja no seu ritmo</h1>
        <p class="sub">Sistema focado em resultado: cadastre vendas em segundos, controle despesas e comunique seu valor com relatórios simples de entender.</p>
        <div class="cta">{cta_html}</div>

        <!-- Métricas/Provas -->
        <div class="metrics" aria-label="Provas & métricas">
          <div class="metric">
            <div class="num" data-target="{DEV.get('metric_clientes',0)}" data-suffix="" data-decimals="0">0</div>
            <div class="lbl">Clientes atendidos</div>
          </div>
          <div class="metric">
            <div class="num" data-target="{DEV.get('metric_projetos',0)}" data-suffix="" data-decimals="0">0</div>
            <div class="lbl">Projetos entregues</div>
          </div>
          <div class="metric">
            <div class="num" data-target="{DEV.get('metric_satisfacao',0)}" data-suffix="%" data-decimals="0">0</div>
            <div class="lbl">Satisfação</div>
          </div>
          <div class="metric">
            <div class="num" data-target="{DEV.get('metric_resposta_horas',0)}" data-suffix="h" data-decimals="0">0</div>
            <div class="lbl">Tempo de resposta</div>
          </div>
        </div>

        <!-- Benefícios principais -->
        <section class="grid" aria-label="Benefícios">
          <div class="card" tabindex="0" role="article" aria-label="Cadastro de Vendas">
            <div class="emoji">⚡</div>
            <h4 class="card-title">Cadastro em segundos</h4>
            <p class="card-desc">Menos cliques, mais produtividade. Desconto em % e total final automáticos.</p>
          </div>
          <div class="card" tabindex="0" role="article" aria-label="Controle de Despesas">
            <div class="emoji">🧮</div>
            <h4 class="card-title">Controle que dá clareza</h4>
            <p class="card-desc">Organize gastos por categoria e saiba exatamente para onde vai o dinheiro.</p>
          </div>
          <div class="card" tabindex="0" role="article" aria-label="Relatórios Simples">
            <div class="emoji">📣</div>
            <h4 class="card-title">Fale a linguagem do dono</h4>
            <p class="card-desc">Informação sem complicação, para decisões rápidas e seguras.</p>
          </div>
        </section>

        <!-- Logos/selos (exemplo fictício) -->
        <div class="logos" aria-label="Provas sociais">
          <span class="logo-pill">🏷️ ModaLocal</span>
          <span class="logo-pill">🧵 Ateliê25</span>
          <span class="logo-pill">👗 VesteJá</span>
          <span class="logo-pill">🛍️ FashionHub</span>
          <span class="logo-pill">⭐ 4.9/5 média</span>
        </div>
      </section>

      <!-- SOBRE e DIFERENCIAIS -->
      <section class="about" aria-label="Sobre e diferenciais">
        <div class="panel">
          <h3>Sobre <span class="highlight">{DEV.get('nome','')}</span></h3>
          <p class="bio">{DEV.get('headline','')} {DEV.get('sub','')}</p>
          <ul class="bullets">
            <li>Implantação rápida e suporte próximo — você nunca fica na mão.</li>
            <li>Design focado no que importa: simplicidade, velocidade e clareza.</li>
            <li>Funciona bem em computador comum — nada de travamentos.</li>
            <li>Exportações e compartilhamentos práticos quando necessário.</li>
          </ul>
        </div>
        <div class="panel">
          <h3>Depoimentos</h3>
          <div class="quotes">
            <div class="quote">“Organizou nossa rotina. A equipe entendeu tudo em 1 dia.”<div class="who">— Gestora de Loja</div></div>
            <div class="quote">“Entregou rápido e sem enrolação. Finalmente um sistema que ajuda!”<div class="who">— Empresária do varejo</div></div>
          </div>
        </div>
      </section>

      <p class="footer">👨‍💻 Desenvolvido por {DEV.get('nome','')}</p>

      <script>
        // animação de contadores com sufixo e decimais
        const ease = (t)=>1 - Math.pow(1 - t, 3);
        const DURATION = 900;
        function animateNum(el){{
          const target = parseFloat(el.getAttribute('data-target')) || 0;
          const suffix = el.getAttribute('data-suffix') || "";
          const decimals = parseInt(el.getAttribute('data-decimals')||"0",10);
          const startVal = 0;
          const start = performance.now();
          function step(now){{
            const p = Math.min(1, (now - start)/DURATION);
            const val = startVal + (target - startVal)*ease(p);
            el.textContent = val.toFixed(decimals).replace('.', ',') + suffix;
            if (p < 1) requestAnimationFrame(step);
          }}
          requestAnimationFrame(step);
        }}
        const metrics = document.querySelectorAll('.metric .num');
        const io = new IntersectionObserver((entries)=>{{
          entries.forEach(e=>{{
            if(e.isIntersecting){{
              animateNum(e.target);
              io.unobserve(e.target);
            }}
          }});
        }},{{ threshold: .4 }});
        metrics.forEach(m=>io.observe(m));

        // acessibilidade: Enter/Espaço dá um "pulse" nos cards
        document.querySelectorAll('.card[tabindex="0"]').forEach(card=>{{
          card.addEventListener('keydown', (ev)=>{{
            if(ev.key === 'Enter' || ev.key === ' '){{
              ev.preventDefault();
              card.style.transform = 'scale(0.99)';
              setTimeout(()=>card.style.transform='none', 150);
            }}
          }});
        }});
      </script>
    </div>
    """
    components.html(html_inicio, height=900, scrolling=True)

    # ============== FAQ / CONTATO (nativo do Streamlit) ==============
    st.markdown("### ❓ Perguntas frequentes")
    with st.expander("O sistema precisa de internet?"):
        st.write("Funciona localmente. Internet só é necessária para atualizações ou recursos externos que você quiser usar.")
    with st.expander("Como é o suporte?"):
        st.write("Suporte próximo e direto. Ajustes rápidos conforme sua rotina.")
    with st.expander("Consigo migrar de outro sistema?"):
        st.write("Sim. Ajudamos a importar seus registros quando possível (CSV/Excel).")
    with st.expander("Preciso de máquina potente?"):
        st.write("Não. O foco é leveza e usabilidade, pensado para computador comum.")

    st.markdown("### 📬 Fale com a gente")
    with st.form("lead_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            nome_lead = st.text_input("Seu nome")
        with col_b:
            tel_lead = st.text_input("WhatsApp (com DDD)")
        msg_lead = st.text_area("Como posso te ajudar?", height=80, placeholder="Ex.: Quero implantar na minha loja…")
        enviar = st.form_submit_button("Quero conversar")

        if enviar:
            if DEV.get("whatsapp"):
                st.success("Obrigado! Clique abaixo para abrir a conversa no WhatsApp:")
                link = DEV["whatsapp"]
                # se quiser, você pode concatenar a mensagem: link += f"&text={urllib.parse.quote(msg_lead)}"
                st.markdown(f"[Abrir WhatsApp]({link})")
            else:
                st.success("Obrigado! Em breve entraremos em contato 😉")

# ================== CADASTRO DE VENDAS ==================
elif escolha == "📋 Cadastro de Vendas":
    st.markdown("## 🛒 Cadastro de Vendas")
    st.markdown("Registre suas vendas com rapidez e acompanhe o histórico.")

    # Colunas fixas do CSV
    colunas_padrao = ["Data", "Produto", "Pagamento", "Valor", "Desconto(%)", "Valor Final"]

    # ---- Formulário de cadastro ----
    with st.form("form_venda", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            data_v = st.date_input("📅 Data", value=date.today())
        with col2:
            produto = st.text_input("📦 Produto")
        with col3:
            pagamento = st.selectbox(
                "💳 Forma de Pagamento",
                ["Pix", "Cartão Débito", "Cartão Crédito", "Dinheiro", "Outro"]
            )

        col4, col5, col6 = st.columns(3)
        with col4:
            valor = st.number_input("💰 Valor (R$)", min_value=0.0, format="%.2f", step=0.01)
        with col5:
            desconto = st.number_input("🏷 Desconto (%)", min_value=0.0, max_value=100.0, format="%.2f", step=0.1)
        with col6:
            valor_final = valor - (valor * desconto / 100)
            st.metric("💵 Valor Final", f"R$ {valor_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        enviar = st.form_submit_button("💾 Salvar Venda")

    if enviar:
        try:
            # lê atual garantindo colunas
            df_vendas = carregar_csv_garantindo_colunas(ARQ_REGISTROS, colunas_padrao)

            # nova linha
            nova = pd.DataFrame(
                [[pd.to_datetime(data_v).strftime("%Y-%m-%d"), produto, pagamento, valor, desconto, valor_final]],
                columns=colunas_padrao
            )
            # apende e grava
            df_vendas = pd.concat([df_vendas, nova], ignore_index=True)
            safe_write_csv(df_vendas, ARQ_REGISTROS)

            st.success("✅ Venda registrada com sucesso!")
            st.toast(f"Salvo em: {ARQ_REGISTROS}", icon="💾")
            st.session_state["reload_key"] += 1
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erro ao salvar vendas: {type(e).__name__}: {e}")

    # ---- Histórico de vendas + filtro ----
    df_vendas = carregar_csv_garantindo_colunas(ARQ_REGISTROS, colunas_padrao)
    if not df_vendas.empty:
        df_vendas["Data"] = pd.to_datetime(df_vendas["Data"], errors="coerce")

        colf1, colf2 = st.columns(2)
        with colf1:
            data_inicio = st.date_input("Data Inicial", value=date.today() - timedelta(days=7))
        with colf2:
            data_fim = st.date_input("Data Final", value=date.today())

        df_filtrado = df_vendas[
            df_vendas["Data"].between(pd.to_datetime(data_inicio), pd.to_datetime(data_fim))
        ].copy()

        st.markdown(f"**Vendas de {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}**")
        st.dataframe(
            df_filtrado.style.format({
                "Valor": "R$ {:.2f}",
                "Desconto(%)": "{:.2f}%",
                "Valor Final": "R$ {:.2f}"
            }),
            use_container_width=True
        )

        # --- EXCLUSÃO DE VENDAS (somente se houver linhas filtradas) ---
        st.markdown("#### 🗑️ Excluir vendas do período listado acima")
        if df_filtrado.empty:
            st.info("Nenhuma venda nesse intervalo para excluir.")
        else:
            # cria id estável temporário para mapear ao CSV original
            df_base = df_vendas.reset_index().rename(columns={"index": "__id_csv"})
            df_filtrado = df_filtrado.merge(
                df_base[["__id_csv", "Data", "Produto", "Pagamento", "Valor", "Desconto(%)", "Valor Final"]],
                on=["Data", "Produto", "Pagamento", "Valor", "Desconto(%)", "Valor Final"],
                how="left"
            )

            # Cabeçalho
            st.markdown(
                "<div style='display:flex;gap:12px;font-weight:700;color:#ddd'>"
                "<div style='width:120px'>Data</div>"
                "<div style='flex:1'>Produto</div>"
                "<div style='width:140px'>Pagamento</div>"
                "<div style='width:130px;text-align:right'>Valor Final</div>"
                "<div style='width:70px;text-align:center'>Excluir</div>"
                "</div>", unsafe_allow_html=True
            )

            # Lista com botão por linha
            for _, r in df_filtrado.sort_values("Data").iterrows():
                linha = (
                    f"<div style='display:flex;gap:12px;align-items:center;border-bottom:1px solid rgba(255,255,255,.06);padding:6px 0'>"
                    f"<div style='width:120px'>{pd.to_datetime(r['Data']).strftime('%d/%m/%Y')}</div>"
                    f"<div style='flex:1'>{(str(r['Produto']) or '').strip()}</div>"
                    f"<div style='width:140px'>{(str(r['Pagamento']) or '').strip()}</div>"
                    f"<div style='width:130px;text-align:right'>R$ {float(r['Valor Final']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + "</div>"
                    f"</div>"
                )
                c1, c2 = st.columns([1, 0.12])
                with c1:
                    st.markdown(linha, unsafe_allow_html=True)
                with c2:
                    if pd.notna(r.get("__id_csv")) and st.button("🗑️", key=f"del_venda_{int(r['__id_csv'])}", help="Excluir esta venda"):
                        _df = safe_read_csv(ARQ_REGISTROS)
                        try:
                            _df = _df.reset_index().rename(columns={"index": "__id_csv"})
                            _df = _df[_df["__id_csv"] != int(r["__id_csv"])]
                            _df = _df.drop(columns="__id_csv")
                            safe_write_csv(_df, ARQ_REGISTROS)
                            st.success("Venda excluída com sucesso.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Falha ao excluir: {e}")
    else:
        st.info("Nenhuma venda registrada ainda.")

# ================== DESPESAS ==================
elif escolha == "💸 Despesas":
    st.markdown("""
        <h1 style='color:#FF006F;text-align:center;font-weight:bold;'>💸 Controle de Despesas</h1>
        <p style='text-align:center;color:#ccc;'>Monitore seus gastos e mantenha o lucro no caminho certo</p>
    """, unsafe_allow_html=True)

    df_despesas = carregar_csv_garantindo_colunas(ARQ_DESPESAS, ["Data", "Categoria", "Descricao", "Valor"])
    # tipagem
    df_despesas["Data"] = pd.to_datetime(df_despesas["Data"], errors="coerce")
    df_despesas["Valor"] = pd.to_numeric(df_despesas["Valor"], errors="coerce").fillna(0)
    df_despesas = df_despesas.dropna(subset=["Data"])

    with st.form("form_desp"):
        c1, c2 = st.columns([1, 1])
        with c1:
            data_d = st.date_input("📅 Data da despesa", value=date.today())
        with c2:
            valor_d = st.number_input("💰 Valor (R$)", min_value=0.0, format="%.2f")

        c3, c4 = st.columns([1, 2])
        with c3:
            categoria = st.selectbox("📂 Categoria", ["Roupas", "Salário", "Aluguel", "Outros"])
        with c4:
            descricao = st.text_input("📝 Descrição")

        enviar = st.form_submit_button("💾 Salvar Despesa")

        if enviar:
            if not descricao.strip():
                st.warning("⚠️ A descrição não pode estar vazia.")
            else:
                nova = pd.DataFrame([{
                    "Data": pd.to_datetime(data_d),
                    "Categoria": categoria,
                    "Descricao": descricao.strip(),
                    "Valor": float(valor_d)
                }])
                df_despesas = pd.concat([df_despesas, nova], ignore_index=True)
                df_despesas["Data"] = pd.to_datetime(df_despesas["Data"], errors="coerce")
                df_despesas["Valor"] = pd.to_numeric(df_despesas["Valor"], errors="coerce").fillna(0)

                safe_write_csv(df_despesas, ARQ_DESPESAS)
                st.success("✅ Despesa salva com sucesso!")
                st.rerun()

    if not df_despesas.empty:
        df_exibir = df_despesas.sort_values("Data", ascending=False).copy()
        df_exibir["Data"] = pd.to_datetime(df_exibir["Data"], errors="coerce").dt.strftime("%d/%m/%Y")
        st.dataframe(df_exibir, use_container_width=True)
    else:
        st.info("Nenhuma despesa cadastrada ainda.")

# ================== RELATÓRIOS ==================
elif escolha == "📈 Relatórios":
    st.markdown("""
        <style>
          .lm-badge{
            display:inline-block; padding:6px 12px; border:1px solid rgba(255,255,255,.12);
            border-radius:999px; color:#b8b8c2; font-size:12px;
            background:rgba(255,255,255,.03);
          }
          .lm-chip{
            display:inline-block; padding:6px 10px; border-radius:999px;
            border:1px solid rgba(255,255,255,.08); font-size:12px; color:#d9d9e3;
            background:linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.02));
            margin: 0 6px 6px 0;
          }
        </style>
        <div style="text-align:center; margin: 0 0 26px 0;">
          <span class="lm-badge">📈 Relatórios & KPIs</span>
          <h1 style="
              margin:12px 0 6px 0;
              font-size:2.6em;
              font-weight:800;
              letter-spacing:-.5px;
              line-height:1.1;
              background: linear-gradient(90deg, #6a3df5, #FF006F);
              -webkit-background-clip: text;
              -webkit-text-fill-color: transparent;">
              Dashboard Financeiro
          </h1>
          <p style="margin:0;color:#cccccc;font-size:1.05em;">
              Análises interativas com Plotly • período flexível • linha do tempo diária • PDF do período.
          </p>
          <div style="margin-top:12px;">
            <span class="lm-chip">Vendas</span>
            <span class="lm-chip">Despesas</span>
            <span class="lm-chip">Lucro</span>
            <span class="lm-chip">Ticket médio</span>
            <span class="lm-chip">Formas de pagamento</span>
          </div>
        </div>
    """, unsafe_allow_html=True)
    st.divider()

    # ---------- Leitura padronizada ----------
    def ler_csv_flex(caminho):
        return safe_read_csv(caminho)

    def padroniza_vendas(df_raw):
        if df_raw.empty:
            return pd.DataFrame(columns=["Data", "Produto", "Pagamento", "Valor", "DescontoPerc", "ValorFinal"])
        df = df_raw.copy()
        df = df.rename(columns={"Desconto(%)": "DescontoPerc", "Valor Final": "ValorFinal"})
        for col in ["Data", "Produto", "Pagamento", "Valor", "DescontoPerc", "ValorFinal"]:
            if col not in df.columns:
                df[col] = None
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        for c in ["Valor", "DescontoPerc", "ValorFinal"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df["ValorFinal"] = df["ValorFinal"].fillna(df["Valor"])
        df = df.dropna(subset=["Data"])
        return df

    def padroniza_despesas(df_raw):
        if df_raw.empty:
            return pd.DataFrame(columns=["Data", "Categoria", "Descricao", "Valor"])
        df = df_raw.copy()
        for col in ["Data", "Categoria", "Descricao", "Valor"]:
            if col not in df.columns:
                df[col] = None
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
        df = df.dropna(subset=["Data"])
        return df

    df_vendas   = padroniza_vendas(ler_csv_flex(ARQ_REGISTROS))
    df_despesas = padroniza_despesas(ler_csv_flex(ARQ_DESPESAS))

    # ---------- Período ----------
    opcoes_periodo = [
        "Dia específico", "Hoje", "7 dias",
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        opcao_periodo = st.selectbox("📅 Período de Análise:", opcoes_periodo, index=0)
    with col2:
        ano_escolhido = st.number_input("Ano", min_value=2000, max_value=2100, value=date.today().year)
    with col3:
        data_especifica = st.date_input("Escolha o dia", value=date.today()) if opcao_periodo == "Dia específico" else None

    hoje = date.today()
    if opcao_periodo == "Dia específico":
        data_inicio = data_especifica
        data_fim = data_especifica
    elif opcao_periodo == "Hoje":
        data_inicio = hoje
        data_fim = hoje
    elif opcao_periodo == "7 dias":
        data_inicio = hoje - timedelta(days=6)
        data_fim = hoje
    else:
        meses_map = {
            "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, "Maio": 5, "Junho": 6,
            "Julho": 7, "Agosto": 8, "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
        }
        mes_num = meses_map[opcao_periodo]
        data_inicio = date(ano_escolhido, mes_num, 1)
        data_fim = date(ano_escolhido, mes_num, calendar.monthrange(ano_escolhido, mes_num)[1])

    st.caption(f"Período selecionado: {pd.to_datetime(data_inicio).strftime('%d/%m/%Y')} até {pd.to_datetime(data_fim).strftime('%d/%m/%Y')}")

    # ---------- Filtrar período ----------
    vendas_f = df_vendas[df_vendas["Data"].between(pd.to_datetime(data_inicio), pd.to_datetime(data_fim))].copy()
    despesas_f = df_despesas[df_despesas["Data"].between(pd.to_datetime(data_inicio), pd.to_datetime(data_fim))].copy()

    # ---------- Série diária contínua ----------
    intervalo = pd.date_range(pd.to_datetime(data_inicio), pd.to_datetime(data_fim), freq="D")
    v_dia = (vendas_f.set_index("Data").resample("D")["ValorFinal"].sum().reindex(intervalo, fill_value=0)) if not vendas_f.empty else pd.Series(0, index=intervalo)
    d_dia = (despesas_f.set_index("Data").resample("D")["Valor"].sum().reindex(intervalo, fill_value=0)) if not despesas_f.empty else pd.Series(0, index=intervalo)
    df_diario = pd.DataFrame({"Data": intervalo, "Vendas": v_dia.values.astype(float), "Despesas": d_dia.values.astype(float)})
    df_diario["Lucro"] = df_diario["Vendas"] - df_diario["Despesas"]

    # ---------- KPIs ----------
    total_bruto = float(vendas_f["Valor"].fillna(0).sum()) if "Valor" in vendas_f.columns else float(vendas_f["ValorFinal"].fillna(0).sum())
    total_liq   = float(vendas_f["ValorFinal"].fillna(0).sum())
    descontos   = float((vendas_f["Valor"].fillna(0) - vendas_f["ValorFinal"].fillna(0)).sum()) if "Valor" in vendas_f.columns else 0.0
    total_desp  = float(despesas_f["Valor"].fillna(0).sum())
    lucro       = total_liq - total_desp

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Vendas Brutas", f"R$ {total_bruto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    k2.metric("🏷 Descontos",     f"R$ {descontos:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    k3.metric("📊 Lucro",         f"R$ {lucro:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    k4.metric("💸 Despesas",      f"R$ {total_desp:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # ---------- helpers ----------
    def _fmt_brl(v):
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _plotly_base(fig, titulo=None):
        if titulo:
            fig.update_layout(title=dict(text=titulo, x=0.01, xanchor="left"))
        fig.update_layout(
            template="plotly_dark",
            margin=dict(l=10, r=160, t=50, b=40),
            hoverlabel=dict(bgcolor="rgba(20,20,20,0.9)", font_size=12),
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02, traceorder="normal", bgcolor="rgba(0,0,0,0)"),
            font=dict(size=13),
        )
        fig.update_xaxes(showgrid=False, tickformat="%d/%m", automargin=True)
        fig.update_yaxes(title=None, tickprefix="R$ ", separatethousands=True, automargin=True)
        return fig

    # ---------- Gráfico linha ----------
    df_diario_plot = df_diario.copy()
    df_diario_plot["Vendas_MA7"] = df_diario_plot["Vendas"].rolling(7, min_periods=1).mean()
    fig_line = px.line(df_diario_plot, x="Data", y=["Vendas", "Despesas", "Lucro", "Vendas_MA7"], markers=True)
    fig_line.for_each_trace(lambda tr: tr.update(line=dict(shape="spline")) if tr.name == "Vendas_MA7" else None)
    fig_line.for_each_trace(lambda t: t.update(hovertemplate="%{x|%d/%m/%Y}<br>%{y:.2f}"))
    _plotly_base(fig_line, "📅 Evolução Diária (com Média Móvel 7d)")
    st.plotly_chart(fig_line, use_container_width=True)

    # ---------- Barras comparativas ----------
    fig_bar = px.bar(df_diario_plot, x="Data", y=["Vendas", "Despesas", "Lucro"], barmode="group")
    fig_bar.for_each_trace(lambda t: t.update(hovertemplate="%{x|%d/%m/%Y}<br>%{y:.2f}"))
    _plotly_base(fig_bar, "📊 Comparativo Diário (Vendas × Despesas × Lucro)")
    st.plotly_chart(fig_bar, use_container_width=True)

    # ---------- Formas de pagamento ----------
    if not vendas_f.empty and "Pagamento" in vendas_f.columns:
        dist_pag = (vendas_f.groupby("Pagamento", dropna=False)["ValorFinal"].sum()
                    .reset_index().sort_values("ValorFinal", ascending=False))
        if not dist_pag.empty:
            fig_pag = px.pie(dist_pag, names="Pagamento", values="ValorFinal", hole=0.45)
            fig_pag.update_traces(textinfo="percent+label", hovertemplate="%{label}<br>%{value:.2f}")
            _plotly_base(fig_pag, "💳 Distribuição por Forma de Pagamento")
            st.plotly_chart(fig_pag, use_container_width=True)

    # ---------- Top 10 Produtos ----------
    if not vendas_f.empty and "Produto" in vendas_f.columns:
        top_prod = (vendas_f.groupby("Produto", dropna=False)["ValorFinal"].sum()
                    .reset_index().sort_values("ValorFinal", ascending=False).head(10))
        if not top_prod.empty:
            fig_top = px.bar(top_prod, x="Produto", y="ValorFinal")
            fig_top.update_xaxes(tickangle=-20)
            fig_top.update_traces(hovertemplate="%{x}<br>%{y:.2f}")
            _plotly_base(fig_top, "🏆 Top 10 Produtos por Receita (Valor Final)")
            st.plotly_chart(fig_top, use_container_width=True)

    # =================== EXPORTAÇÃO PDF ===================
    st.divider()
    st.caption("📄 Exportação")

    def _fmt_brl_safe(v):
        try:
            return _fmt_brl(v)
        except Exception:
            v = 0 if pd.isna(v) else float(v)
            return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _draw_header_footer(c: _canvas.Canvas, doc):
        brand = colors.HexColor("#FF006F")
        w, h = A4
        c.saveState()
        # Header
        c.setFillColor(brand); c.rect(0, h-18*mm, w, 18*mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(12*mm, h-11*mm, "Relatório Financeiro - Lana Modas")
        c.setFont("Helvetica", 9)
        c.drawRightString(
            w-12*mm, h-11*mm,
            f"Período: {pd.to_datetime(data_inicio).strftime('%d/%m/%Y')} a {pd.to_datetime(data_fim).strftime('%d/%m/%Y')}"
        )
        # Footer
        c.setFillColor(colors.grey)
        c.setFont("Helvetica", 8)
        c.drawString(12*mm, 10*mm, "Gerado por Lana Modas")
        c.drawRightString(w-12*mm, 10*mm, f"Página {doc.page}")
        c.restoreState()

    def _fig_to_story(fig, width_mm=178, ratio=16/9):
        # Requer: pip install -U kaleido
        try:
            import plotly.io as pio
            height_px = int((width_mm / 25.4) * 96 / ratio * 2)  # aproximação para manter proporção
            png = pio.to_image(fig, format="png", width=1600, height=max(600, height_px), scale=2, engine="kaleido")
            bio = BytesIO(png)
            w = min(width_mm*mm, A4[0]-24*mm)
            h = w / ratio
            return RLImage(bio, width=w, height=h)
        except Exception:
            return Paragraph(
                "Obs.: Para incluir gráficos no PDF, instale o pacote <b>kaleido</b> (pip install -U kaleido).",
                ParagraphStyle("warn", parent=getSampleStyleSheet()["BodyText"], textColor=colors.red, fontSize=9)
            )

    if st.button("Gerar Relatório PDF"):
        buffer = BytesIO()
        styles = getSampleStyleSheet()
        h2 = ParagraphStyle(
            "H2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#FF006F"),
            spaceBefore=8, spaceAfter=6
        )
        body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=9.5, leading=12)

        doc = BaseDocTemplate(
            buffer, pagesize=A4,
            leftMargin=12*mm, rightMargin=12*mm, topMargin=28*mm, bottomMargin=16*mm,
            title="Relatório Financeiro - Lana Modas", author="Lana Modas",
            subject="Vendas, Despesas e Lucro"
        )
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
        doc.addPageTemplates([PageTemplate(id='p1', frames=frame, onPage=_draw_header_footer)])

        story = []

        # KPIs
        kpi_data = [
            ["Vendas Brutas",   _fmt_brl_safe(total_bruto)],
            ["Descontos",       _fmt_brl_safe(descontos)],
            ["Despesas",        _fmt_brl_safe(total_desp)],
            ["Lucro (Líquido)", _fmt_brl_safe(lucro)],
        ]
        kpi = Table(kpi_data, colWidths=[70*mm, 40*mm], hAlign="LEFT")
        kpi.setStyle(TableStyle([
            ("FONT",        (0,0), (-1,-1), "Helvetica", 10),
            ("ALIGN",       (1,0), (1,-1),  "RIGHT"),
            ("GRID",        (0,0), (-1,-1), 0.25, colors.Color(0.75,0.75,0.75)),
            ("BOX",         (0,0), (-1,-1), 0.25, colors.Color(0.75,0.75,0.75)),
            ("BACKGROUND",  (0,0), (-1,0),  colors.whitesmoke),
            ("TEXTCOLOR",   (0,3), (-1,3),  colors.HexColor("#0b0b0e")),
            ("BACKGROUND",  (0,3), (-1,3),  colors.Color(1,0,0.435, 0.10)),
        ]))
        story += [Spacer(1, 6), kpi, Spacer(1, 10)]

        # Tabela diária
        df_tbl = df_diario.copy()
        if not df_tbl.empty:
            df_tbl["Data"] = pd.to_datetime(df_tbl["Data"]).dt.strftime("%d/%m/%Y")
            df_tbl["Vendas_fmt"]   = df_tbl["Vendas"].apply(_fmt_brl_safe)
            df_tbl["Despesas_fmt"] = df_tbl["Despesas"].apply(_fmt_brl_safe)
            df_tbl["Lucro_fmt"]    = df_tbl["Lucro"].apply(_fmt_brl_safe)

            header = [["Data", "Vendas", "Despesas", "Lucro"]]
            rows = df_tbl[["Data","Vendas_fmt","Despesas_fmt","Lucro_fmt"]].values.tolist()

            tot_row = [
                "Total",
                _fmt_brl_safe(df_tbl["Vendas"].sum()),
                _fmt_brl_safe(df_tbl["Despesas"].sum()),
                _fmt_brl_safe(df_tbl["Lucro"].sum()),
            ]
            data_table = header + rows + [tot_row]

            lt = LongTable(data_table, colWidths=[30*mm, 42*mm, 42*mm, 42*mm], repeatRows=1)
            lt.setStyle(TableStyle([
                ("FONT",          (0,0), (-1,-1), "Helvetica", 9),
                ("ALIGN",         (1,1), (-1,-2), "RIGHT"),
                ("ALIGN",         (1,-1), (-1,-1), "RIGHT"),
                ("BACKGROUND",    (0,0), (-1,0),  colors.Color(.2,.2,.2)),
                ("TEXTCOLOR",     (0,0), (-1,0),  colors.whitesmoke),
                ("ROWBACKGROUNDS",(0,1), (-1,-2), [colors.whitesmoke, colors.Color(0.97,0.97,0.97)]),
                ("GRID",          (0,0), (-1,-1), 0.25, colors.Color(0.75,0.75,0.75)),
                ("LINEABOVE",     (0,-1), (-1,-1), 0.5, colors.HexColor("#FF006F")),
                ("FONT",          (0,-1), (-1,-1), "Helvetica-Bold", 9),
            ]))
            story += [Paragraph("Detalhamento diário", h2), lt, Spacer(1, 10)]
        else:
            story += [Paragraph("Não há dados diários no período selecionado.", body), Spacer(1, 6)]

        # Gráficos (páginas seguintes)
        figs = []
        if 'fig_line' in locals(): figs.append(("Evolução diária", fig_line))
        if 'fig_bar'  in locals(): figs.append(("Comparativo diário (Vendas x Despesas x Lucro)", fig_bar))
        if 'fig_pag'  in locals(): figs.append(("Distribuição de pagamentos", fig_pag))
        if 'fig_top'  in locals(): figs.append(("Top 10 produtos", fig_top))

        if figs:
            story.append(PageBreak())
            for i, (titulo, fig) in enumerate(figs):
                story += [Paragraph(titulo, h2), _fig_to_story(fig), Spacer(1, 8)]
                if i < len(figs)-1:
                    story.append(Spacer(1, 4))

        # Build & download
        try:
            doc.build(story)
            st.download_button(
                "📄 Baixar PDF do Relatório",
                buffer.getvalue(),
                file_name=f"relatorio_lana_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Erro ao gerar PDF: {e}\nTente instalar/atualizar: pip install reportlab kaleido plotly -U")
