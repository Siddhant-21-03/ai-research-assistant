# AI Research Assistant

This is a Retrieval-Augmented Generation (RAG) application built to help parse, search, and chat with personal documents like PDFs, CSVs, and text files. 

## Features

- **Document Processing Pipeline**: Uses LangChain and ChromaDB for chunking, generating embeddings, and storing vector context from uploaded files.
- **Conversational Memory**: The backend maintains chat history state to handle logical follow-up questions.
- **Context Filtering**: Users can query across the entire vector database or filter searches to a single specific document.
- **User Interface**: A Streamlit frontend providing a chat interface, source citations, document management, and usage statistics.
- **API Backend**: Built with FastAPI to keep the machine learning orchestration decoupled from the frontend client.

## Technology Stack

- **Backend**: Python, FastAPI
- **Frontend**: Streamlit
- **Machine Learning**: LangChain, ChromaDB, Google Gemini API
- **Data Loading**: PyPDFLoader, RecursiveCharacterTextSplitter

## Running Locally

### Prerequisites

- Python 3.10+
- A Google Gemini API Key

### Setup Instructions

1. Clone the repository and navigate into it:
   ```bash
   git clone https://github.com/Siddhant-21-03/ai-research-assistant.git
   cd ai-research-assistant
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   Create a `.env` file in the root directory and add your API key.
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

### Starting the Servers

The application requires both the backend API and the frontend server to be running simultaneously.

1. **Start the FastAPI Backend:**
   Open a terminal in the project directory:
   ```bash
   python -m uvicorn backend.main:app --reload
   ```
   The API will be available at `http://127.0.0.1:8000`.

2. **Start the Streamlit Frontend:**
   Open a second terminal window:
   ```bash
   streamlit run frontend/app.py
   ```
   The UI will be accessible at `http://localhost:8501`.
