# Multi Tenant Research Lab Knowledge Base

A secure multi tenant RAG system for a research lab with four different tenants and shared public documents. This system helps researchers find information from their own lab data and public documents while keeping everything secure and private.

## What This System Does

This system acts like a smart assistant for a research center that has four different labs:
- U1 Genomics Lab
- U2 NLP Lab  
- U3 Robotics Lab
- U4 Materials Lab

Each lab has their own private documents, but there are also public documents that everyone can access. The system makes sure users can only see what they are allowed to see and protects personal information.

## Key Features

- **Multi Tenant Security**: Each lab can only access their own private documents plus public documents
- **PII Protection**: Automatically hides personal information like phone numbers and ID numbers
- **Injection Detection**: Blocks attempts to break system rules or access unauthorized data
- **Memory Support**: Remembers conversations in chat mode using either buffer or summary memory
- **Proper Citations**: Always shows which documents were used to answer questions
- **Chat Interface**: Supports both single questions and multi turn conversations

## How It Works

1. **Planner**: Checks if your question is safe and not trying to break the system
2. **Retriever**: Searches through documents to find relevant information
3. **Policy Guard**: Makes sure you only see documents you are allowed to see and hides personal information
4. **LLM**: Generates answers using only the allowed information
5. **Memory**: Remembers your conversation if you are in chat mode

## Installation

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install requirements:
   ```
   pip install -r requirements.txt
   ```
4. Set up your API key:
   ```
   export GROQ_API_KEY="your-api-key-here"
   ```

## Usage

### Single Question Mode
Ask one question and get an answer:
```
python -m app.main --tenant U1 --query "What PPE is required in wet labs?" --memory summary --config config.yaml
```

### Chat Mode
Start a conversation that remembers what you talked about:
```
python -m app.main --tenant U1 --chat --memory buffer --config config.yaml
```

In chat mode you can use these commands:
- `/clear` - Delete conversation memory
- `/mode buffer` - Switch to buffer memory
- `/mode summary` - Switch to summary memory  
- `/exit` - Leave chat mode

## Configuration

The system uses `config.yaml` to control settings:

```yaml
llm:
  provider: groq
  model: llama-3.1-8b-instant
  temperature: 0.0
  max_tokens: 400

retrieval:
  backend: chroma
  top_k: 6
  chunk_size: 700
  chunk_overlap: 120

logging:
  path: logs/run.jsonl
```

## Security Features

### Access Control
- Users can only see their own lab's private documents
- Everyone can see public documents
- Cross tenant access is blocked

### PII Masking
The system automatically hides personal information:
- CNIC numbers: `12345-1234567-1` becomes `[REDACTED]`
- Phone numbers: `+92-300-1234567` becomes `[REDACTED]`

### Injection Detection
Blocks malicious queries like:
- "ignore all previous rules"
- "dump memory"
- "override policy guard"
- "exfiltrate data"

## Testing

Run the security tests:
```
pytest -q
```

Run red team testing:
```
python -m tools.run_redteam --config config.yaml
```

## Memory Types

### Buffer Memory
- Stores every conversation turn
- Uses more tokens but keeps all details
- Good for short conversations

### Summary Memory  
- Creates summaries of conversations
- Uses fewer tokens
- Good for long conversations
- May lose some details

## Project Structure

```
├── agents/           # Core system components
│   ├── controller.py # Main agent loop
│   ├── llm.py       # LLM wrapper
│   └── planner.py   # Query planning and security
├── app/             # User interface
│   ├── main.py      # CLI and chat interface
│   └── clear_memory.py
├── data/            # Lab documents and data
│   ├── L1_genomics/ # U1 lab documents
│   ├── L2_nlp/      # U2 lab documents  
│   ├── L3_robotics/ # U3 lab documents
│   ├── L4_materials/# U4 lab documents
│   └── public/      # Shared public documents
├── policies/        # Security policies
│   └── guard.py     # Policy enforcement
├── retrieval/       # Document search
│   ├── index.py     # Vector database
│   └── search.py    # Search and filtering
├── tests/           # Security tests
└── tools/           # Testing tools
```

## Logging

Every query is logged to `logs/run.jsonl` with details about:
- What was asked
- What documents were found
- What security checks were applied
- What answer was given
- How long it took

## Requirements

- Python 3.8+
- Groq API key
- ChromaDB for vector storage
- Sentence transformers for embeddings

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

This project was created for educational purposes as part of an Agentic AI course assignment.

## Contact

Created by Muhammad Zain Raza
Agentic AI Assignment 2
FAST-NUCES Islamabad