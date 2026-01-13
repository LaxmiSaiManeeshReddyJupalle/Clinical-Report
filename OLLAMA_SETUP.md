# Ollama Integration Setup Guide

This guide explains how to set up local AI-powered report generation using Ollama.

## Why Ollama?

**HIPAA Compliance**: Ollama runs entirely on your local machine, ensuring:
- No PHI data is sent to external servers
- Complete data privacy and security
- Full control over the AI model
- No internet connection required after model download

## Installation

### Step 1: Install Ollama

**macOS:**
```bash
# Download and install from ollama.ai
curl -fsSL https://ollama.ai/install.sh | sh

# Or download the app from https://ollama.ai/download
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download the installer from: https://ollama.ai/download

### Step 2: Verify Installation

```bash
# Check Ollama is running
ollama --version

# Test connection
curl http://localhost:11434/api/tags
```

### Step 3: Download a Model

Choose a model based on your needs:

#### Recommended Models:

**llama3.2 (3B)** - Fast, efficient, good for summaries
```bash
ollama pull llama3.2
```

**llama3.1 (8B)** - Better quality, slower
```bash
ollama pull llama3.1:8b
```

**mistral (7B)** - Good balance of speed and quality
```bash
ollama pull mistral
```

### Step 4: Test the Model

```bash
# Interactive test
ollama run llama3.2

# Try a clinical summary prompt
>>> Summarize this patient note: "Patient presents with mild depression, prescribed Sertraline 50mg daily."

# Exit with /bye
```

## Using with the Clinical Report Generator

### 1. Start the Application

```bash
cd /Users/saimanish/Documents/Clinical\ report
source .venv/bin/activate
streamlit run src/ui/app.py
```

### 2. In the UI

1. Navigate to **Step 3: Generate Report**
2. Look for the **AI Synthesis Options** section
3. If Ollama is running, you'll see:
   - ✅ **Ollama available**
   - Checkbox: "🤖 Use Local AI (Ollama) for Report Synthesis"
4. Check the box to enable AI synthesis
5. Generate your report

### 3. What to Expect

**Without Ollama (Structured Format):**
```
## Full Summary

### Admission Information
**From: admission_summary.txt**
Patient admitted with major depressive disorder...
---

### Treatment Plan
**From: treatment_plan.txt**
Current medications: Sertraline 50mg daily...
```

**With Ollama (AI-Synthesized Narrative):**
```
## Clinical Summary

This patient was admitted to the acute treatment unit with a
diagnosis of major depressive disorder, recurrent, moderate severity.
The patient reports experiencing persistent depressed mood and
anhedonia for approximately three weeks prior to admission.

Treatment was initiated with Sertraline 50mg daily, along with
Trazodone 50mg at bedtime for insomnia. Over the course of the
hospitalization, the patient demonstrated gradual improvement...
```

## Troubleshooting

### Ollama Not Available

**Symptoms:**
- UI shows "Local AI not available"
- No checkbox for Ollama

**Solutions:**

1. **Check if Ollama is running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

   If this fails:
   ```bash
   # macOS/Linux
   ollama serve

   # Or restart the Ollama application
   ```

2. **Check if model is downloaded:**
   ```bash
   ollama list
   ```

   If no models listed:
   ```bash
   ollama pull llama3.2
   ```

3. **Restart the Streamlit app:**
   - Stop the app (Ctrl+C)
   - Restart: `streamlit run src/ui/app.py`

### Generation is Slow

**Cause:** Model is too large for your hardware

**Solutions:**
1. Use a smaller model (llama3.2 instead of llama3.1:8b)
2. Close other applications to free up RAM
3. For very old hardware, consider using CPU-only mode

### Report Quality Issues

**If reports are too generic:**
- Try a larger model (llama3.1 or mistral)
- The prompts are optimized for clinical documentation
- Structured format (without Ollama) may be more appropriate for certain use cases

**If reports are too verbose:**
- Use llama3.2 (more concise)
- Adjust temperature in `src/rag/ollama_client.py` (lower = more focused)

## Model Comparison

| Model | Size | Speed | Quality | Recommended For |
|-------|------|-------|---------|----------------|
| llama3.2 | 2GB | Fast | Good | Quick summaries, limited RAM |
| mistral | 4GB | Medium | Very Good | Balanced performance |
| llama3.1:8b | 4.7GB | Slow | Excellent | High-quality reports, powerful hardware |

## Configuration

### Change Default Model

Edit `src/ui/app.py` line 106:
```python
ollama = create_ollama_client(model="mistral", temperature=0.3)
```

### Adjust Generation Settings

Edit `src/rag/ollama_client.py`:

```python
@dataclass
class OllamaConfig:
    model: str = "llama3.2"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.3  # Lower = more focused (0.0-1.0)
    max_tokens: int = 2000    # Maximum length
    timeout: int = 120        # Timeout in seconds
```

## Testing the Integration

### Quick Test (Command Line)

```bash
cd /Users/saimanish/Documents/Clinical\ report
source .venv/bin/activate

python -c "
from src.rag.ollama_client import create_ollama_client

# Check availability
client = create_ollama_client()
if client:
    print('✅ Ollama connected')
    print(f'Available models: {client.list_models()}')

    # Test generation
    response = client.generate(
        'Summarize: Patient with depression, on Sertraline.',
        system_prompt='You are a clinical documentation specialist.'
    )
    print(f'Response: {response[:200]}...')
else:
    print('❌ Ollama not available')
"
```

### Full Integration Test

```bash
python -c "
from src.rag.vector_store import ClinicalVectorStore, DocumentChunk
from src.rag.retriever import ReportGenerator, ClinicalRetriever, ReportType
from src.rag.ollama_client import create_ollama_client, OllamaLLMAdapter

# Create test data
store = ClinicalVectorStore(persist_dir=None, collection_name='test')
store.add_documents([
    DocumentChunk(
        text='Patient admitted with MDD. Reports sad mood for 3 weeks.',
        metadata={'source': 'admission.txt'},
        doc_id='test1'
    )
])

# Create generator with Ollama
ollama = create_ollama_client()
if ollama:
    llm_client = OllamaLLMAdapter(ollama)
    retriever = ClinicalRetriever(store)
    generator = ReportGenerator(retriever, llm_client=llm_client)

    # Generate report
    report = generator.generate_report(
        query='patient summary',
        report_type=ReportType.FULL_SUMMARY
    )
    print('✅ Report generated with Ollama')
    print(report.content[:300])
else:
    print('❌ Ollama not available')
"
```

## Security Notes

- ✅ All processing happens locally
- ✅ No PHI leaves your machine
- ✅ HIPAA compliant
- ✅ Works offline (after model download)
- ✅ No API keys or external services required

## Performance Tips

1. **First run is slower**: Model needs to load into memory
2. **Keep Ollama running**: Don't close the Ollama app
3. **Sufficient RAM**: 8GB minimum, 16GB recommended
4. **SSD helps**: Models load faster from SSD

## Support

For Ollama-specific issues:
- Documentation: https://github.com/ollama/ollama
- Discord: https://discord.gg/ollama

For integration issues:
- Check application logs in terminal
- Verify mock data exists: `/mock_data/`
- Ensure all dependencies installed: `pip install -r requirements.txt`
