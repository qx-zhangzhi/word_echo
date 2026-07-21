# -*- coding: utf-8 -*-

from vocab.services.word_builder import build_word_defaults


def main():
    words = [
        "apple",
        "accelerate",
        "sustainable",
    ]

    for w in words:
        print("=" * 60)
        print(f"Testing word: {w}")

        result = build_word_defaults(w)

        for k, v in result.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
