from PyPDF2 import PdfReader
import os

# Define paths relative to your project root
input_path = os.path.join("input-datasets", "books", "DnD_BasicRules_2018.pdf")
output_path = os.path.join("input-datasets", "books", "DnD_BasicRules_2018.txt")

# Read and extract text
reader = PdfReader(input_path)
text = ""
for page in reader.pages:
    page_text = page.extract_text()
    if page_text:
        text += page_text + "\n"

# Save extracted text
with open(output_path, "w", encoding="utf-8") as f:
    f.write(text)

print(f"✅ Extraction complete! Text saved to: {output_path}")
