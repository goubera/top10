# 🚀 Déploiement Gratuit

## Option 1 : Render.com (Recommandé - Plus simple)

### Étapes :

1. **Aller sur [render.com](https://render.com)** et créer un compte (gratuit)

2. **Créer un nouveau Web Service** :
   - Click "New +" → "Web Service"
   - Connecter votre GitHub repo `goubera/top10`
   - Branch : `claude/test-functionality-01KsngqPVpJiuKKFoUqXBWT3`
   - Root directory : `solana-tracker-web`

3. **Configuration** :
   - **Name** : `solana-token-tracker` (ou autre)
   - **Runtime** : Python 3
   - **Build Command** : `pip install -r backend/requirements.txt && python backend/create_mock_data.py`
   - **Start Command** : `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan** : Free (gratuit)

4. **Variables d'environnement** (optionnel) :
   - Ajouter `BIRDEYE_API_KEY` si vous en avez une

5. **Deploy** !

**Résultat** : Vous aurez une URL comme :
`https://solana-token-tracker.onrender.com/static/index.html`

⏱️ **Temps** : 5-10 minutes
💰 **Prix** : GRATUIT (avec limitations : sleep après 15min inactivité)

---

## Option 2 : Railway.app

1. **Aller sur [railway.app](https://railway.app)** et se connecter avec GitHub

2. **New Project** → **Deploy from GitHub repo**
   - Sélectionner `goubera/top10`
   - Branch : `claude/test-functionality-01KsngqPVpJiuKKFoUqXBWT3`

3. **Settings** :
   - **Root Directory** : `solana-tracker-web`
   - **Start Command** : `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Environment Variables** (optionnel) :
   - `BIRDEYE_API_KEY` = votre clé

5. **Deploy** !

**Résultat** : URL automatique générée

💰 **Prix** : 500 heures gratuites/mois (largement suffisant)

---

## Option 3 : Vercel (Simple mais limitations)

1. **Installer Vercel CLI** :
```bash
npm install -g vercel
```

2. **Dans le dossier du projet** :
```bash
cd solana-tracker-web
vercel
```

3. **Suivre les prompts**

**Note** : Vercel a des limitations pour les apps Python avec base de données. Render ou Railway sont meilleurs pour ce projet.

---

## Option 4 : Heroku (Plus complexe)

1. **Créer compte sur [heroku.com](https://heroku.com)**

2. **Installer Heroku CLI** :
```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

3. **Déployer** :
```bash
cd solana-tracker-web
heroku login
heroku create solana-token-tracker
git push heroku claude/test-functionality-01KsngqPVpJiuKKFoUqXBWT3:main
```

💰 **Prix** : Gratuit mais nécessite carte bancaire pour vérification

---

## ⚡ La plus RAPIDE : Render.com

**Je recommande Render** car :
- ✅ 100% gratuit sans CB
- ✅ Interface simple
- ✅ Déploiement automatique depuis GitHub
- ✅ Logs faciles à consulter
- ✅ Support SQLite out-of-the-box

**Inconvénients** :
- ⚠️ Le service "s'endort" après 15min d'inactivité
- ⚠️ Premier chargement peut prendre 30-60s

---

## 📱 Accès après déploiement

Une fois déployé, vous aurez une URL publique :
```
https://votre-app.onrender.com/static/index.html
```

Partageable avec n'importe qui ! 🎉
