from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton
import sys

app = QApplication(sys.argv)
window = QWidget()
layout = QVBoxLayout()

log_text = QTextEdit()
log_text.setReadOnly(True)
layout.addWidget(log_text)

button = QPushButton("Test")
button.clicked.connect(lambda: log_text.append("Bouton cliqué !"))
layout.addWidget(button)

window.setLayout(layout)
window.resize(700, 500)
window.show()
sys.exit(app.exec())
