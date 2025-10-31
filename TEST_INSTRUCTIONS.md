# Instructions de Test - DexScreener API Key

## ✅ Étapes Complétées

- [x] Clé API DexScreener ajoutée aux GitHub Secrets
- [x] Code mis à jour avec système multi-source
- [x] Tests passés localement
- [x] Changements committés et poussés

## 🧪 Comment Tester Maintenant

### Option 1: Déclencher le Workflow Manuellement (RECOMMANDÉ)

1. **Aller sur GitHub Actions**:
   - Visitez: https://github.com/goubera/top10/actions
   - Cliquez sur le workflow "Daily Solana Top10" dans la liste de gauche

2. **Déclencher manuellement**:
   - Cliquez sur le bouton "Run workflow" (en haut à droite)
   - Sélectionnez la branche `claude/debug-data-collection-011CUdrF9q15vqP3t4jumJKX`
   - Cliquez "Run workflow"

3. **Surveiller les logs**:
   - Attendez que le workflow démarre (quelques secondes)
   - Cliquez sur le run qui vient d'être créé
   - Regardez les logs en temps réel

### Option 2: Attendre la Collecte Automatique

Le workflow s'exécute automatiquement tous les jours à **06:10 UTC** (environ 08:10 heure de Paris).

La prochaine exécution automatique sera demain matin.

## 📊 Que Vérifier dans les Logs

### ✅ Logs de Succès Attendus

```
INFO:data_sources:Trying DexScreener...
INFO:data_sources:✓ DexScreener succeeded with X pairs
INFO:__main__:Starting data collection for 2025-10-31
INFO:__main__:Received X pairs from data source
INFO:__main__:Found X unique tokens
INFO:__main__:Selected top 10 pairs by volume
INFO:__main__:✓ Successfully wrote data/top10_2025-10-31.csv with 10 rows
```

### ❌ Si Erreur d'API Key

```
ERROR:data_sources:DexScreener source failed: 403 Client Error: Forbidden
ERROR:data_sources:All data sources failed...
```

**Solution**: Vérifier que:
- Le secret s'appelle exactement `DEXSCREENER_API_KEY` (sensible à la casse)
- La clé API est valide et non expirée
- Pas d'espaces avant/après la clé

## 🔍 Vérification des Résultats

Après un run réussi, vérifier:

1. **Fichier CSV créé**:
   - Chemin: `solana-meme-top10-collector/data/top10_YYYY-MM-DD.csv`
   - Doit contenir 11 lignes (header + 10 lignes de données)

2. **Fichier de résumé**:
   - Chemin: `solana-meme-top10-collector/data/run_summary.json`
   - Doit contenir: `"success": true`

3. **Commit automatique**:
   - Un nouveau commit `chore(data): add daily artifacts [skip ci]` doit apparaître
   - Contenant les nouveaux fichiers CSV

## 🐛 Troubleshooting

### Problème: "API key not working"
```bash
# Test local (si vous avez accès à la clé)
cd solana-meme-top10-collector
export DEXSCREENER_API_KEY="votre-cle-ici"
python test_api_connection.py
```

### Problème: "Workflow ne démarre pas"
- Vérifier que le workflow a `workflow_dispatch` activé (déjà fait ✓)
- Vérifier les permissions du repo

### Problème: "403 encore présent"
1. Vérifier le nom exact du secret dans GitHub
2. Re-créer le secret si nécessaire
3. Vérifier que la clé API est active sur dexscreener.com

## 📝 Notes Importantes

- Les anciens CSV vides (septembre-octobre) ne seront pas re-générés automatiquement
- La collecte recommence à partir de maintenant
- Les données historiques devront être collectées manuellement si nécessaire

## 🎯 Prochaines Étapes

1. ✅ Déclencher un test manuel du workflow
2. ⏳ Vérifier les logs de succès
3. ⏳ Confirmer la création du CSV avec données
4. ⏳ Merger la branche vers main une fois confirmé
5. ⏳ Surveillance: vérifier la collecte automatique quotidienne

---

**Besoin d'aide?** Vérifiez les logs dans GitHub Actions ou le fichier `data/run_summary.json` après chaque run.
