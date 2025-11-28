# redactor.py
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


class RedactionEngine:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

        # ------------------------------
        # Add custom phone number pattern
        # ------------------------------
        phone_regex = r"(\+?\d{1,4}[-.\s]?)??(\(?\d{1,4}\)?[-.\s]?)+\d{1,10}"

        phone_pattern = Pattern(
            name="custom_phone_pattern",
            regex=phone_regex,
            score=0.8
        )

        phone_recognizer = PatternRecognizer(
            supported_entity="PHONE_NUMBER",
            patterns=[phone_pattern]
        )

        # Add recognizer to Presidio registry
        self.analyzer.registry.add_recognizer(phone_recognizer)

    def process(self, text: str, mode: str = "redact"):
        results = self.analyzer.analyze(text=text, language="en")

        entities = [
            {
                "type": r.entity_type,
                "text": text[r.start:r.end],
                "start": r.start,
                "end": r.end
            }
            for r in results
        ]

        if mode == "redact":
            anonymized = self.anonymizer.anonymize(
                text=text,
                analyzer_results=results,
                operators={"DEFAULT": OperatorConfig("replace", {"new_value": ""})}
            )
            redacted_text = anonymized.text

        else:  # highlight mode
            operators = {
                r.entity_type: OperatorConfig("replace", {"new_value": f"[{r.entity_type}]"})
                for r in results
            }

            operators["DEFAULT"] = OperatorConfig("replace", {"new_value": "[REDACTED]"})
            anonymized = self.anonymizer.anonymize(
                text=text,
                analyzer_results=results,
                operators=operators
            )
            redacted_text = anonymized.text

        return redacted_text.strip(), sorted(entities, key=lambda x: x["start"])
