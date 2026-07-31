"""
fetch_trends.py
Captura sinais de Google Trends para o Radar de Demandas
("O Estrategista de Dados").

O QUE FAZ
- Le uma lista de termos em keywords.json
- Para cada termo, busca a serie de interesse ao longo do tempo
  (ultimas semanas) e as consultas relacionadas em ascensao
- Calcula uma "forca" de 0 a 100 para cada sinal
- Escreve tudo em signals-trends.json, no MESMO formato que o
  array `signalsData` do Radar de Demandas (Ideias.html), pronto
  para o front-end consumir via fetch()

POR QUE RODAR FORA DO NAVEGADOR
O Google nao oferece API oficial do Trends. A biblioteca pytrends
imita requisicoes do site trends.google.com e por isso PRECISA
rodar num ambiente com IP residencial/de servidor "normal" e
acesso irrestrito a internet -- nunca vai funcionar direto de
dentro de um artifact HTML (bloqueio de CORS + risco de o Google
marcar a origem como bot). Este script foi pensado para rodar:
  1) na sua maquina, manualmente ou via cron; ou
  2) num workflow agendado do GitHub Actions (ver
     .github/workflows/trends.yml neste mesmo pacote)

USO
    pip install pytrends
    python fetch_trends.py
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from pytrends.request import TrendReq

HERE = Path(__file__).parent
KEYWORDS_FILE = HERE / "keywords.json"
OUTPUT_FILE = HERE / "signals-trends.json"

# Janela de tempo: ultimos 3 meses, Brasil
TIMEFRAME = "today 3-m"
GEO = "BR"

# Pausa entre chamadas para reduzir risco de bloqueio (rate limit do Google)
SLEEP_BETWEEN_CALLS_SECONDS = 8


def load_keywords() -> list[str]:
    if not KEYWORDS_FILE.exists():
        raise FileNotFoundError(
            f"Nao encontrei {KEYWORDS_FILE}. Crie o arquivo com uma lista "
            'de termos, ex: ["curso de marketing digital", "consultoria de dados"]'
        )
    with open(KEYWORDS_FILE, encoding="utf-8") as f:
        return json.load(f)


def compute_strength(series: list[int]) -> int:
    """Media das ultimas 4 semanas, 0-100 (mesma escala do Trends)."""
    if not series:
        return 0
    last4 = series[-4:] if len(series) >= 4 else series
    return round(sum(last4) / len(last4))


def compute_growth_pct(series: list[int]) -> float:
    """Variacao % entre a media das ultimas 4 semanas e as 4 anteriores."""
    if len(series) < 8:
        return 0.0
    recent = sum(series[-4:]) / 4
    previous = sum(series[-8:-4]) / 4
    if previous == 0:
        return 100.0 if recent > 0 else 0.0
    return round((recent - previous) / previous * 100, 1)


def build_signal(idx: int, keyword: str, pytrends: TrendReq) -> dict | None:
    pytrends.build_payload([keyword], timeframe=TIMEFRAME, geo=GEO)

    iot = pytrends.interest_over_time()
    if iot.empty:
        print(f'  [aviso] sem dados de interesse para "{keyword}"')
        return None
    series = iot[keyword].tolist()

    strength = compute_strength(series)
    growth = compute_growth_pct(series)

    # Consulta relacionada em maior ascensao (se existir)
    rising_query = None
    try:
        related = pytrends.related_queries()
        rising_df = related.get(keyword, {}).get("rising")
        if rising_df is not None and not rising_df.empty:
            rising_query = rising_df.iloc[0]["query"]
    except Exception as e:
        print(f'  [aviso] related_queries falhou para "{keyword}": {e}')

    # Regiao com maior interesse (opcional, reforca o angulo de "cidade escondida")
    top_region = None
    try:
        by_region = pytrends.interest_by_region(resolution="REGION", inc_geo_code=False)
        if not by_region.empty:
            top_region = by_region[keyword].idxmax()
    except Exception as e:
        print(f'  [aviso] interest_by_region falhou para "{keyword}": {e}')

    if growth > 15:
        headline = f'"{keyword}" em alta: buscas sobem {growth}% em 4 semanas'
    elif growth < -15:
        headline = f'"{keyword}" em queda: buscas caem {abs(growth)}% em 4 semanas'
    else:
        headline = f'"{keyword}" estavel, com forca de busca em {strength}/100'

    desc_parts = [f"Interesse medio de busca: {strength}/100 (Brasil, ultimos 3 meses)."]
    if rising_query:
        desc_parts.append(f'Consulta relacionada em maior ascensao: "{rising_query}".')
    if top_region:
        desc_parts.append(f"Estado com maior interesse: {top_region}.")
    desc = " ".join(desc_parts)

    return {
        "id": idx,
        "type": "trend",
        "title": headline,
        "desc": desc,
        "source": "Google Trends",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "strength": strength,
    }


def main():
    keywords = load_keywords()
    pytrends = TrendReq(hl="pt-BR", tz=180)  # tz=180 -> America/Sao_Paulo (UTC-3)

    signals = []
    for i, kw in enumerate(keywords, start=1):
        print(f"[{i}/{len(keywords)}] buscando: {kw}")
        try:
            signal = build_signal(i, kw, pytrends)
            if signal:
                signals.append(signal)
        except Exception as e:
            print(f'  [erro] falhou para "{kw}": {e}')
        time.sleep(SLEEP_BETWEEN_CALLS_SECONDS)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(signals, f, ensure_ascii=False, indent=2)

    print(f"\nOK: {len(signals)} sinais escritos em {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
