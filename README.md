# Radar de Demandas — Google Trends real

Fecha o primeiro elo da lista de evolução: sinais de "Trends" deixam de
ser mockados e passam a vir do Google Trends de verdade, atualizados
toda segunda de manhã, sem precisar de servidor pago.

## Como funciona

```
GitHub Actions (roda toda segunda, 07h BR)
        |
        v
  fetch_trends.py  --usa pytrends-->  Google Trends
        |
        v
 signals-trends.json  (fica salvo no seu repositório)
        |
        v
radar-de-demandas.html  --fetch()-->  le o JSON direto do GitHub
```

Não tem backend rodando 24/7: o GitHub Actions "acorda" uma vez por
semana, busca os dados, e salva o resultado como um arquivo no seu
próprio repositório. O HTML só precisa saber a URL desse arquivo.

## Passo a passo

1. Crie um repositório novo no GitHub (pode ser público), por exemplo
   `radar-trends`.
2. Suba estes 5 itens para a raiz do repositório:
   - `fetch_trends.py`
   - `keywords.json`
   - `requirements.txt`
   - `.github/workflows/trends.yml`
   - `radar-de-demandas.html`
3. Edite `keywords.json` com os termos que você quer monitorar
   (comece com os 8 que já deixei, ajuste com o tempo).
4. No GitHub: aba **Actions** → habilite os workflows do repositório.
5. Rode uma vez manualmente: Actions → "Atualizar sinais de Google
   Trends" → **Run workflow**. Isso gera o primeiro
   `signals-trends.json` no repositório (leva 1-2 min, por causa da
   pausa entre cada termo pra não levar bloqueio do Google).
6. Copie a URL raw do arquivo gerado. Formato:
   `https://raw.githubusercontent.com/SEU-USUARIO/radar-trends/main/signals-trends.json`
7. Abra `radar-de-demandas.html`, ache a constante `REAL_TRENDS_URL`
   perto do topo do `<script>`, e cole essa URL no lugar do
   placeholder.
8. Reabra o `radar-de-demandas.html` no navegador. Se a aba "Sinais"
   mostrar "Trends real conectado — N sinais atualizados", funcionou.

Depois disso, toda segunda de manhã o GitHub Actions atualiza o JSON
sozinho, e o HTML sempre busca a versão mais recente quando você abre
a página.

## Ajustes que valem a pena depois

- **Frequência**: para testar sem esperar a próxima segunda, use o
  botão "Run workflow" manualmente quantas vezes quiser.
- **Mais termos**: cada termo adicionado em `keywords.json` soma
  ~8 segundos de execução (é a pausa de segurança entre chamadas).
  Com 8 termos o job roda em ~1-2 min; com 30 termos, uns 5 min —
  ainda tranquilo pro limite gratuito do GitHub Actions.
- **Hospedar o HTML**: hoje você abre o arquivo localmente. Se
  quiser um link fixo pra acessar de qualquer lugar (celular
  incluso), ative o GitHub Pages no mesmo repositório e o
  `radar-de-demandas.html` vira uma URL pública.
- **Reclame Aqui e Notion** ficam de fora deste pacote de propósito
  (ver observações que te passei sobre viabilidade e termos de uso).
