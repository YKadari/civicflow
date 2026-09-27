from app.ai.ollama import classify_intent


def main():
    requests = [
        "My September housing payment has not arrived.",

        (
            "I was supposed to receive $850 at the "
            "beginning of the month, but nothing has "
            "appeared in my account."
        ),

        "I uploaded my income verification yesterday.",

        "I moved and need to update my mailing address.",

        "Can someone tell me what is happening with my case?",
    ]

    for description in requests:
        result = classify_intent(description)

        print()
        print("Request:")
        print(description)

        print("Classification:")
        print(result.request_type)

        print("Confidence:")
        print(result.confidence)


if __name__ == "__main__":
    main()