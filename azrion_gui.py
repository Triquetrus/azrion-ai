import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton
from PyQt6.QtCore import Qt

# IMPORTANT:
# Change 'azrion_main' to the actual filename of your current script (without .py).
# For example, if your big script is in "azrion.py", use:
#   from azrion import azrion_chat, get_ai_greeting
from azrion import azrion_chat, get_ai_greeting  # adjust module name if needed


class AzrionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Azrion Assistant")
        self.resize(800, 600)

        self.layout = QVBoxLayout(self)

        self.chat_view = QTextEdit(self)
        self.chat_view.setReadOnly(True)
        self.input_line = QLineEdit(self)
        self.send_button = QPushButton("Send", self)

        self.layout.addWidget(self.chat_view)
        self.layout.addWidget(self.input_line)
        self.layout.addWidget(self.send_button)

        self.send_button.clicked.connect(self.send_message)
        self.input_line.returnPressed.connect(self.send_message)

        # Initial greeting from your existing function
        greeting = get_ai_greeting()
        self.append_message("Azrion", greeting)

    def append_message(self, sender, text):
        self.chat_view.append(f"{sender}: {text}")

    def send_message(self):
        user_text = self.input_line.text().strip()
        if not user_text:
            return
        self.append_message("You", user_text)
        self.input_line.clear()

        # Use your existing chat logic (includes system_action, memory, etc.)
        reply = azrion_chat(user_text)
        self.append_message("Azrion", reply)


def main():
    app = QApplication(sys.argv)
    win = AzrionWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
