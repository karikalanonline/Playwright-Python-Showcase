Playwright-Python-Showcase

A sample automation framework built with **Playwright (Python)** following Page Object Model (POM) design.

Project Structure:
project/
├─ pages/ # Page Object classes (LoginPage, DashboardPage, etc.)
├─ data (test data, input)
├─ tests/ # Test files (pytest based)
├─ utils/ # Utilities (logger, retry, config helpers)
├─ conftest.py # Pytest fixtures (browser/page setup, login, screenshots)
├─ pytest.ini # Pytest configuration
└─ requirements.txt # Python dependencies


Clone the repository:
   ```bash
   git clone https://github.com/karikalansonline/Playwright-Python-Showcase.git
   cd Playwright-Python-Showcase

Install dependencies:
   pip install -r requirements.txt
   playwright install