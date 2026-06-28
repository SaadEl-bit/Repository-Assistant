# 📋 Fiche de Planification — Prototype Assistant Conversationnel Repository

**Projet :** Assistant d'analyse de repository logiciel  
**Type :** Chatbot conversationnel avec mémoire + RAG  
**Scope :** Phase 1 (Chatbot fonctionnel) — Phase 2 (Rapport .md) reportée  
**Date de création :** 2026-06-28  
**Statut :** 🟡 En phase de planification

---

## 📌 Vue d'ensemble du prototype

L'objectif est de construire un assistant conversationnel capable d'analyser le repository **Rafiki** (projet d'accompagnement scolaire) et de répondre en langage naturel aux questions des utilisateurs sur :

- L'architecture générale du projet
- L'emplacement des fonctionnalités (authentification, gestion des étudiants, etc.)
- Les modules principaux et leurs relations
- Les fichiers sensibles ou critiques
- Les zones de complexité élevée

**Output :** Interface chatbot (Streamlit) avec mémoire de conversation et citations de sources.

---

## 🏗️ Architecture technique (Stack validée)

| Couche | Outil / Technologie | Rôle |
|--------|---------------------|------|
| **Parsing & Ingestion** | Python natif (`ast`, `os`, `pathlib`) | Lire et structurer le repository |
| **Chunking sémantique** | Python natif + `ast` | Découper par fonction / classe / section |
| **Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`) | Vectorisation locale et gratuite |
| **Vector DB** | `ChromaDB` (persistent) | Stockage et recherche sémantique |
| **Orchestration RAG** | `LangChain` | Chaînage retrieval + LLM + mémoire |
| **LLM** | DeepSeek API (`deepseek-chat` ou `deepseek-coder`) | Génération des réponses |
| **LLM Fallback** | Groq API (Llama 3) | Backup gratuit en cas d'indisponibilité DeepSeek |
| **Interface** | `Streamlit` | Chatbot web interactif |
| **Mémoire** | `LangChain ConversationBufferMemory` | Historique conversationnel |

---

## ⚠️ RÈGLES DE CONSTRUCTION (OBLIGATOIRES POUR LES AGENTS AI)

### Règle 1 : Ne jamais construire sans certitude
> **Si une étape, une dépendance, ou une architecture n'est pas clairement validée — STOP et demander confirmation avant de continuer.**

- Ne pas inventer de librairies non listées dans la stack.
- Ne pas modifier l'architecture globale sans validation.
- Ne pas supprimer ou écraser du code existant sans sauvegarde.

### Règle 2 : Suivre strictement les phases et steps
> **Les phases sont ordonnées. Une phase ne commence que si la précédente est validée et loguée.**

- Respecter l'ordre chronologique des phases.
- Ne pas passer à la phase N+1 si la phase N n'est pas fonctionnelle.
- Documenter chaque blocage ou écart dans la section **Log History**.

### Règle 3 : Vérification préalable obligatoire
> **Avant de commencer toute phase, l'agent doit :**

1. Lire la fiche de planification en entier.
2. Identifier les dépendances de la phase (quels fichiers/modules doivent exister).
3. Vérifier que l'environnement est prêt (clés API, modèles téléchargés, etc.).
4. Signaler TOUTE anomalie avant d'écrire la première ligne de code.

### Règle 4 : Isolation des fichiers sensibles
> **Le fichier `.env` et tout fichier contenant des secrets ne doivent JAMAIS être indexés.**

- Liste d'exclusion stricte à respecter (voir Phase 1, Step 3).
- En cas de doute sur un fichier : EXCLURE par défaut.

### Règle 5 : Anti-hallucination par design
> **Le prototype ne doit JAMAIS inventer d'informations sur le repository.**

- Seuil de distance ChromaDB à configurer (si > 0.5 → réponse "Non trouvé").
- Prompt système obligatoire avec instruction de restriction au contexte.
- Citation obligatoire des sources (fichier + lignes) dans chaque réponse.

### Règle 6 : Log History obligatoire
> **Après chaque phase terminée, mettre à jour la section Log History de cette fiche.**

- Date et heure de complétion.
- Résumé de ce qui a été fait.
- Problèmes rencontrés et comment ils ont été résolus.
- Prochaine phase estimée.

---

## 🗓️ PHASES DE CONSTRUCTION

---

### 🔷 PHASE 0 : Préparation de l'environnement
**Objectif :** Avoir un environnement de développement fonctionnel avec toutes les dépendances.

#### Step 0.1 — Création de l'environnement virtuel
- [ ] Créer un dossier `rafiki-assistant/`
- [ ] Créer un environnement virtuel Python (`python -m venv venv`)
- [ ] Activer l'environnement

#### Step 0.2 — Installation des dépendances
- [ ] Créer `requirements.txt` avec :
  ```
  streamlit
  chromadb
  sentence-transformers
  langchain
  langchain-community
  langchain-openai
  deepseek
  requests
  radon
  ```
- [ ] Installer : `pip install -r requirements.txt`
- [ ] Vérifier que `sentence-transformers` télécharge bien `all-MiniLM-L6-v2` au premier lancement

#### Step 0.3 — Configuration des clés API
- [ ] Créer `.env` (non versionné) avec :
  ```
  DEEPSEEK_API_KEY=sk-...
  GROQ_API_KEY=gsk-... (fallback)
  ```
- [ ] Créer `.env.example` (versionné, sans vraies valeurs)
- [ ] Créer `.gitignore` avec `.env`, `chroma_db/`, `venv/`, `__pycache__/`

#### Step 0.4 — Vérification structure Rafiki
- [ ] Confirmer le chemin du repository Rafiki à analyser
- [ ] Lister les types de fichiers présents (`.py`, `.md`, `.json`, `.yaml`, etc.)
- [ ] Identifier la présence ou non de frontend (JS/React) — adapter le parsing si besoin

**🚦 Validation Phase 0 :** Toutes les librairies importables sans erreur. Clés API testées avec un appel simple.

---

### 🔷 PHASE 1 : Ingestion et Parsing du Repository
**Objectif :** Extraire, structurer et préparer tous les fichiers pertinents du repository.

#### Step 1.1 — Définition des règles d'exclusion
- [ ] Créer `config.py` avec la liste `SENSITIVE_PATTERNS` :
  ```python
  SENSITIVE_PATTERNS = [
      '.env', '.env.local', '.env.production',
      'secrets.json', '*.key', '*.pem',
      'config.prod.py', 'settings.prod.py',
      '__pycache__', 'node_modules',
      '.git', '.github',
      'venv/', 'env/', '.venv/',
      '*.pyc', '*.log', '*.tmp',
      'chroma_db/',  # Base vectorielle locale
  ]
  ```
- [ ] Implémenter `should_index(file_path) -> bool`

#### Step 1.2 — Parcours récursif du repository
- [ ] Implémenter `discover_files(repo_path) -> List[str]`
- [ ] Filtrer avec `should_index()`
- [ ] Logger le nombre de fichiers trouvés vs exclus

#### Step 1.3 — Parsing Python (AST)
- [ ] Implémenter `parse_python_file(file_path) -> List[Chunk]`
- [ ] Extraire :
  - Fonctions (`ast.FunctionDef`) → chunk avec docstring
  - Classes (`ast.ClassDef`) → chunk avec méthodes
  - Imports (`ast.Import`, `ast.ImportFrom`) → chunk séparé
- [ ] Capturer métadonnées : `source`, `type`, `name`, `lines_start`, `lines_end`

#### Step 1.4 — Parsing Markdown (Documentation)
- [ ] Implémenter `parse_markdown_file(file_path) -> List[Chunk]`
- [ ] Découper par sections (`## Titre`)
- [ ] Capturer métadonnées : `source`, `type`, `section_title`

#### Step 1.5 — Parsing JSON / YAML / TOML (Configuration)
- [ ] Implémenter `parse_config_file(file_path) -> List[Chunk]`
- [ ] Découper par fichier entier (les configs sont généralement courtes)
- [ ] Capturer métadonnées : `source`, `type`, `format`

#### Step 1.6 — Assemblage des chunks
- [ ] Créer `Chunk` dataclass :
  ```python
  @dataclass
  class Chunk:
      id: str
      content: str
      metadata: dict
  ```
- [ ] Générer des IDs uniques : `{filename}_{type}_{name}_{line}`
- [ ] Valider qu'aucun chunk n'est vide ou trop court (< 50 caractères)
- [ ] Logger le nombre total de chunks générés

**🚦 Validation Phase 1 :** Script `test_ingestion.py` qui parcourt Rafiki et affiche : nombre de fichiers, nombre de chunks, exemple de 3 chunks avec métadonnées.

---

### 🔷 PHASE 2 : Chunking Sémantique et Embeddings
**Objectif :** Vectoriser tous les chunks et les stocker dans ChromaDB.

#### Step 2.1 — Chargement du modèle d'embedding
- [ ] Initialiser `SentenceTransformer('all-MiniLM-L6-v2')` une seule fois
- [ ] Vérifier la dimension des vecteurs (384 pour all-MiniLM)
- [ ] Logger le temps de chargement

#### Step 2.2 — Création de la collection ChromaDB
- [ ] Initialiser `chromadb.PersistentClient(path="./chroma_db")`
- [ ] Créer la collection `rafiki_chunks`
- [ ] Vérifier qu'aucune collection du même nom n'existe déjà (sinon la supprimer ou réutiliser)

#### Step 2.3 — Embedding et stockage par batch
- [ ] Implémenter `index_chunks(chunks: List[Chunk])`
- [ ] Traiter par batchs de 100 chunks (évite la surcharge mémoire)
- [ ] Pour chaque batch :
  - Encoder les contenus : `model.encode([c.content for c in batch])`
  - Ajouter à ChromaDB : `collection.add(ids=..., documents=..., metadatas=..., embeddings=...)`
- [ ] Logger la progression (batch X / total Y)

#### Step 2.4 — Vérification de l'index
- [ ] Compter les documents dans ChromaDB : `collection.count()`
- [ ] Vérifier qu'il correspond au nombre de chunks générés
- [ ] Faire une requête test : `collection.query(query_texts=["authentification"], n_results=1)`
- [ ] Vérifier que le résultat est pertinent

**🚦 Validation Phase 2 :** Script `test_embeddings.py` qui indexe Rafiki et retourne les 3 chunks les plus proches de la question "Comment fonctionne l'authentification ?".

---

### 🔷 PHASE 3 : Orchestration RAG avec LangChain
**Objectif :** Construire la chaîne qui relie ChromaDB au LLM via LangChain.

#### Step 3.1 — Configuration du LLM
- [ ] Créer `llm_config.py` avec deux providers :
  - DeepSeek (principal) : `ChatOpenAI` avec `base_url="https://api.deepseek.com/v1"`
  - Groq (fallback) : `ChatOpenAI` avec `base_url="https://api.groq.com/openai/v1"`
- [ ] Implémenter `get_llm()` qui tente DeepSeek d'abord, fallback sur Groq en cas d'erreur
- [ ] Paramètre `temperature=0` (déterministe)

#### Step 3.2 — Configuration du Retriever
- [ ] Wrapper ChromaDB dans `LangChain Chroma` :
  ```python
  from langchain_community.vectorstores import Chroma
  vectorstore = Chroma(
      client=chroma_client,
      collection_name="rafiki_chunks",
      embedding_function=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
  )
  ```
- [ ] Créer le retriever : `retriever = vectorstore.as_retriever(search_kwargs={"k": 5})`

#### Step 3.3 — Construction du Prompt RAG
- [ ] Définir le template système :
  ```
  Tu es un assistant expert en analyse de repository logiciel.
  Tu analyses le projet "Rafiki" (accompagnement scolaire 2ème année bac).

  RÈGLES STRICTES :
  1. Réponds UNIQUEMENT sur la base du CONTEXTE fourni ci-dessous.
  2. Si le contexte ne permet pas de répondre, dis EXPLICITEMENT :
     "Je ne dispose pas d'informations suffisantes dans le repository pour répondre."
  3. Cite TOUJOURS tes sources : nom du fichier et lignes concernées.
  4. Ne fais aucune supposition hors du contexte.
  5. Structure ta réponse de manière claire et technique.

  CONTEXTE :
  {context}

  QUESTION : {question}

  RÉPONSE DÉTAILLÉE ET SOURCÉE :
  ```
- [ ] Créer `PromptTemplate` LangChain avec variables `{context}` et `{question}`

#### Step 3.4 — Chaîne avec mémoire conversationnelle
- [ ] Initialiser `ConversationBufferMemory` :
  ```python
  memory = ConversationBufferMemory(
      memory_key="chat_history",
      return_messages=True,
      output_key="answer"
  )
  ```
- [ ] Construire `ConversationalRetrievalChain` :
  ```python
  qa_chain = ConversationalRetrievalChain.from_llm(
      llm=llm,
      retriever=retriever,
      memory=memory,
      return_source_documents=True,
      combine_docs_chain_kwargs={"prompt": PROMPT}
  )
  ```

#### Step 3.5 — Gestion du seuil de pertinence
- [ ] Wrapper le retriever avec une vérification de distance
- [ ] Si `distance > 0.5` pour le meilleur résultat → retourner "Non trouvé" sans appeler le LLM
- [ ] Implémenter `check_relevance(results) -> bool`

**🚦 Validation Phase 3 :** Script `test_rag.py` qui pose 3 questions :
1. "Où est l'authentification ?" → doit retourner un chunk pertinent + sources
2. "Quelle est la couleur du ciel ?" → doit retourner "Non trouvé dans le repository"
3. Deux questions liées avec mémoire → la 2ème doit comprendre le contexte de la 1ère

---

### 🔷 PHASE 4 : Détection des zones critiques
**Objectif :** Identifier les fichiers sensibles, complexes ou non testés.

#### Step 4.1 — Détection fichiers sensibles
- [ ] Scanner les fichiers indexés pour :
  - Mots-clés : `password`, `secret`, `token`, `api_key`, `private_key`
  - Patterns regex : `"[A-Za-z0-9]{32,}"` (tokens), `https?://[^\s]+` (URLs)
- [ ] Générer une liste `sensitive_files.json`

#### Step 4.2 — Analyse de complexité (Python)
- [ ] Utiliser `radon` pour calculer la complexité cyclomatique :
  ```python
  from radon.complexity import cc_visit
  ```
- [ ] Identifier les fonctions/classes avec complexité > 10 (haute)
- [ ] Générer une liste `complex_functions.json`

#### Step 4.3 — Détection fichiers non testés
- [ ] Comparer le contenu de `src/` avec `tests/`
- [ ] Identifier les modules sans fichier de test correspondant
- [ ] Générer une liste `untested_modules.json`

#### Step 4.4 — Intégration dans le RAG
- [ ] Ajouter une collection ChromaDB séparée `rafiki_critical` pour ces métadonnées
- [ ] Permettre au chatbot de répondre à : "Quels sont les fichiers sensibles ?" ou "Quelles sont les zones complexes ?"

**🚦 Validation Phase 4 :** Script `test_critical.py` qui affiche les 3 listes (sensibles, complexes, non testés) et vérifie qu'une question sur les zones critiques retourne une réponse sourcée.

---

### 🔷 PHASE 5 : Interface Streamlit (Chatbot)
**Objectif :** Créer l'interface utilisateur interactive.

#### Step 5.1 — Structure de l'app Streamlit
- [ ] Créer `app.py` avec la structure :
  ```
  Repository Assistant
  ├── Sidebar : Info projet + Stats (nb fichiers, nb chunks)
  ├── Zone chat : Historique des messages
  ├── Input : Barre de saisie utilisateur
  └── Sources : Expansion panel avec les fichiers cités
  ```

#### Step 5.2 — Gestion de l'état (session_state)
- [ ] Initialiser `st.session_state.messages` pour l'historique
- [ ] Initialiser `st.session_state.qa_chain` (une seule instance)
- [ ] Initialiser `st.session_state.memory` (persistance conversation)

#### Step 5.3 — Affichage des messages
- [ ] Boucle sur `session_state.messages` pour afficher l'historique
- [ ] Distinction visuelle User (droite) vs Assistant (gauche)
- [ ] Format Markdown pour les réponses

#### Step 5.4 — Traitement de la question
- [ ] Capturer l'input utilisateur
- [ ] Appeler `qa_chain.invoke({"question": input})`
- [ ] Extraire :
  - `result["answer"]` → texte de la réponse
  - `result["source_documents"]` → chunks sources
- [ ] Afficher la réponse
- [ ] Afficher un expander "📄 Sources" avec la liste des fichiers + lignes

#### Step 5.5 — Gestion des erreurs
- [ ] Try/except autour de l'appel au LLM
- [ ] Si DeepSeek fail → fallback Groq automatique
- [ ] Si Groq fail aussi → message : "Service temporairement indisponible. Réessayez plus tard."
- [ ] Logger les erreurs dans un fichier `logs/error.log`

#### Step 5.6 — Stats et monitoring
- [ ] Sidebar : Nombre total de chunks indexés
- [ ] Sidebar : Nombre de fichiers analysés
- [ ] Sidebar : Temps moyen de réponse (calculé sur les 5 dernières requêtes)

**🚦 Validation Phase 5 :** Lancer `streamlit run app.py`, poser 5 questions variées, vérifier :
- Réponses cohérentes et sourcées
- Mémoire fonctionnelle (question de suivi)
- Fallback en cas d'indisponibilité
- Sources affichées correctement

---

### 🔷 PHASE 6 : Évaluation et tests
**Objectif :** Mesurer la qualité et la fiabilité de l'assistant.

#### Step 6.1 — Jeu de questions de test
- [ ] Créer `evaluation/questions.json` avec 20 questions catégorisées :
  - Architecture (5 questions)
  - Fonctionnalités / localisation (5 questions)
  - Documentation (5 questions)
  - Zones critiques (3 questions)
  - Hallucination traps (2 questions : questions sans réponse dans le repo)

#### Step 6.2 — Métriques d'évaluation
- [ ] **Pertinence retrieval** : Le bon chunk est-il dans le top-3 ?
- [ ] **Exactitude réponse** : La réponse est-elle factuellement correcte ?
- [ ] **Citation sources** : Les sources sont-elles citées et correctes ?
- [ ] **Taux d'hallucination** : % de réponses inventées (doit être ~0%)
- [ ] **Latence** : Temps moyen question → réponse

#### Step 6.3 — Script d'évaluation automatique
- [ ] Créer `evaluate.py` qui :
  - Pose chaque question au chatbot
  - Enregistre la réponse
  - Compare avec une réponse attendue (manuelle)
  - Génère un rapport `evaluation_report.md`

#### Step 6.4 — Test de charge
- [ ] Simuler 10 questions simultanées (si applicable)
- [ ] Vérifier la stabilité de ChromaDB et du LLM

**🚦 Validation Phase 6 :** Rapport d'évaluation avec au moins 80% de pertinence retrieval et 0% d'hallucination détectée.

---

### 🔷 PHASE 7 : Documentation et livrable
**Objectif :** Préparer la réponse structurée à l'exercice de sélection.

#### Step 7.1 — Rédaction de la réponse structurée
Rédiger un document répondant aux 7 points de l'exercice :
1. Comment vous analysez le repository
2. Comment vous indexez les fichiers, le code et la documentation
3. Comment l'assistant retrouve les informations pertinentes
4. Comment il génère une réponse fiable et sourcée
5. Comment il limite les hallucinations
6. Comment il identifie les zones critiques du projet
7. Comment vous évaluez la qualité de l'assistant

#### Step 7.2 — Section "Usage de l'IA"
- [ ] Déclarer clairement :
  - Ce qui a été réalisé avec l'aide d'une IA (brainstorming, structuration, revue technique)
  - Ce qui relève de l'analyse personnelle (choix de l'architecture, justification des choix, évaluation critique)
  - Les limites de l'aide IA (ne remplace pas la compréhension profonde du code métier)

#### Step 7.3 — Schémas et diagrammes
- [ ] Architecture globale (diagramme flux de données)
- [ ] Schéma du pipeline RAG
- [ ] Schéma de la mémoire conversationnelle

#### Step 7.4 — Démonstration
- [ ] Enregistrer une courte démo (GIF ou vidéo) du chatbot en action
- [ ] Préparer 3 questions-types pour l'oral

**🚦 Validation Phase 7 :** Document complet, honnête sur l'usage de l'IA, démonstration fonctionnelle.

---

## 📜 LOG HISTORY

> **Cette section doit être mise à jour après chaque phase terminée.**

| Date | Phase | Statut | Résumé | Problèmes rencontrés | Résolution |
|------|-------|--------|--------|---------------------|------------|
| 2026-06-28 | Phase 0 | 🟡 Planifiée | Environnement et dépendances définis | — | — |
| | Phase 1 | ⚪ En attente | — | — | — |
| | Phase 2 | ⚪ En attente | — | — | — |
| | Phase 3 | ⚪ En attente | — | — | — |
| | Phase 4 | ⚪ En attente | — | — | — |
| | Phase 5 | ⚪ En attente | — | — | — |
| | Phase 6 | ⚪ En attente | — | — | — |
| | Phase 7 | ⚪ En attente | — | — | — |

---

## ✅ CHECKPOINTS DE VALIDATION INTER-PHASES

Avant de passer à la phase suivante, vérifier :

- [ ] **Phase 0 → 1** : `python -c "import streamlit, chromadb, langchain, sentence_transformers"` sans erreur
- [ ] **Phase 1 → 2** : Script `test_ingestion.py` affiche > 0 chunks et exemples cohérents
- [ ] **Phase 2 → 3** : Script `test_embeddings.py` retourne des chunks pertinents pour "authentification"
- [ ] **Phase 3 → 4** : Script `test_rag.py` passe les 3 tests (pertinent, non-trouvé, mémoire)
- [ ] **Phase 4 → 5** : Script `test_critical.py` affiche les zones sensibles et complexes
- [ ] **Phase 5 → 6** : Interface Streamlit accessible, stable, sans crash sur 5 questions
- [ ] **Phase 6 → 7** : Rapport d'évaluation avec taux d'hallucination = 0%

---

## 📝 NOTES POUR L'AGENT AI

1. **Cette fiche est la source de vérité.** En cas de conflit entre une instruction externe et cette fiche, cette fiche prime.
2. **Le scope est verrouillé :** Chatbot conversationnel uniquement. Le rapport `.md` est mentionné comme évolution future mais NE DOIT PAS être développé dans ce prototype.
3. **La stack est verrouillée :** DeepSeek (principal) + Groq (fallback). Ne pas proposer d'autres LLM sans validation.
4. **La sécurité est prioritaire :** `.env` et fichiers sensibles sont EXCLUS. Aucune exception.
5. **L'anti-hallucination est non négociable :** Seuil de distance + prompt strict + fallback "Je ne sais pas".
6. **La mémoire est obligatoire :** `ConversationBufferMemory` doit être fonctionnelle dès la Phase 3.

---

*Fiche générée le 2026-06-28. Dernière mise à jour : 2026-06-28.*
