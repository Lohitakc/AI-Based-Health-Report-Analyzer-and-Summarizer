from app.rag.vectorstore import get_vector_store


def main() -> None:
    vector_store = get_vector_store()
    chunks = vector_store.ingest(force_rebuild=True)
    print(f"Ingested {chunks} chunks into ChromaDB.")


if __name__ == "__main__":
    main()

