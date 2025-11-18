# 🔑 Comment obtenir votre clé API Birdeye (GRATUIT)

## Pourquoi Birdeye ?

Birdeye offre un **FREE tier généreux** avec **30,000 crédits par mois** GRATUITS.
C'est largement suffisant pour :
- Collecter les données quotidiennement
- Tester et développer l'application
- Tracker jusqu'à 100+ tokens par jour

**Pas de carte de crédit requise !**

---

## 📋 Étapes pour obtenir votre clé API

### 1. Créer un compte Birdeye

1. Aller sur **https://birdeye.so**
2. Cliquer sur **"Sign Up"** ou **"Get API Key"**
3. S'inscrire avec votre email (gratuit, pas de CB)

### 2. Accéder à l'API Dashboard

1. Une fois connecté, aller sur **https://birdeye.so/user/api**
2. Ou naviguer : **Profile → API** dans le menu

### 3. Créer votre première clé API

1. Cliquer sur **"Create API Key"** ou **"New API Key"**
2. Donner un nom à votre clé (ex: "Solana Tracker")
3. Copier la clé générée (elle ressemble à `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

⚠️ **Important** : Sauvegardez votre clé immédiatement, elle ne sera plus affichée !

---

## ⚙️ Configuration dans l'application

### Option 1 : Fichier `.env` (Recommandé)

```bash
cd solana-tracker-web/backend
echo "BIRDEYE_API_KEY=votre_cle_ici" > .env
```

### Option 2 : Variable d'environnement

**Linux/Mac:**
```bash
export BIRDEYE_API_KEY=votre_cle_ici
```

**Windows:**
```powershell
set BIRDEYE_API_KEY=votre_cle_ici
```

---

## ✅ Vérifier que ça fonctionne

```bash
cd solana-tracker-web/backend
python collector.py
```

Si tout est OK, vous verrez :
```
✅ Birdeye API key detected
✅ Fetched X tokens from Birdeye
```

---

## 📊 Limites du FREE Tier

| Feature | FREE Tier |
|---------|-----------|
| **Crédits/mois** | 30,000 |
| **Rate limit** | ~5-10 requêtes/sec |
| **Endpoints** | Tous (trending, prices, etc.) |
| **Support** | Documentation en ligne |

**Estimation** :
- 1 collecte = ~100 crédits
- 30,000 / 100 = **300 collectes par mois**
- 300 / 30 = **10 collectes par jour** possibles

Plus que suffisant pour une collecte quotidienne !

---

## 🚫 Que se passe-t-il SANS clé API ?

L'application fonctionne quand même en **mode fallback** :
- ✅ Dashboard fonctionne
- ✅ Données de test réalistes
- ⚠️  Pas de vraies données en temps réel

Vous verrez :
```
⚠️  FALLBACK MODE: Generating mock data
   No API key detected - using simulated data
```

---

## 🔒 Sécurité

**NE JAMAIS commit votre clé API dans Git !**

Le fichier `.env` est déjà dans `.gitignore` pour vous protéger.

Si vous avez accidentellement exposé votre clé :
1. Aller sur birdeye.so/user/api
2. Révoquer la clé compromise
3. Créer une nouvelle clé

---

## 🆘 Problèmes courants

### Erreur 403 Forbidden

**Cause** : Clé API invalide ou expirée

**Solution** :
```bash
# Vérifier que la clé est bien définie
echo $BIRDEYE_API_KEY

# Recréer le fichier .env
cd backend
echo "BIRDEYE_API_KEY=votre_nouvelle_cle" > .env
```

### Erreur 429 Too Many Requests

**Cause** : Limite de rate dépassée

**Solution** :
- Réduire la fréquence de collecte
- Attendre quelques minutes
- Vérifier que vous n'avez pas plusieurs processus qui appellent l'API

### "No data from Birdeye API"

**Cause** : Endpoint indisponible ou format de réponse changé

**Solution** :
- Vérifier que Birdeye API est up : https://status.birdeye.so
- L'application basculera automatiquement en mode fallback
- Ouvrir une issue GitHub si le problème persiste

---

## 🎯 Alternatives (si Birdeye ne fonctionne pas)

### 1. Helius (Gratuit aussi)
- 100k requêtes/mois gratuit
- https://www.helius.dev

### 2. Moralis
- 40k API calls/mois gratuit
- https://moralis.io

### 3. CoinGecko
- Tier gratuit disponible
- https://www.coingecko.com/api

---

## 📞 Support

- **Documentation Birdeye** : https://docs.birdeye.so
- **Status API** : https://status.birdeye.so
- **Discord** : https://discord.gg/birdeye

---

**Bon tracking des memecoins Solana ! 🚀**
