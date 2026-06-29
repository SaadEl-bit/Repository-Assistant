import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from src.rag_chain import build_qa_chain

REPO_PATH = Path(r"H:\Study\Projects\Assistant Repsitory\Rafiki")


@st.cache_resource
def get_qa_chain():
    return build_qa_chain(REPO_PATH)


def init_session():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "qa_chain" not in st.session_state:
        with st.spinner("Chargement du moteur d'analyse (1-2 min)..."):
            st.session_state.qa_chain = get_qa_chain()
        st.sidebar.success("Moteur pret")


def main():
    st.set_page_config(
        page_title="Repository Assistant",
        page_icon="",
        layout="wide",
    )

    init_session()

    col_stats = st.sidebar.container()
    st.sidebar.markdown("---")
    st.sidebar.markdown("### A propos")
    st.sidebar.markdown(
        "Assistant d'analyse de repository logiciel. "
        "Posez des questions sur l'architecture, le code, "
        "la documentation et les fichiers critiques du projet."
    )
    st.sidebar.markdown("**Repository analyse** : Rafiki")
    st.sidebar.markdown(
        "**Limitations** : L'assistant repond uniquement "
        "sur la base du contenu indexe du repository."
    )

    st.title("Repository Assistant")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "sources" in msg and msg["sources"]:
                with st.expander("Sources"):
                    for s in msg["sources"][:5]:
                        meta = s.metadata
                        source = meta.get("source", "?")
                        lines = f"lignes {meta.get('lines_start', '?')}-{meta.get('lines_end', '?')}"
                        st.write(f"- `{source}` ({lines})")

    if prompt := st.chat_input("Posez votre question sur le repository..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyse en cours..."):
                try:
                    result = st.session_state.qa_chain.invoke({"question": prompt})
                    answer = result["answer"]
                    sources = result.get("source_documents", [])
                except Exception as e:
                    answer = f"**Erreur** : {str(e)}"
                    sources = []

            st.markdown(answer)

            if sources:
                with st.expander("Sources"):
                    for s in sources[:5]:
                        meta = s.metadata
                        source = meta.get("source", "?")
                        lines = f"lignes {meta.get('lines_start', '?')}-{meta.get('lines_end', '?')}"
                        st.write(f"- `{source}` ({lines})")

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources,
            })


if __name__ == "__main__":
    main()
