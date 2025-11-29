import tkinter as tk
from redactor import redact_text
from accuracy import levenshtein_similarity
import spacy
nlp = spacy.load("en_core_web_sm")
print("Model loaded successfully!")

def run_redaction():
    input_text = input_box.get("1.0", "end")
    output = redact_text(input_text)
    output_box.delete("1.0", "end")
    output_box.insert("1.0", output)

def calculate_accuracy():
    expected = expected_box.get("1.0", "end").strip()
    predicted = output_box.get("1.0", "end").strip()

    score = levenshtein_similarity(expected, predicted)
    accuracy_label.config(text=f"Accuracy: {round(score * 100, 2)}%")

window = tk.Tk()
window.title("Hybrid Redaction & Accuracy System")

tk.Label(window, text="Input Text").pack()
input_box = tk.Text(window, height=6, width=70)
input_box.pack()

tk.Button(window, text="Redact", command=run_redaction).pack()

tk.Label(window, text="Redacted Output").pack()
output_box = tk.Text(window, height=6, width=70)
output_box.pack()

tk.Label(window, text="Expected Redacted Text").pack()
expected_box = tk.Text(window, height=6, width=70)
expected_box.pack()

tk.Button(window, text="Calculate Accuracy", command=calculate_accuracy).pack()
accuracy_label = tk.Label(window, text="Accuracy: ")
accuracy_label.pack()

window.mainloop()
