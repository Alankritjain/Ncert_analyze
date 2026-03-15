# NCERT Textbook Retrieval System

A complete local Python pipeline for semantic search and retrieval of NCERT textbook content using paragraph-level chunking, sentence transformers, and ChromaDB.

## 🎯 Features

- **Markdown Processing**: Parses NCERT textbooks in markdown format with heading hierarchy preservation
- **Intelligent Chunking**: Paragraph-level chunking with context preservation
- **Semantic Search**: Dense vector embeddings using `sentence-transformers/all-mpnet-base-v2`
- **Vector Storage**: Efficient storage and retrieval using ChromaDB
- **Rich Metadata**: Tracks class, subject, chapter, and heading context for every chunk
- **Structured Output**: JSON export with consistent schema
- **Ready for Integration**: Designed for easy FastAPI/Django backend integration
- **Cross-Encoder Ready**: Architecture prepared for future reranking implementation

## 📁 Project Structure

```
Ai_ML_sem4/
├── config/
│   ├── __init__.py
│   └── config.py                    # Central configuration
├── src/
│   ├── __init__.py
│   ├── parser/
│   │   ├── __init__.py
│   │   └── markdown_parser.py       # Markdown parsing with heading hierarchy
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── text_cleaner.py          # Text cleaning and normalization
│   │   ├── chunker.py               # Paragraph-level chunking
│   │   └── metadata_extractor.py    # Metadata extraction and enrichment
│   ├── embedding/
│   │   ├── __init__.py
│   │   ├── embedder.py              # Sentence-transformers embedding
│   │   └── vector_store.py          # ChromaDB interface
│   └── retrieval/
│       ├── __init__.py
│       └── retriever.py             # Semantic search interface
├── scripts/
│   ├── ingest_pipeline.py           # End-to-end ingestion pipeline
│   └── query_system.py              # Interactive query interface
├── data/
│   └── NCERT/                       # Input markdown files
│       └── Class_10/
│           └── Science/
│               └── Book_1/
│                   └── Chapter_01/
│                       └── chapter.md
├── output/
│   └── chunks/                      # JSON output files
├── chroma_db/                       # ChromaDB persistent storage
├── logs/                            # Pipeline logs
├── tests/
│   └── test_examples.py            # Test cases
├── requirements.txt
├── sample_json_schema.json         # Chunk schema definition
└── README.md
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or navigate to project directory
cd Ai_ML_sem4

# Install dependencies
pip install -r requirements.txt
```

### 2. Prepare Data

Place your markdown files in the expected structure:

```
data/NCERT/Class_XX/Subject/Book_X/Chapter_XX/chapter.md
```

Example:
```
data/NCERT/Class_10/Science/Book_1/Chapter_01/chapter.md
```

### 3. Run Ingestion Pipeline

```bash
# Process all markdown files and build vector index
python scripts/ingest_pipeline.py

# Clear existing data before ingestion
python scripts/ingest_pipeline.py --clear-existing

# Specify custom data directory
python scripts/ingest_pipeline.py --data-dir path/to/data
```

### 4. Query the System

```bash
# Interactive mode (recommended)
python scripts/query_system.py --interactive

# Single query
python scripts/query_system.py --query "What is photosynthesis?"

# Query with filters
python scripts/query_system.py --query "explain cell division" \
    --class-filter class10 \
    --subject-filter science \
    --top-k 3

# Export results to JSON
python scripts/query_system.py --query "photosynthesis" \
    --output results.json \
    --format json
```

## 📊 Pipeline Stages

### 1. Markdown Parsing
- Extracts content with heading hierarchy (H1, H2, H3)
- Preserves document structure
- Handles nested sections

### 2. Text Cleaning
- Unicode normalization
- Whitespace cleaning
- URL and HTML removal
- Preserves educational symbols (math notation)

### 3. Chunking
- Paragraph-level splitting
- Respects min/max size constraints (50-1000 chars)
- Maintains 50-character overlap
- Preserves heading context

### 4. Metadata Extraction
- Path-based: class, subject, book, chapter
- Content-based: headings, paragraph numbers
- Statistics: character count, word count
- Temporal: creation timestamp

### 5. Embedding Generation
- Model: `sentence-transformers/all-mpnet-base-v2`
- Dimension: 768
- Normalized vectors for cosine similarity
- Batch processing for efficiency

### 6. Vector Storage
- ChromaDB for persistent storage
- Cosine similarity metric
- Metadata filtering support
- Efficient similarity search

## 🔧 Configuration

Edit `config/config.py` to customize:

```python
# Chunking parameters
CHUNKING = {
    "strategy": "paragraph",
    "min_chunk_size": 50,
    "max_chunk_size": 1000,
    "overlap": 50,
    "preserve_headings": True
}

# Retrieval parameters
RETRIEVAL = {
    "top_k": 5,
    "score_threshold": 0.5,
    "rerank": False  # Enable for cross-encoder
}

# Embedding model
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
DEVICE = "cpu"  # Change to "cuda" for GPU
```

## 📋 Chunk Schema

Each chunk follows this structure:

```json
{
  "chunk_id": "class10_science_ch1_p003",
  "text": "Content of the paragraph...",
  "char_count": 223,
  "word_count": 42,
  "metadata": {
    "chunk_id": "class10_science_ch1_p003",
    "source_file": "data/NCERT/Class_10/Science/Book_1/Chapter_01/chapter.md",
    "class_name": "class10",
    "subject": "science",
    "book": "book1",
    "chapter": "ch1",
    "heading_h1": "Life Processes",
    "heading_h2": "Nutrition",
    "heading_h3": "Autotrophic Nutrition",
    "paragraph_number": 3,
    "char_count": 223,
    "word_count": 42,
    "created_at": "2026-03-12T10:30:45.123456",
    "schema_version": "1.0"
  }
}
```

## 🔍 Query Examples

### Interactive Mode
```bash
python scripts/query_system.py -i
```

Then:
```
🔍 Query: What is photosynthesis?
🔍 Query: filter:science
🔍 Query: explain cell division
🔍 Query: filter:class10
🔍 Query: clear
```

### Programmatic Usage

```python
from src.retrieval.retriever import SemanticRetriever

# Initialize retriever
retriever = SemanticRetriever()

# Search with filters
results = retriever.search(
    query="What is photosynthesis?",
    top_k=5,
    class_filter="class10",
    subject_filter="science"
)

# Access results
for result in results:
    print(f"Score: {result.similarity_score:.4f}")
    print(f"Context: {result.get_display_context()}")
    print(f"Text: {result.text}")
```

## 🔌 FastAPI Integration Example

```python
from fastapi import FastAPI, Query
from src.retrieval.retriever import SemanticRetriever

app = FastAPI()
retriever = SemanticRetriever()

@app.get("/search")
async def search(
    query: str,
    top_k: int = 5,
    class_name: str = Query(None, alias="class"),
    subject: str = None
):
    results = retriever.search(
        query=query,
        top_k=top_k,
        class_filter=class_name,
        subject_filter=subject
    )
    
    return {
        "query": query,
        "results": [r.to_dict() for r in results]
    }
```

## 🎯 Future Enhancements

### Cross-Encoder Reranking
Ready to integrate cross-encoder for improved ranking:

```python
# In config.py
RETRIEVAL = {
    "rerank": True,
    "rerank_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "rerank_top_k": 3
}
```

Implementation stub in `src/retrieval/retriever.py`:
```python
def _rerank_results(self, query: str, results: List[Dict]) -> List[Dict]:
    from sentence_transformers import CrossEncoder
    model = CrossEncoder(self.rerank_model)
    pairs = [(query, result['text']) for result in results]
    scores = model.predict(pairs)
    return sorted(zip(scores, results), reverse=True)
```

## 📝 Development

### Run Tests
```bash
python -m pytest tests/
```

### Add New Subject
Just add files in the expected structure:
```
data/NCERT/Class_10/Mathematics/Book_1/Chapter_01/chapter.md
```

Then rerun ingestion:
```bash
python scripts/ingest_pipeline.py
```

### Clear Vector Store
```bash
python scripts/ingest_pipeline.py --clear-existing
```

## 🐛 Troubleshooting

### No results found
- Ensure ingestion completed successfully
- Check vector store count: `python scripts/query_system.py` (interactive mode) → `stats`
- Verify markdown files are in correct location

### ChromaDB errors
- Delete `chroma_db/` folder and rerun ingestion
- Check disk space

### Model download issues
- First run downloads the model (~420MB)
- Requires internet connection
- Model cached in `~/.cache/torch/sentence_transformers/`

### Memory issues
- Reduce batch size in config
- Process fewer files at once
- Use CPU instead of GPU if VRAM limited

## 📄 License

Educational project for NCERT textbook retrieval.

## 👥 Authors

Education AI Team - Senior Python Architects

## 🙏 Acknowledgments

- Sentence Transformers for embedding models
- ChromaDB for vector storage
- NCERT for educational content
