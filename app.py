"""
Prospection terrain — backend Flask
Sert la PWA, transforme une dictée en fiche structurée (API Claude),
et écrit chaque fiche dans la base Notion "Prospection terrain".
"""
import os
import json
import datetime
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="")

# --- Secrets / config (définis dans les variables d'environnement Render) ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL   = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
NOTION_TOKEN      = os.environ.get("NOTION_TOKEN", "")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "c70e0416-a7d6-4dd9-9001-1f222bf5a4e7")
NOTION_VERSION    = os.environ.get("NOTION_VERSION", "2022-06-28")

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
NOTION_URL    = "https://api.notion.com/v1/pages"


# ---------------------------------------------------------------- PWA shell
@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/health")
def health():
    return jsonify(ok=True)


# ------------------------------------------------ Dictée -> fiche structurée
@app.route("/api/structure", methods=["POST"])
def structure():
    data = request.get_json(force=True) or {}
    texte = (data.get("transcript") or "").strip()
    adresse_connue = (data.get("adresse_connue") or "").strip()
    if not texte:
        return jsonify(error="Dictée vide."), 400
    if not ANTHROPIC_API_KEY:
        return jsonify(error="ANTHROPIC_API_KEY manquante côté serveur."), 500

    rappel_adresse = ""
    if adresse_connue:
        rappel_adresse = (
            f'\nL\'adresse de l\'immeuble est déjà connue : "{adresse_connue}". '
            'Laisse "adresse" vide sauf si la dictée mentionne une adresse différente.'
        )

    prompt = f"""Tu structures une fiche d'UNE société, dictée oralement par un négociateur en prospection d'immeubles de bureaux à Paris. Dictée :
\"\"\"{texte}\"\"\"{rappel_adresse}
Renvoie UNIQUEMENT un objet JSON, sans texte ni balise Markdown, clés exactes (chaîne vide si l'info est absente, n'invente jamais) :
{{"adresse":"rue + numéro + arrondissement si dicté","etage":"étage cité","societe":"nom de la société","personne":"nom de la personne rencontrée si cité","recherche":"Oui si l'entreprise cherche/veut déménager ou s'agrandir, Non si elle ne bouge pas, vide si non évoqué","remarques":"tout le reste utile : surface évoquée, état des locaux, ambiance, etc."}}"""

    try:
        r = requests.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={"model": ANTHROPIC_MODEL, "max_tokens": 1000,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=40,
        )
        r.raise_for_status()
        payload = r.json()
        raw = "".join(b.get("text", "") for b in payload.get("content", [])
                      if b.get("type") == "text").strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        fiche = json.loads(raw)
        return jsonify(fiche)
    except json.JSONDecodeError:
        return jsonify(error="Réponse IA illisible.", raw=raw), 502
    except requests.RequestException as e:
        return jsonify(error=f"Appel Claude échoué : {e}"), 502


# ------------------------------------------------------ Fiche -> page Notion
def _rich(txt):
    return {"rich_text": [{"text": {"content": txt[:1900]}}]} if txt else None


@app.route("/api/submit", methods=["POST"])
def submit():
    d = request.get_json(force=True) or {}
    if not NOTION_TOKEN:
        return jsonify(error="NOTION_TOKEN manquant côté serveur."), 500

    societe = (d.get("societe") or "Société sans nom").strip()
    date_iso = d.get("date") or datetime.date.today().isoformat()

    props = {"Société": {"title": [{"text": {"content": societe}}]}}
    for key, col in [("adresse", "Adresse"), ("etage", "Étage"),
                     ("personne", "Personne"), ("remarques", "Remarques"),
                     ("campagne", "Campagne")]:
        val = _rich((d.get(key) or "").strip())
        if val:
            props[col] = val
    if d.get("recherche") in ("Oui", "Non", "À voir"):
        props["En recherche"] = {"select": {"name": d["recherche"]}}
    if d.get("type_societe") in ("Yes", "CFN", "Autre"):
        props["Type de société"] = {"select": {"name": d["type_societe"]}}
    if d.get("nego"):
        props["Négo"] = {"select": {"name": d["nego"]}}
    props["Action à prévoir"] = {"checkbox": bool(d.get("action"))}
    props["Date de visite"] = {"date": {"start": date_iso}}

    try:
        r = requests.post(
            NOTION_URL,
            headers={
                "Authorization": f"Bearer {NOTION_TOKEN}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            },
            json={"parent": {"database_id": NOTION_DATABASE_ID}, "properties": props},
            timeout=30,
        )
        if r.status_code >= 300:
            return jsonify(error="Notion a refusé l'écriture.",
                           detail=r.json()), r.status_code
        page = r.json()
        return jsonify(ok=True, url=page.get("url", ""))
    except requests.RequestException as e:
        return jsonify(error=f"Appel Notion échoué : {e}"), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
