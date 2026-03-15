# NCERT Retrieval System - Quick Start Guide

## Step-by-Step Setup

### 1. Prerequisites
- Python 3.8 or higher
- pip package manager
- ~2GB free disk space (for models and data)

### 2. Installation (5 minutes)

```bash
# Navigate to project directory
cd C:\Ai_ML_sem4

# Install all dependencies
pip install -r requirements.txt
```

**Note**: First run will download the embedding model (~420MB). This is a one-time download.

### 3. Verify Installation

```bash
# Run test examples
python tests/test_examples.py
```

### 4. Quick Demo with Sample Data

The project includes a sample chapter. Let's process it:

```bash
# Run ingestion pipeline
python scripts/ingest_pipeline.py

# Expected output:
# - Found 1 markdown files
# - Extracted X sections
# - Created Y chunks
# - Indexed Y chunks in vector database
```

### 5. Query the System

**Interactive Mode** (Recommended):
```bash
python scripts/query_system.py --interactive
```

Try these sample queries:
```
🔍 Query: What is oxidation?
🔍 Query: Explain chemical reactions
🔍 Query: What causes rusting?
🔍 Query: Types of decomposition reactions
```

**Single Query Mode**:
```bash
python scripts/query_system.py --query "What is oxidation?" --top-k 3
```

### 6. Add Your Own Data

1. Create directory structure:
```
data/NCERT/Class_10/YourSubject/Book_1/Chapter_01/chapter.md
```

2. Add your markdown files

3. Run ingestion:
```bash
# This will add to existing data
python scripts/ingest_pipeline.py

# Or clear existing and start fresh
python scripts/ingest_pipeline.py --clear-existing
```

## Common Commands

### Check System Status
```bash
python scripts/query_system.py -i
# Then type: stats
```

### Query with Filters
```bash
# Filter by subject
python scripts/query_system.py --query "photosynthesis" --subject-filter science

# Filter by class and subject
python scripts/query_system.py --query "cell division" \
    --class-filter class10 \
    --subject-filter biology \
    --top-k 5
```

### Export Results to JSON
```bash
python scripts/query_system.py \
    --query "chemical equations" \
    --output results.json \
    --format json
```

## Customization

### Change Chunk Size
Edit `config/config.py`:
```python
CHUNKING = {
    "min_chunk_size": 100,    # Increase for larger chunks
    "max_chunk_size": 1500,   # Increase max size
    "overlap": 75,            # More overlap for context
}
```

### Change Number of Results
Edit `config/config.py`:
```python
RETRIEVAL = {
    "top_k": 10,              # Return more results
    "score_threshold": 0.6,   # Higher threshold = stricter matching
}
```

### Use GPU (if available)
Edit `config/config.py`:
```python
DEVICE = "cuda"  # Change from "cpu" to "cuda"
```

## Troubleshooting

### Problem: No markdown files found
**Solution**: Check your data directory structure:
```bash
python -c "from config.config import Config; print(Config.DATA_DIR)"
```

### Problem: ChromaDB errors
**Solution**: Delete and rebuild:
```bash
# Windows
rmdir /s chroma_db
python scripts/ingest_pipeline.py --clear-existing
```

### Problem: Out of memory
**Solution**: Reduce batch size in the embedding process. Edit `scripts/ingest_pipeline.py`:
```python
# Line with embed_chunks:
self.embedder.embed_chunks(all_chunks, batch_size=16)  # Reduced from 32
```

### Problem: Model download fails
**Solution**: Manually download model:
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
# This will cache the model
```

## Performance Tips

1. **Batch processing**: Process multiple files at once for efficiency
2. **GPU acceleration**: Use GPU if available (10x faster)
3. **Chunk size**: Larger chunks = fewer embeddings but less precision
4. **Index management**: Rebuild index periodically for best performance

## Integration Examples

### Python Script
```python
from src.retrieval.retriever import SemanticRetriever

retriever = SemanticRetriever()
results = retriever.search("What is photosynthesis?", top_k=5)

for result in results:
    print(f"Score: {result.similarity_score}")
    print(f"Text: {result.text}")
```

### FastAPI Endpoint
```python
from fastapi import FastAPI
from src.retrieval.retriever import SemanticRetriever

app = FastAPI()
retriever = SemanticRetriever()

@app.get("/search")
def search(q: str, k: int = 5):
    results = retriever.search(q, top_k=k)
    return {"results": [r.to_dict() for r in results]}
```

### Django View
```python
from django.http import JsonResponse
from src.retrieval.retriever import SemanticRetriever

retriever = SemanticRetriever()

def search_view(request):
    query = request.GET.get('q', '')
    results = retriever.search(query, top_k=5)
    
    return JsonResponse({
        'query': query,
        'results': [r.to_dict() for r in results]
    })
```

## Next Steps

1. ✅ Complete this quick start
2. 📚 Add your textbook content
3. 🔍 Test query quality with real questions
4. 🎯 Tune configuration for your use case
5. 🚀 Integrate with your backend (FastAPI/Django)
6. 📊 Implement cross-encoder reranking (optional)

## Need Help?

- Check `README.md` for detailed documentation
- Review `sample_json_schema.json` for data format
- Run `python tests/test_examples.py` to verify setup
- Check logs in `logs/` directory

## Success Metrics

After setup, you should be able to:
- ✓ Index 100+ chunks per minute
- ✓ Query in under 1 second
- ✓ Get relevant results with >0.7 similarity score
- ✓ Filter by class/subject/chapter

Enjoy building your NCERT retrieval system! 🎉
