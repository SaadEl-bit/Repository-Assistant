# Repository Assistant

Un assistant conversationnel **RAG** (Retrieval-Augmented Generation) capable d'analyser un repository logiciel et de répondre en langage naturel à des questions sur son code, sa documentation, son architecture et ses zones critiques.

> **Cas d'usage :** Projet **Rafiki** — plateforme d'accompagnement scolaire pour la 2ème année baccalauréat (Maroc).  : https://github.com/SaadEl-bit/Rafiki
> **Stack :** Python, LangChain, ChromaDB, Streamlit, sentence-transformers, cross-encoders, LLM multi-provider (NVIDIA / Groq / DeepSeek).

---

## Fonctionnalités

| Fonctionnalité | Détail |
|---|---|
| **Ingestion multi-format** | Parse Python (AST), Markdown (sections), JSON/YAML/TOML, JS/TS/CSS |
| **Arbre d'architecture** | Extraction automatique de la structure du repo → indexé dans ChromaDB |
| **Recherche sémantique** | Embeddings multilingues (`paraphrase-multilingual-MiniLM-L12-v2` → 384d) |
| **Double filtrage anti-hallucination** | Cosine distance (`threshold=0.80`) + Cross-encoder re-ranking (`ms-marco-MiniLM-L-6-v2`) |
| **Mémoire conversationnelle** | Questions de suivi grâce à `ConversationBufferMemory` |
| **Zones critiques** | Détection de fichiers sensibles, complexité cyclomatique (radon), modules non testés |
| **Multi-LLM** | NVIDIA (principal) → Groq (fallback 1) → DeepSeek (fallback 2) avec cascade automatique |
| **Interface Streamlit** | Chatbot web avec historique, citations de sources, sidebar de stats |

---

## Architecture

### Pipeline de données

```
Repository/ (ex: Rafiki/)
    │
    ▼
┌──────────────────────────┐
│  config.py               │
│  discover_files()        │  → Filtre : exclusions + extensions autorisées
│  should_index()          │  → ~95 fichiers indexés / 77k exclus
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  ingestion.py            │
│  parse_file()            │  → AST (Python), sections (MD), fichier (JSON/JS)
│  extract_repo_tree()     │  → Arbre d'architecture (1 chunk type='architecture')
│  build_chunks()          │  → 812 chunks avec métadonnées
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  indexer.py              │
│  load_model()            │  → paraphrase-multilingual-MiniLM-L12-v2 (384d)
│  index_chunks()          │  → ChromaDB (collection: rafiki_chunks, 812 docs)
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────────┐
│  rag_chain.py                │
│  RelevanceRetriever(k=50)    │  → Cosine filter (distance < 0.80)
│  CrossEncoderScorer          │  → Re-ranking (score > 0)
│  PromptTemplate + Memory     │  → Contexte + historique
│  ConversationalRetrievalChain│  → NVIDIA / Groq / DeepSeek
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────┐
│  app.py (Streamlit)      │
│  Chat + Sources + Sidebar│
└──────────────────────────┘

┌──────────────────────────────┐
│  critical_analysis.py        │
│  scan_sensitive()            │  → 281 potentielles vulnérabilités
│  scan_complexity()           │  → 9 fonctions complexes (>10)
│  scan_untested()             │  → 27 modules sans tests
│  → Indexé dans ChromaDB      │
└──────────────────────────────┘
```

### Stack technique

| Couche | Technologie | Rôle |
|---|---|---|
| Parsing | Python `ast`, `pathlib`, regex | Lire et structurer le repository |
| Embeddings | `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`, 384d) | Vectorisation locale multilingue (50+ langues) |
| Cross-encoder | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Re-ranking de pertinence post-retrieval |
| Vector DB | ChromaDB (persistent, cosine) | Stockage et recherche sémantique |
| Orchestration RAG | LangChain (`langchain_classic`) | Chaînage retrieval + LLM + mémoire |
| LLM principal | NVIDIA API (`nvidia/llama-3.3-nemotron-super-49b-v1`) | Génération de réponses |
| LLM fallback 1 | Groq API (`llama-3.3-70b-versatile`) | Backup si NVIDIA indisponible |
| LLM fallback 2 | DeepSeek API (`deepseek-chat`) | Dernier recours |
| UI | Streamlit | Chatbot web interactif |
| Mémoire | `ConversationBufferMemory` | Historique conversationnel |
| Analyse code | `radon` | Complexité cyclomatique |

---

## Prérequis

- **Python 3.10+**
- **Clés API** : NVIDIA (obligatoire), Groq (recommandé), DeepSeek (optionnel)
- **8 Go RAM minimum** (pour le chargement des modèles sentence-transformers)

---

## Installation

```bash
# 1. Cloner le projet
git clone <votre-repo>
cd Repository-Assistant

# 2. Créer l'environnement virtuel
python -m venv venv

# 3. Activer l'environnement
# Windows :
venv\Scripts\activate
# Linux/Mac :
source venv/bin/activate

# 4. Installer les dépendances
pip install -r requirements.txt
```

## Configuration

Créez un fichier `.env` à la racine :

```env
# Obligatoire
NVIDIA_API_KEY=nvapi-votre-cle-nvidia

# Recommandé (fallback)
GROQ_API_KEY=gsk-votre-cle-groq

# Optionnel (dernier recours)
DEEPSEEK_API_KEY=sk-votre-cle-deepseek
```

Un template `.env.example` est fourni comme référence versionnée.

---

## Utilisation

### Lancer le chatbot

```bash
streamlit run app.py
```

Ouvrez `http://localhost:8501` dans votre navigateur.

### Exemples de questions

| Catégorie | Question |
|---|---|
| Architecture | "Quelle est l'architecture du projet Rafiki ?" |
| Code | "Où se trouve le module d'authentification ?" |
| Documentation | "Qu'est-ce que Rafiki ?" |
| Zones critiques | "Quels sont les fichiers sensibles ?" |
| Test anti-hallucination | "Quelle est la couleur du ciel ?" (doit répondre "Non trouvé") |

### Tests de validation

```bash
# Phase 1 — Ingestion & chunking
python test_ingestion.py

# Phase 2 — Embeddings & ChromaDB
python test_embeddings.py

# Phase 3 — Chaîne RAG complète
python test_rag.py

# Phase 4 — Zones critiques
python test_critical.py
```

### Évaluation

```bash
python evaluate.py
```

Génère un rapport dans `evaluation/evaluation_report.md`.

---

## Structure du projet

```
Repository-Assistant/
├── app.py                  # Interface Streamlit (chatbot)
├── config.py               # Configuration découverte & exclusions
├── ingestion.py            # Parsing & chunking + extract_repo_tree()
├── indexer.py              # Embeddings & indexation ChromaDB
├── llm_config.py           # Configuration LLM (NVIDIA / Groq / DeepSeek)
├── rag_chain.py            # Chaîne RAG (retriever + cross-encoder + mémoire + prompt)
├── cross_encoder.py        # Cross-encoder re-ranking (ms-marco-MiniLM-L-6-v2)
├── critical_analysis.py    # Analyse zones critiques
├── diagnostic_retrieval.py # Script de diagnostic retrieval
│
├── test_ingestion.py       # Validation Phase 1
├── test_embeddings.py      # Validation Phase 2
├── test_rag.py             # Validation Phase 3
├── test_critical.py        # Validation Phase 4
├── evaluate.py             # Script d'évaluation automatique
│
├── evaluation/
│   ├── questions.json      # 20 questions catégorisées
│   └── evaluation_report.md # Rapport d'évaluation (généré)
│
├── chroma_db/              # Base vectorielle persistante (généré)
├── .env                    # Clés API (non versionné)
├── .env.example            # Template .env (versionné)
├── .gitignore              # Règles d'exclusion Git
├── requirements.txt        # Dépendances Python
└── README.md               # Ce fichier
```

---

## Comment ça fonctionne

### 1. Ingestion (`config.py` + `ingestion.py`)

Le repository est parcouru récursivement. Chaque fichier est parsé selon son extension :

- **`.py`** → Analyse AST : chaque fonction, classe et bloc d'imports devient un chunk avec métadonnées (nom, lignes, docstring)
- **`.md`** → Découpage par sections `##` : chaque section devient un chunk
- **`.json` / `.yaml` / `.toml`** → Fichier entier = 1 chunk
- **`.js` / `.ts` / `.jsx` / `.tsx` / `.css`** → Fichier entier = 1 chunk
- **Arbre d'architecture** → Un chunk supplémentaire `type='architecture'` est généré automatiquement

### 2. Indexation (`indexer.py`)

Les chunks sont vectorisés avec `paraphrase-multilingual-MiniLM-L12-v2` (modèle multilingue, 384 dimensions) et stockés dans ChromaDB avec espace métrique `cosine`.

### 3. Retrieval & RAG (`rag_chain.py`)

```text
Question utilisateur
    │
    ▼
ChromaDB.similarity_search_with_score(k=50)
    │
    ▼
Filtre cosine (distance < 0.80)
    │
    ▼
Cross-encoder re-ranking (score > 0 = pertinent)
    │
    ▼
PromptTemplate (contexte + question + règles)
    │
    ▼
LLM : NVIDIA → (fallback) Groq → (fallback) DeepSeek
    │
    ▼
Réponse sourcée + historique mémoire
```

### 4. Anti-hallucination (3 lignes de défense)

1. **Filtre cosine** : les documents avec une distance ≥ 0.80 sont exclus avant d'atteindre le LLM
2. **Cross-encoder re-ranking** : chaque document est scoré par rapport à la question ; seuls les documents avec un score > 0 sont conservés
3. **Prompt système** : instruction stricte de ne répondre qu'à partir du contexte fourni

### 5. Zones critiques (`critical_analysis.py`)

3 analyses automatiques :
- **Fichiers sensibles** : mots-clés (`password`, `secret`, `token`), patterns de tokens (32+ caractères), URLs
- **Complexité cyclomatique** : utilise `radon` pour identifier les fonctions avec complexité > 10
- **Modules non testés** : compare `src/` avec `tests/`

---

## Changelog

### Prototype 2 (2026-06-29)
- ✅ `extract_repo_tree()` — arbre d'architecture indexé automatiquement
- ✅ `cross_encoder.py` — module de re-ranking avec `ms-marco-MiniLM-L-6-v2`
- ✅ Double filtrage : cosine (0.80) + cross-encoder (score > 0)
- ✅ `test_critical.py` — validation Phase 4
- ✅ Évaluation automatisée (20 questions, rapport `.md`)
- ✅ Documentation README complète

### Prototype 1 (2026-06-29)
- ✅ Passage NVIDIA LLM (`nvidia/llama-3.3-nemotron-super-49b-v1`)
- ✅ Modèle embedding multilingue (`paraphrase-multilingual-MiniLM-L12-v2`)
- ✅ `RelevanceRetriever` avec seuil 0.65
- ✅ k=3 + troncature 2000 caractères
- ✅ Correction cascade fallback NVIDIA → Groq → DeepSeek

---

## Roadmap

- [ ] **Rapport `.md` auto-généré** : résumé structuré du repository
- [ ] **Hybrid search** : BM25 + embeddings (améliore le recall)
- [ ] **Meilleur embedding** : tester `intfloat/multilingual-e5-small` ou `BAAI/bge-m3`
- [ ] **Streamlit multi-repo** : sélection du repository à analyser via l'UI
- [ ] **Mode conversationnel avancé** : résumé de conversation, questions de clarification
- [ ] **Déploiement Docker** : conteneurisation pour déploiement cloud

---

## Licence

Ce projet est développé dans le cadre d'un exercice de sélection.  
**Usage de l'IA** : Ce projet a été conçu et développé avec l'assistance d'une IA pour le brainstorming, la structuration du code et la revue technique. Les choix architecturaux, l'analyse critique et les décisions techniques relèvent de l'auteur.
