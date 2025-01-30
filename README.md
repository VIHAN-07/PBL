Here’s a structured and well-formatted `README.md` file for your project based on the provided files:

```markdown
# 🌌 Cold Email Synthesizer

## 🚀 Overview
Cold Email Synthesizer is a **Streamlit** web application that leverages **LangChain** and **Groq LLM** to generate highly targeted cold emails based on job descriptions. The application allows users to:
- Extract job postings from a provided webpage URL.
- Match job requirements with a portfolio of past projects.
- Generate personalized cold emails using AI.

## 🛠 Features
- 🌍 **Web Scraping**: Extract job postings from a given webpage.
- 🏗 **Portfolio Matching**: Identify relevant portfolio links for the job description.
- 📩 **AI-Powered Email Writing**: Generate professional cold emails.
- 🎨 **Custom UI Theme**: A futuristic alien-themed Streamlit UI.

## 📦 Installation
### Prerequisites
Ensure you have **Python 3.8+** installed.

### Steps to Install
1. **Clone the repository**
   ```sh
   git clone https://github.com/your-username/cold-email-synthesizer.git
   cd cold-email-synthesizer
   ```
2. **Create a virtual environment (optional but recommended)**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   venv\Scripts\activate  # On Windows
   ```
3. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```

## 🚀 Usage
1. **Set up your API keys**  
   Rename `config.json` and replace `GROQ_API_KEY` with your API key:
   ```json
   {
     "GROQ_API_KEY": "your_api_key_here"
   }
   ```

2. **Run the Streamlit app**
   ```sh
   streamlit run main.py
   ```

3. **Upload your portfolio (CSV format)**  
   The CSV should have two columns:  
   - `Techstack`: List of technologies used (separated by `|`).
   - `Links`: URL of the related project.

4. **Enter a job page URL**  
   - The app scrapes job postings.
   - It extracts skills and matches them with your portfolio.
   - Generates a customized cold email.

## 📂 Project Structure
```
cold-email-synthesizer/
│── main.py              # Streamlit app entry point
│── chains.py            # LangChain logic for job extraction & email generation
│── portfolio.py         # Portfolio handling & querying
│── utils.py             # Text processing utilities
│── config.json          # Configuration file for API keys
│── requirements.txt     # Dependencies
```

## 🔧 Technologies Used
- **Streamlit** (`streamlit`) - Web interface
- **LangChain** (`langchain_community`, `langchain_core`, `langchain_groq`) - AI-powered job & email processing
- **Chromadb** (`chromadb`) - Portfolio matching
- **Pandas** (`pandas`) - Data processing
- **BeautifulSoup4** (`beautifulsoup4`) - Web scraping
- **Dotenv** (`python-dotenv`) - Environment variable management

## 👥 Contribution
Feel free to fork this repository and submit pull requests. Contributions are welcome!

## 📜 License
This project is licensed under the MIT License.

---

💡 *Happy cold emailing! 🚀*
```

Let me know if you'd like any modifications! 🚀