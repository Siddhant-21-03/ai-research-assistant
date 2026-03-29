# AI Research Assistant 🔬

A full-stack Retrieval-Augmented Generation (RAG) application that allows users to semantically search, chat with, and analyze their personal documents (PDF, CSV, TXT, MD) using Advanced AI.

## 🌟 Features
- **Intelligent RAG Pipeline**: Built with LangChain and ChromaDB to chunk, embed, and accurately retrieve context from uploaded documents.
- **Conversational Memory**: The AI remembers your chat history, allowing for context-aware follow-up questions and deeper logical analysis.
- **Context Filtering**: Seamlessly switch between querying "All Documents" or filtering to extract facts from a specific file.
- **Modern UI**: A sleek, dark-themed Streamlit frontend featuring document management sidebars, vector database statistics, and inline source citation.
- **Robust Backend**: Powered by an asynchronous FastAPI architecture, keeping the heavy machine learning workloads completely decoupled from the frontend.

## 🛠️ Technology Stack
- **Backend API**: FastAPI, Python
- **Frontend App**: Streamlit
- **AI & ML**: LangChain, ChromaDB, Google Gemini (2.5 Flash & Embeddings)
- **Data Engineering**: PyPDFLoader, RecursiveCharacterTextSplitter

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A Google Gemini API Key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-research-assistant.git
   cd ai-research-assistant
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your Environment Variables:
   Create a `.env` file in the root directory and add your API key:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

### Running the Application

This is a two-part application. You will need to start both the Backend (FastAPI) and Frontend (Streamlit) servers.

**1. Start the Backend API:**
Open your terminal in the project directory and run:
```bash
python -m uvicorn backend.main:app --reload
```
*The backend will run on `http://127.0.0.1:8000`. You can view the API documentation at `/docs`.*

**2. Start the Frontend UI:**
Open a **new** terminal window and run:
```bash
streamlit run frontend/app.py
```
*The frontend will open in your browser at `http://localhost:8501`.*
