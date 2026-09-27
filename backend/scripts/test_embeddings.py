from app.ai.embeddings import embed_text


def main():
    text = (
        "A scheduled housing payment "
        "has not been received."
    )

    embedding = embed_text(text)

    print("Embedding dimensions:")
    print(len(embedding))

    print()
    print("First 10 values:")
    print(embedding[:10])


if __name__ == "__main__":
    main()