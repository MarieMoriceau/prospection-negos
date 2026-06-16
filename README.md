# Prospection terrain — appli négos

PWA mobile : le négociateur **dicte une société** repérée sur un immeuble, l'IA range la dictée dans les bons champs, il corrige si besoin, et la fiche part dans la base **Notion « Prospection terrain »**.

Une dictée = une société. Le bouton « Société suivante » garde l'adresse de l'immeuble pour enchaîner.

---

## 1. Mettre le code sur GitHub

Crée un repo `prospection-terrain` sous ton compte `MarieMoriceau`, et dépose tous ces fichiers (glisser-déposer dans l'interface GitHub web fonctionne très bien) :

```
app.py
requirements.txt
Dockerfile
.gitignore
static/index.html
static/manifest.json
static/sw.js
static/icon-192.png
static/icon-512.png
```

## 2. Préparer l'intégration Notion (l'étape qu'on oublie toujours)

1. Va sur **notion.so/my-integrations** → **New integration** → nomme-la `Prospection terrain` → copie le **Internal Integration Secret** (commence par `ntn_…` ou `secret_…`). C'est ton `NOTION_TOKEN`.
2. **CRUCIAL** : ouvre la base **Prospection terrain** dans Notion → menu `•••` en haut à droite → **Connections** → **Connect to** → choisis ton intégration.
   👉 Sans cette étape, le token existe mais n'a accès à rien : l'appli recevra une erreur `object_not_found`.

## 3. Déployer sur Render

1. **New → Web Service** → connecte ton repo GitHub.
2. Render détecte le `Dockerfile` tout seul. Région : Frankfurt.
3. Dans **Environment**, ajoute ces variables :

| Variable | Valeur |
|---|---|
| `ANTHROPIC_API_KEY` | ta clé API Anthropic (`sk-ant-…`) |
| `NOTION_TOKEN` | le secret de l'intégration (étape 2) |
| `NOTION_DATABASE_ID` | `c70e0416-a7d6-4dd9-9001-1f222bf5a4e7` *(déjà la valeur par défaut, tu peux ne pas la mettre)* |

   Optionnel : `ANTHROPIC_MODEL` (défaut `claude-sonnet-4-6` ; mets `claude-haiku-4-5-20251001` pour réduire le coût par fiche, l'extraction reste simple).

4. **Create Web Service**. Au bout de 2-3 min, tu as une URL `https://prospection-terrain.onrender.com`.

## 4. Installer sur le téléphone des négos

Ouvre l'URL dans **Safari (iPhone)** ou **Chrome (Android)** → menu Partager → **Sur l'écran d'accueil**. L'icône aubergine apparaît, l'appli s'ouvre en plein écran. Au premier usage, le téléphone demande l'autorisation du **micro** : accepter.

---

## Bon à savoir

- **Réveil à froid (plan Free)** : si personne n'a utilisé l'appli depuis ~15 min, le premier chargement prend 30-50 s (Render endort le service). Acceptable pour tester. Si les négos adoptent l'outil, un plan **Starter** (toujours allumé) supprime l'attente — à arbitrer selon l'usage réel.
- **Hors-ligne** : l'écran se charge hors connexion, mais l'envoi d'une fiche a besoin du réseau (Notion + IA). En zone blanche, le négo attend une barre de réseau avant d'enregistrer.
- **Correction** : tous les champs sont éditables avant envoi (les noms propres mal entendus se corrigent au clavier). Après envoi, la fiche se modifie directement dans l'appli Notion.

## En cas de souci

| Symptôme | Cause probable |
|---|---|
| `object_not_found` à l'envoi | intégration pas connectée à la base (étape 2.2) |
| `ANTHROPIC_API_KEY manquante` | variable d'env oubliée sur Render |
| La structuration ne renvoie rien | clé Anthropic invalide ou quota épuisé |
| Erreur de propriété Notion | un nom de colonne a été renommé dans la base (l'appli attend : Société, Adresse, Étage, Personne, En recherche, Remarques, Négo, Date de visite) |

Si Notion refuse le parent `database_id`, c'est le piège habituel base ≠ source de données : l'ID de **source de données** est `0ef0e459-f23c-4899-8d13-a24ce18323cd`.
