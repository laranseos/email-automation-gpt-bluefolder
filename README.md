# Email Automation and Retrieval System

This project is an advanced email automation and retrieval system that integrates with Gmail, OpenAI, and BlueFolder APIs. It uses LangChain for document processing and Chroma for vector-based search, enabling efficient handling of emails, categorization, and automated replies.

---

## Features

- **Email Parsing**: Extract structured information from emails using GPT-based parsing.
- **Categorization**: Automatically categorize emails based on their content.
- **Blacklist Handling**: Ignore emails from blacklisted senders.
- **Service Request Fetching**: Fetch emails with BlueFolder service requests.
- **Automated Replies**: Generate and send replies based on parsed information and matched service requests.
- **Vector Search**: Retrieve relevant documents using FAISS and Chroma vector stores (RAG-based retrieval).

---

## Setup

### Prerequisites

- Python 3.8 or higher
- Gmail API credentials
- OpenAI API key
- BlueFolder API token

### Installation

1. **Clone the repository:**

   `git clone https://github.com/laranseos/email-automation-gpt-bluefolder.git`

   `cd email-automation-gpt-bluefolder`

2. **Install dependencies:**

pip install -r requirements.txt

3. **Set up environment variables:**

Create a .env file in the root directory.

Add the following:

    `OPENAI_API_KEY=your-openai-api-key`

    `BLUEFOLDER_API_TOKEN=your-bluefolder-api-token`

4. **Configure Gmail API:**

Place credentials.json and token.json in the services/ directory (you will be prompted to authenticate on first run).

### Running the Project

1.  **Train Context for Vector Search**
    To build the FAISS or Chroma vector store from PDF data:

        `python rag/train_context.py`

2.  **Process Emails**
    To fetch and process unread emails:

        `python main.py`
