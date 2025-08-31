# Solana Meme Coin — Daily Top 10 Collector

Collecte quotidienne des **Top 10 nouveaux tokens Solana** (par performance early) et stockage en CSV.

## 1) Ce que fait ce projet
- Récupère les **nouveaux pairs** via **Dexscreener**.
- (Optionnel) Enrichit via **Birdeye** (holders, sécurité).
- Exporte un CSV quotidien dans `data/` (ex: `top10_YYYY-MM-DD.csv`).

## 2) Installation locale
> Toujours se placer dans le bon dossier :
```bash
cd solana-meme-top10-collector
```
Créer un venv + installer :
```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```
Copier l'env et renseigner les clés :
```bash
cp .env.example .env
```
Puis lancer :
```bash
python collector.py
```

## 3) Planification CI (GitHub Actions)
- Le workflow tourne **chaque jour à 08:10 Europe/Paris** (cron `06:10 UTC`).
- Les CSV du jour sont commités dans `data/`.

### Secrets à créer sur GitHub (Settings → Secrets → Actions)
- `DEXSCREENER_API_KEY`
- `BIRDEYE_API_KEY`
- `HELIUS_API_KEY` *(optionnel en V1)*

## 4) Pourquoi Helius est optionnel en V1 ?
Dexscreener + Birdeye suffisent pour un Top 10 quotidien.  
Helius sert en **V2** pour le **temps réel** (webhooks) et des signaux on-chain plus précoces (mints, migrations).

## 5) Roadmap V2
- Calcul **ATH multiple** dans la **première heure** (OHLCV minute Birdeye).
- Ajout Helius (webhooks) pour temps réel.
- Petit dashboard Streamlit pour visualiser les métriques.
