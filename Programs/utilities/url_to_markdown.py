# utilities/url_to_markdown.py

import requests
from bs4 import BeautifulSoup
from readability import Document
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QFileDialog
)
from PySide6.QtCore import Qt


class UrlToMarkdownWidget(QWidget):
    def __init__(self):
        super().__init__()  # Initialize the QWidget
        self.selected_folder = None  # Store chosen output path
        self.init_ui()  # Set up the layout

    def init_ui(self):
        # Outer layout to stack vertically
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- URL Input Section ---
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL here")
        self.url_input.setFixedHeight(36)
        layout.addWidget(self.url_input)

        # --- Folder Selection Row ---
        folder_row = QHBoxLayout()

        # Button to open folder selection dialog
        self.choose_folder_button = QPushButton("Choose Vault Folder")
        self.choose_folder_button.clicked.connect(self.choose_folder)
        folder_row.addWidget(self.choose_folder_button)

        # Label to show which folder is selected
        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("color: lightgray;")
        folder_row.addWidget(self.folder_label)

        layout.addLayout(folder_row)

        # --- Submit Button ---
        self.generate_button = QPushButton("Generate Markdown")
        self.generate_button.setFixedHeight(40)
        self.generate_button.clicked.connect(self.generate_markdown_clicked)
        layout.addWidget(self.generate_button)

        layout.addStretch()

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Obsidian Vault Folder")
        if folder:
            self.selected_folder = folder
            self.folder_label.setText(folder)

    def generate_markdown_clicked(self):
        url = self.url_input.text()
        folder = self.selected_folder

        if not url or not folder:
            print("Missing URL or output folder.")
            return

        try:
            # Step 1: Fetch HTML from the webpage
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/115.0.0.0 Safari/537.36"
                )
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            raw_html = response.text

            # Step 2: Extract article content using readability
            doc = Document(raw_html)
            article_html = doc.summary(html_partial=True)
            article_title = doc.title()

            # Step 3: Clean article HTML
            soup = BeautifulSoup(article_html, "html.parser")
            cleaned_html = soup.prettify()

            # Step 4: Send cleaned HTML to the LLM for markdown conversion
            filtered_markdown = self.run_llm_filter(cleaned_html)

            # Step 5: Construct file name from title
            safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in article_title.strip())
            filename = f"{safe_title}.md"
            output_path = os.path.join(folder, filename)

            # Step 6: Write output to markdown file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(filtered_markdown)

            print(f"✅ Markdown saved to: {output_path}")

        except Exception as e:
            print(f"❌ Error: {e}")

    def run_llm_filter(self, raw_html: str) -> str:
        """
        Sends cleaned article HTML to the local Ollama instance for markdown conversion.
        """

        model = "phi"
        
        system_prompt = (
            "You are a Markdown formatter. The user will give you HTML content extracted from a blog post. "
            "This HTML has already been cleaned to include only the main article (no sidebars, ads, or navigation). "
            "Your job is to convert it into valid, readable Markdown. "
            "Preserve all content, including headers, paragraphs, emphasis, and inline links. "
            "Do not summarize, rephrase, or exclude anything. "
            "Return only the Markdown output — no explanations or comments."
        )

        payload = {
            "model": model,
            "prompt": raw_html,
            "system": system_prompt,
            "stream": False
        }

        try:
            response = requests.post("http://localhost:11434/api/generate", json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()

        except requests.exceptions.RequestException as e:
            print(f"❌ LLM request failed: {e}")
            return "# LLM processing failed\n\nAn error occurred while calling the local model."
