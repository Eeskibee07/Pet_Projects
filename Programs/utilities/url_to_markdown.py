import requests
from bs4 import BeautifulSoup
from readability import Document
import os
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QFileDialog, QCheckBox, QComboBox
)
from PySide6.QtCore import Qt
import html2text  # for HTML to Markdown conversion
from datetime import datetime


class UrlToMarkdownWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_folder = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL here")
        self.url_input.setFixedHeight(36)
        layout.addWidget(self.url_input)

        folder_row = QHBoxLayout()
        self.choose_folder_button = QPushButton("Choose Vault Folder")
        self.choose_folder_button.clicked.connect(self.choose_folder)
        folder_row.addWidget(self.choose_folder_button)

        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("color: lightgray;")
        folder_row.addWidget(self.folder_label)

        layout.addLayout(folder_row)

        self.blog_selector = QComboBox()
        self.blog_selector.addItems(["Default", "Cafe Hayek"])
        layout.addWidget(self.blog_selector)

        self.use_llm_checkbox = QCheckBox("Use LLM for Classification and Markdown Conversion")
        layout.addWidget(self.use_llm_checkbox)

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

            doc = Document(raw_html)
            article_html = doc.summary(html_partial=True)
            article_title = doc.title()

            soup = BeautifulSoup(article_html, "html.parser")
            relevant_tags = soup.find_all(["p", "h2", "h3", "blockquote", "li"])

            kept_tags = []
            for tag in relevant_tags:
                text = tag.get_text(strip=True)
                if not text or len(text) < 30:
                    continue
                print(f"\nEvaluating paragraph:\n{text}\n")
                if self.use_llm_checkbox.isChecked():
                    if self.is_relevant_to_title(article_title, text):
                        print("→ Classified as YES\n")
                        kept_tags.append(tag)
                    else:
                        print("→ Classified as NO\n")
                else:
                    kept_tags.append(tag)

            if not kept_tags:
                print("❌ No content passed relevance filtering.")
                return

            combined_html = "\n".join(str(tag) for tag in kept_tags)

            if self.use_llm_checkbox.isChecked():
                converted_markdown = self.run_llm_markdown_conversion(combined_html)
            else:
                paragraphs = ["\t" + tag.get_text(strip=True) for tag in kept_tags]
                combined_text = "\n\n".join(paragraphs)
                converted_markdown = html2text.html2text(combined_text)

            safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in article_title.strip())

            # Append date for Cafe Hayek if applicable
            date_suffix = ""
            if self.blog_selector.currentText() == "Cafe Hayek":
                match = re.search(r'on (\w+ \d{1,2}, \d{4})', kept_tags[0].get_text(strip=True))
                if match:
                    try:
                        dt = datetime.strptime(match.group(1), "%B %d, %Y")
                        date_suffix = f"_{dt.strftime('%m-%d-%Y')}"
                    except ValueError:
                        pass

            filename = f"{safe_title}{date_suffix}.md"
            output_path = os.path.join(folder, filename)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(converted_markdown)

            print(f"✅ Markdown saved to: {output_path}")

        except Exception as e:
            print(f"❌ Error: {e}")

    def is_relevant_to_title(self, title: str, paragraph: str, model: str = "phi") -> bool:
        prompt = (
            f"The title of the article is: \"{title}\"\n\n"
            "The following paragraph appears in the article. "
            "Respond only with YES or NO. "
            "Is this paragraph part of the article's main content?\n\n"
            f"{paragraph}"
        )

        payload = {
            "model": model,
            "prompt": prompt,
            "system": "You are a content filter. Respond only with YES or NO.",
            "stream": False
        }

        try:
            response = requests.post("http://localhost:11434/api/generate", json=payload)
            response.raise_for_status()
            result = response.json()
            raw = result.get("response", "").strip().upper()
            print(f"LLM response: {raw}\n")
            return "YES" in raw
        except Exception as e:
            print(f"❌ Classification error: {e}")
            return False

    def run_llm_markdown_conversion(self, html: str, model: str = "phi") -> str:
        system_prompt = (
            "You are a strict HTML-to-Markdown converter. Do not summarize. Do not translate. Do not reword. "
            "You will receive cleaned HTML representing a blog article's main content, with headers, paragraphs, and links. "
            "Convert it *directly* into valid Markdown. Preserve all formatting. "
            "Only output the Markdown content. Do not explain, translate, or comment. "
            "Do not prefix your output with phrases like 'Here is the translated text' or 'The Markdown content is...'"
        )

        payload = {
            "model": model,
            "prompt": html,
            "system": system_prompt,
            "stream": False
        }

        try:
            response = requests.post("http://localhost:11434/api/generate", json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
        except Exception as e:
            print(f"❌ LLM request failed: {e}")
            return "# LLM processing failed\n\nAn error occurred while calling the local model."
