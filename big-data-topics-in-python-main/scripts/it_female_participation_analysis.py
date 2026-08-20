from pathlib import Path
import re
import pandas as pd
import matplotlib.pyplot as plt

# Descobre a raiz do projeto subindo a partir deste script até encontrar a pasta
# "data" — assim o script roda de qualquer diretório.
ROOT = Path(__file__).resolve().parent
while not (ROOT / "data").exists() and ROOT != ROOT.parent:
    ROOT = ROOT.parent

# Caminhos das fontes (dados brutos) e dos destinos (dados tratados e gráficos).
RAW          = ROOT / "data" / "raw"
INEP         = RAW / "inep"
DICT_FILE    = INEP / "dicionario_enade_2021.xlsx"
ESTACIO_FILE = RAW / "estacio" / "estacio_ti_2023_2025.xlsx"
OUT          = ROOT / "charts"
PROCESSED_ENADE   = ROOT / "data" / "processed" / "enade-2021"
PROCESSED_ESTACIO = ROOT / "data" / "processed" / "estacio"

# Garante que as pastas de saída existam antes de gravar qualquer arquivo.
for _d in (OUT, PROCESSED_ENADE, PROCESSED_ESTACIO):
    _d.mkdir(parents=True, exist_ok=True)

# Define o estilo visual dos gráficos (usa o tema seaborn quando disponível).
try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("ggplot")
plt.rcParams.update({"font.size": 11, "axes.titlesize": 13,
                    "axes.titleweight": "bold", "savefig.dpi": 150,
                    "figure.dpi": 110, "axes.edgecolor": "#cccccc"})

# Paleta de cores usada nos gráficos.
PURPLE, MAGENTA, GRAY = "#8E44AD", "#C2185B", "#B0BEC5"
TEAL = "#00897B"

# Legenda de fonte exibida no rodapé de cada gráfico (de acordo com a origem dos dados).
SOURCE_ENADE   = "Fonte: INEP — Microdados do ENADE 2021"
SOURCE_ESTACIO = "Fonte: Estácio — formandos em TI (2023–2025)"
SOURCE_BOTH    = "Fonte: INEP (Microdados do ENADE 2021) e Estácio (formandos 2023–2025)"

# Códigos das áreas de TI/Computação no ENADE 2021 e os rótulos exibidos nos gráficos.
IT_CODES = ["72", "79", "4004", "4005", "4006", "6409"]
IT_NAMES = {
    "72":   "Tec. Análise e\nDesenv. de Sistemas",
    "79":   "Tec. Redes de\nComputadores",
    "4004": "Ciência da Computação\n(Bacharelado)",
    "4005": "Ciência da Computação\n(Licenciatura)",
    "4006": "Sistemas de\nInformação",
    "6409": "Tec. Gestão da TI",
}

# Normaliza a capitalização dos nomes de área vindos do dicionário
# (ex.: "Ciência Da Computação" -> "Ciência da Computação").
def tidy(name: str) -> str:
    minus = {"Da", "De", "Do", "E", "Em"}
    return " ".join(w.lower() if w in minus else w for w in name.split())

# Lê o dicionário oficial do INEP e monta o mapa "código da área -> nome da área".
dic = pd.read_excel(DICT_FILE, sheet_name="DICIONÁRIO DE VARIÁVEIS", header=None)
AREA_NAME = {}
for i in range(26, len(dic)):
    if i > 26 and pd.notna(dic.iat[i, 0]):
        break
    for c in (4, 5):
        v = dic.iat[i, c]
        if pd.notna(v):
            m = re.match(r"\s*(\d+)\s*=\s*(.+)", str(v))
            if m:
                AREA_NAME[m.group(1)] = tidy(m.group(2).strip())

# Lê os três arquivos de microdados (área, sexo e idade), apenas com as colunas usadas.
arq1 = pd.read_csv(INEP / "microdados_2021_arq1.txt", sep=";", encoding="latin-1",
                    usecols=["CO_CURSO", "CO_GRUPO"])
arq5 = pd.read_csv(INEP / "microdados_2021_arq5.txt", sep=";", encoding="latin-1",
                    usecols=["CO_CURSO", "TP_SEXO"])
arq6 = pd.read_csv(INEP / "microdados_2021_arq6.txt", sep=";", encoding="latin-1",
                    usecols=["CO_CURSO", "NU_IDADE"])

# Monta o mapa "curso -> área", associa a área a cada estudante e mantém só F e M.
course2group = (arq1.drop_duplicates("CO_CURSO")
                    .set_index("CO_CURSO")["CO_GRUPO"])

arq5 = arq5.copy()
arq5["CO_GRUPO"] = arq5["CO_CURSO"].map(course2group).astype("Int64").astype(str)
arq5 = arq5[arq5["TP_SEXO"].isin(["F", "M"])]

# (a) Participação feminina x masculina dentro de cada área de TI.
ti = arq5[arq5["CO_GRUPO"].isin(IT_CODES)]
part = (ti.groupby("CO_GRUPO")["TP_SEXO"].value_counts().unstack(fill_value=0))
part["total"] = part["F"] + part["M"]
part["pct_F"] = part["F"] / part["total"] * 100
part = part.sort_values("pct_F")

tot_F, tot_M = int(part["F"].sum()), int(part["M"].sum())
pct_F_ti = tot_F / (tot_F + tot_M) * 100

# (b) Ranking de % de mulheres por área, considerando todas as áreas do ENADE 2021.
all_areas = (arq5.groupby("CO_GRUPO")["TP_SEXO"].value_counts().unstack(fill_value=0))
all_areas["pct_F"] = all_areas["F"] / (all_areas["F"] + all_areas["M"]) * 100
all_areas = all_areas.sort_values("pct_F")

# (c) Faixa etária dos concluintes de TI (todos os sexos — ver nota no gráfico).
arq6 = arq6.copy()
arq6["CO_GRUPO"] = arq6["CO_CURSO"].map(course2group).astype("Int64").astype(str)
it_ages = arq6[arq6["CO_GRUPO"].isin(IT_CODES)]["NU_IDADE"].dropna()
age_bins = pd.cut(it_ages, bins=[0, 17, 24, 30, 40, 200],
                    labels=["até 17", "18-24", "25-30", "31-40", "40+"])
age_counts = age_bins.value_counts().reindex(["até 17", "18-24", "25-30", "31-40", "40+"]).dropna()

# (d) Estácio: remove duplicatas e calcula a participação feminina.
estacio_raw = pd.read_excel(ESTACIO_FILE).drop_duplicates()
estacio_pct_f = (estacio_raw["TP_SEXO"] == "F").mean() * 100
estacio = estacio_raw[estacio_raw["TP_SEXO"] == "F"]
estacio_by_course = estacio["CURSO"].value_counts().sort_values()

# Salva os datasets tratados (.csv e .xlsx) das mulheres em TI — ENADE e Estácio.
women_it = ti[ti["TP_SEXO"] == "F"].copy()
women_it["NOME_CURSO"] = women_it["CO_GRUPO"].map(AREA_NAME)
women_it.to_csv(PROCESSED_ENADE / "Enade2021_IT_Women.csv", index=False)
women_it.to_excel(PROCESSED_ENADE / "Enade2021_IT_Women.xlsx", index=False)
print(f"Dataset saved: data/processed/enade-2021/Enade2021_IT_Women.* "
        f"({len(women_it):,} women in IT)")

estacio.to_csv(PROCESSED_ESTACIO / "Estacio_IT_Women.csv", index=False)
estacio.to_excel(PROCESSED_ESTACIO / "Estacio_IT_Women.xlsx", index=False)
print(f"Dataset saved: data/processed/estacio/Estacio_IT_Women.* "
        f"({len(estacio):,} women at Estácio)")

# Cada função g*_ desenha um gráfico no eixo (ax) recebido.

# Rosca com o percentual feminino no total de TI.
def g1_donut(ax):
    ax.pie([pct_F_ti, 100 - pct_F_ti],
            labels=[f"Mulheres\n{pct_F_ti:.1f}%", f"Homens\n{100-pct_F_ti:.1f}%"],
            colors=[PURPLE, GRAY], startangle=90,
            wedgeprops=dict(width=0.42, edgecolor="white"),
            textprops=dict(fontsize=11, fontweight="bold"))
    ax.text(0, 0, f"{tot_F:,}\nmulheres".replace(",", "."),
            ha="center", va="center", fontsize=12, fontweight="bold", color=PURPLE)
    ax.set_title("Participação feminina no total de TI — ENADE 2021")

# Barras empilhadas com a proporção de mulheres e homens por curso de TI.
def g2_share(ax):
    names = [IT_NAMES[c].replace("\n", " ") for c in part.index]
    pf = part["pct_F"].values
    ax.barh(names, pf, color=PURPLE, label="Mulheres")
    ax.barh(names, 100 - pf, left=pf, color=GRAY, label="Homens")
    for i, v in enumerate(pf):
        ax.text(v / 2, i, f"{v:.0f}%", ha="center", va="center",
                color="white", fontweight="bold", fontsize=9)
        ax.text(v + (100 - v) / 2, i, f"{100-v:.0f}%", ha="center", va="center",
                color="white", fontweight="bold", fontsize=9)
    ax.set_xlim(0, 100)
    ax.set_xlabel("% de concluintes")
    ax.set_title("Participação feminina x masculina por curso de TI")
    ax.legend(loc="lower right", fontsize=9, framealpha=0.9)

# Barras com o número absoluto de mulheres concluintes por curso de TI.
def g3_count(ax):
    names = [IT_NAMES[c].replace("\n", " ") for c in part.index]
    ax.barh(names, part["F"].values, color=MAGENTA)
    for i, v in enumerate(part["F"].values):
        ax.text(v + max(part["F"]) * 0.01, i, f"{int(v):,}".replace(",", "."),
                va="center", fontweight="bold", fontsize=9)
    ax.set_xlabel("Nº de mulheres concluintes")
    ax.set_title("Mulheres concluintes por curso de TI — ENADE 2021")
    ax.margins(x=0.13)

# Ranking de % de mulheres entre todas as áreas, destacando as de TI em rosa.
def g4_rank(ax):
    names = [AREA_NAME.get(c, c) for c in all_areas.index]
    colors = [MAGENTA if c in IT_CODES else GRAY for c in all_areas.index]
    ax.barh(names, all_areas["pct_F"].values, color=colors)
    ax.axvline(50, color="#555", ls="--", lw=1)
    ax.set_xlabel("% de mulheres")
    ax.set_title("TI é a área MENOS feminina do ENADE 2021 (rosa = TI)")
    ax.tick_params(axis="y", labelsize=7.5)
    ax.set_xlim(0, 100)

# Barras com o número de mulheres formandas em TI na Estácio, por curso.
def g5_estacio(ax):
    names = [c.title() for c in estacio_by_course.index]
    ax.barh(names, estacio_by_course.values, color=PURPLE)
    for i, v in enumerate(estacio_by_course.values):
        ax.text(v + 0.2, i, str(int(v)), va="center", fontweight="bold", fontsize=9)
    ax.set_xlabel("Nº de mulheres formandas")
    ax.set_title(f"Mulheres formandas em TI — Estácio "
                    f"({estacio_pct_f:.0f}% do total · 2023–2025)")
    ax.margins(x=0.16)

# Barras com a faixa etária dos concluintes de TI e a nota metodológica.
def g6_age(ax):
    ax.bar(age_counts.index.astype(str), age_counts.values, color=TEAL)
    ymax = age_counts.max()
    for i, v in enumerate(age_counts.values):
        ax.annotate(f"{int(v):,}".replace(",", "."), (i, v + ymax * 0.01),
                    ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_ylabel("Nº de concluintes")
    ax.set_title("Faixa etária dos concluintes de TI — ENADE 2021")
    ax.text(0.5, -0.22, "Nota: todos os sexos. O microdado não permite cruzar "
            "sexo×idade por indivíduo (LGPD).",
            transform=ax.transAxes, ha="center", fontsize=8, color="#666")

# Lista (nome do arquivo, função de desenho, fonte dos dados) de cada gráfico.
CHARTS = [
    ("01_total_participation",     g1_donut,   SOURCE_ENADE),
    ("02_participation_by_course", g2_share,   SOURCE_ENADE),
    ("03_women_by_course",         g3_count,   SOURCE_ENADE),
    ("04_areas_ranking",           g4_rank,    SOURCE_ENADE),
    ("05_estacio_by_course",       g5_estacio, SOURCE_ESTACIO),
    ("06_it_age_range",            g6_age,     SOURCE_ENADE),
]

# Gera e salva cada gráfico individual em charts/, com a legenda de fonte no rodapé.
for name, func, source in CHARTS:
    fig, ax = plt.subplots(figsize=(8, 5.2))
    func(ax)
    fig.tight_layout()
    fig.text(0.99, 0.01, source, ha="right", va="bottom",
             fontsize=7.5, style="italic", color="#888")
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight")
    plt.close(fig)
    print(f"saved: charts/{name}.png")

# Monta o painel 2x3 reunindo todos os gráficos em uma única imagem.
fig, axes = plt.subplots(2, 3, figsize=(20, 12))
fig.suptitle("Participação feminina na área de TI — ENADE 2021 e Estácio",
                fontsize=18, fontweight="bold")
for (name, func, source), ax in zip(CHARTS, axes.flat):
    func(ax)
fig.tight_layout(rect=[0, 0.02, 1, 0.97])
fig.text(0.99, 0.01, SOURCE_BOTH, ha="right", va="bottom",
         fontsize=10, style="italic", color="#888")
fig.savefig(OUT / "00_overview_panel.png", bbox_inches="tight")
plt.close(fig)
print("saved: charts/00_overview_panel.png")

# Imprime um resumo dos números no terminal.
print("\n=== SUMMARY ===")
print(f"Women IT graduates: {tot_F:,}  | Men: {tot_M:,}  | %F = {pct_F_ti:.1f}%")
for c in part.index:
    print(f"  {IT_NAMES[c].replace(chr(10),' '):34s} {part.loc[c,'pct_F']:5.1f}% "
            f"(F={int(part.loc[c,'F'])}, M={int(part.loc[c,'M'])})")
