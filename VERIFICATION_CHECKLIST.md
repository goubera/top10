# ✅ Checklist de Vérification - Configuration API DexScreener

## État Actuel

### ✅ Fait
- [x] Problème diagnostiqué (API DexScreener requiert authentification)
- [x] Solution implémentée (système multi-source avec fallbacks)
- [x] Tests passés (4/4 tests unitaires)
- [x] Documentation mise à jour
- [x] Code committé et pushé
- [x] **Clé API DexScreener ajoutée aux GitHub Secrets** ← VOUS VENEZ DE FAIRE ÇA

### 🔄 À Vérifier Maintenant

## 1️⃣ VÉRIFICATION IMMÉDIATE: Déclencher Test Manuel

### Accéder aux GitHub Actions
```
🔗 https://github.com/goubera/top10/actions
```

### Déclencher le Workflow
1. Dans la liste de gauche, cliquez sur **"Daily Solana Top10"**
2. En haut à droite, cliquez sur **"Run workflow"** (bouton vert)
3. Sélectionnez la branche: `claude/debug-data-collection-011CUdrF9q15vqP3t4jumJKX`
4. Cliquez sur **"Run workflow"**
5. Rafraîchissez la page après quelques secondes

### Surveiller l'Exécution
- Cliquez sur le run qui apparaît (en haut de la liste)
- Cliquez sur "collect" pour voir les détails
- Développez "Run collector" pour voir les logs

## 2️⃣ LOGS À VÉRIFIER

### ✅ Signes de Succès

Vous devriez voir dans les logs:

```
INFO:data_sources:Trying DexScreener...
INFO:data_sources:✓ DexScreener succeeded with XX pairs
INFO:__main__:Starting data collection for 2025-10-31
INFO:__main__:Received XX pairs from data source
INFO:__main__:Found XX unique tokens
INFO:__main__:Selected top 10 pairs by volume
INFO:__main__:✓ Successfully wrote data/top10_2025-10-31.csv with 10 rows
```

### ✅ Validation CSV
```
✓ CSV file found: data/top10_2025-10-31.csv
✓ Has 11 rows (1 header + 10 data)
```

### ✅ Commit Automatique
```
Configure git & ensure main branch
Stage generated files
Rebase & push
```

### ❌ Si Erreur API Key

```
ERROR:data_sources:DexScreener source failed: 403 Client Error: Forbidden
WARNING:data_sources:✗ DexScreener failed: ...
INFO:data_sources:Trying Raydium...
```

**Si vous voyez ça:**
1. Vérifiez que le secret GitHub s'appelle exactement: `DEXSCREENER_API_KEY`
2. Vérifiez qu'il n'y a pas d'espaces avant/après la clé
3. Vérifiez que la clé est valide sur https://dexscreener.com/

## 3️⃣ VÉRIFICATION DES FICHIERS

Après un run réussi, allez dans le repo et vérifiez:

### Nouveau CSV avec Données
```
📁 solana-meme-top10-collector/data/top10_2025-10-31.csv
```

**Ouvrez-le et vérifiez:**
- ✅ Il doit avoir plus d'1 ligne (pas juste le header!)
- ✅ Colonnes: date, chain, baseToken, volume24hUsd, etc.
- ✅ 10 lignes de données réelles

**Comparez avec les anciens:**
```
📁 solana-meme-top10-collector/data/top10_2025-09-28.csv  ← Vide (1 ligne)
📁 solana-meme-top10-collector/data/top10_2025-10-31.csv  ← Plein (11 lignes) ✅
```

### Fichier de Résumé
```
📁 solana-meme-top10-collector/data/run_summary.json
```

**Devrait contenir:**
```json
{
  "date": "2025-10-31",
  "success": true,
  "rows_collected": 10,
  "csv_file": "data/top10_2025-10-31.csv"
}
```

## 4️⃣ SI TOUT EST ✅

### Actions à Faire

1. **Merger vers main:**
   ```bash
   git checkout main
   git merge claude/debug-data-collection-011CUdrF9q15vqP3t4jumJKX
   git push origin main
   ```

2. **Surveiller la collecte automatique:**
   - Prochaine exécution: **Demain à 06:10 UTC** (08:10 Paris)
   - Vérifier que les nouveaux CSV sont créés quotidiennement

3. **Nettoyer les vieux CSV vides (optionnel):**
   - Les CSV de septembre sont vides
   - Vous pouvez les supprimer ou les garder comme référence

## 5️⃣ SI PROBLÈME ❌

### Vérifications Supplémentaires

1. **Vérifier le nom du secret:**
   ```
   GitHub → Settings → Secrets and variables → Actions
   Nom exact: DEXSCREENER_API_KEY
   ```

2. **Tester localement (optionnel):**
   ```bash
   cd solana-meme-top10-collector
   export DEXSCREENER_API_KEY="votre-cle"
   python test_api_connection.py
   ```

3. **Vérifier le statut de l'API:**
   - Visitez: https://dexscreener.com/
   - Vérifiez votre dashboard API

4. **Logs détaillés:**
   - GitHub Actions → Run échoué → "Run collector"
   - Regardez l'erreur exacte

## 📊 Dashboard de Monitoring

Après le premier run réussi:

| Métrique | Attendu | Comment vérifier |
|----------|---------|------------------|
| Status workflow | ✅ Success | GitHub Actions page |
| CSV créé | ✅ Oui | Vérifier `data/top10_YYYY-MM-DD.csv` |
| Lignes CSV | 11 (1+10) | Ouvrir le fichier |
| run_summary.json | success: true | Ouvrir le fichier |
| Commit auto | ✅ Oui | Vérifier commits récents |

## 🎯 Résultat Attendu Final

```
✅ Workflow exécuté avec succès
✅ CSV créé avec 10 lignes de données
✅ run_summary.json indique success: true
✅ Commit automatique créé
✅ Prêt pour la collecte quotidienne automatique
```

---

## 🆘 Besoin d'Aide?

**Fichiers à consulter:**
- `TEST_INSTRUCTIONS.md` - Guide détaillé de test
- `DIAGNOSIS.md` - Diagnostic complet du problème
- `README.md` - Documentation générale

**En cas de problème, partagez:**
- Les logs du workflow GitHub Actions
- Le contenu de `data/run_summary.json`
- Le message d'erreur exact
