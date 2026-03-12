import re


class HeuristicDocumentSummarizer:
    _MIN_CHARACTERS = 80
    _MIN_WORDS = 12
    _MAX_SUMMARY_CHARACTERS = 280
    _MAX_SUMMARY_WORDS = 30
    _MAX_SENTENCES = 2

    def summarize(self, extracted_text: str) -> str | None:
        normalized_text = self._normalize(extracted_text)
        if not normalized_text:
            return None

        if len(normalized_text) < self._MIN_CHARACTERS:
            return None

        if len(normalized_text.split()) < self._MIN_WORDS:
            return None

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", normalized_text)
            if sentence.strip()
        ]

        if not sentences:
            return self._truncate_words(normalized_text)

        selected_sentences: list[str] = []
        for sentence in sentences:
            candidate = " ".join(selected_sentences + [sentence]).strip()
            if (
                len(candidate) <= self._MAX_SUMMARY_CHARACTERS
                and len(selected_sentences) < self._MAX_SENTENCES
            ):
                selected_sentences.append(sentence)
                continue
            break

        summary = " ".join(selected_sentences).strip()
        if not summary:
            return self._truncate_words(normalized_text)

        if summary == normalized_text:
            truncated_summary = self._truncate_words(normalized_text)
            return None if truncated_summary == normalized_text else truncated_summary

        return summary

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _truncate_words(self, text: str) -> str:
        words = text.split()
        if len(words) <= self._MAX_SUMMARY_WORDS:
            return text

        truncated = " ".join(words[: self._MAX_SUMMARY_WORDS]).rstrip(".,;:")
        return f"{truncated}..."
