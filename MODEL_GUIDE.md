# Clinical Report AI Models - Quick Reference

## 🏥 Medical-Specialized Models (HIGHLY RECOMMENDED)

### **Meditron** - Best for Clinical Documentation ⭐⭐⭐⭐⭐
```bash
ollama pull meditron
```
**Why choose Meditron:**
- Specifically trained on medical literature and clinical text
- Understands ICD codes, medical abbreviations, drug names
- Better at clinical terminology than general models
- Same performance cost as Mistral (~4GB)
- Pre-trained on 48B tokens of medical data

**Best for:**
- Psychiatric clinical notes (like ATU reports)
- Treatment plans
- Medication reviews
- Assessment summaries

---

### **BioMistral** - Medical & Biomedical Specialist ⭐⭐⭐⭐⭐
```bash
ollama pull biomistral
```
**Why choose BioMistral:**
- Trained on PubMed abstracts and medical texts
- Excellent with medical terminology
- Good at extracting key clinical information
- Based on Mistral architecture (reliable)

**Best for:**
- Complex medical terminology
- Research-heavy clinical notes
- Diagnostic summaries

---

## 🌟 General-Purpose Models (Strong Performers)

### **Llama 3.1 (8B)** - Best General Option ⭐⭐⭐⭐
```bash
ollama pull llama3.1:8b
```
**Why choose Llama 3.1:8b:**
- Excellent instruction following
- Good context understanding
- Well-tested and reliable
- Faster than 70B, better than 3B

**Best for:**
- General clinical summaries when medical-specific models aren't available
- Balanced speed and quality

---

### **Mistral (7B)** - Reliable Workhorse ⭐⭐⭐⭐
```bash
ollama pull mistral
```
**Why choose Mistral:**
- Very efficient
- Good at following formats
- Balanced performance
- Popular and well-supported

**Best for:**
- Structured reports
- When you need consistent formatting

---

### **Gemma 2 (9B)** - Instruction Expert ⭐⭐⭐⭐
```bash
ollama pull gemma2:9b
```
**Why choose Gemma 2:**
- Excellent at following specific formats
- Good with structured templates
- From Google (well-maintained)

**Best for:**
- When you have specific report templates
- Discharge summaries with standard formats

---

## 📊 Model Comparison for Your Hardware

### If you have 8GB RAM:
```bash
ollama pull llama3.2        # Start here (fast, lightweight)
```

### If you have 12-16GB RAM:
```bash
ollama pull meditron         # Best choice for clinical
# OR
ollama pull llama3.1:8b     # Best general-purpose
```

### If you have 20GB+ RAM:
```bash
ollama pull qwen2.5:14b     # Excellent with complex terminology
# OR
ollama pull meditron && ollama pull llama3.1:8b  # Best of both
```

### If you have 32GB+ RAM and GPU:
```bash
ollama pull llama3.1:70b    # Production-quality reports
```

---

## 🎯 Quick Start Recommendations

### **For Your Use Case (ATU Clinical Reports):**

**Option 1: Best Medical Understanding**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download medical specialist
ollama pull meditron

# Test it
ollama run meditron
```

**Option 2: Best Balance**
```bash
# Download both and compare
ollama pull meditron
ollama pull llama3.1:8b

# The UI will let you switch between them
```

**Option 3: Download Multiple for Comparison**
```bash
# Medical specialists
ollama pull meditron
ollama pull biomistral

# General purpose
ollama pull llama3.1:8b
ollama pull mistral

# Switch in the UI dropdown
```

---

## 🔬 Testing Different Models

Once you have multiple models installed, you can:

1. **In the UI**: Select from the dropdown in "AI Synthesis Options"
2. **Compare quality**: Generate the same report with different models
3. **Test speed**: See which works best for your hardware

---

## 💡 Pro Tips

### Speed vs Quality Trade-offs:
- **Fast reports**: llama3.2, mistral
- **Balanced**: meditron, llama3.1:8b, biomistral
- **Best quality**: llama3.1:70b, qwen2.5:14b

### Memory Usage:
- Models stay in RAM while running
- First generation is slower (loading)
- Subsequent generations are fast (cached)
- Close Ollama app to free RAM

### Clinical Accuracy:
**For psychiatric notes (your use case):**
1. ⭐⭐⭐⭐⭐ Meditron
2. ⭐⭐⭐⭐⭐ BioMistral
3. ⭐⭐⭐⭐ Llama 3.1:8b
4. ⭐⭐⭐⭐ Qwen 2.5:14b
5. ⭐⭐⭐ Mistral

---

## 🚀 Installation Commands Summary

```bash
# Install Ollama (one time)
curl -fsSL https://ollama.ai/install.sh | sh

# Recommended: Medical specialist (4GB)
ollama pull meditron

# Alternative: Best general model (5GB)
ollama pull llama3.1:8b

# Alternative: Other medical specialist (4GB)
ollama pull biomistral

# Budget option: Smallest model (2GB)
ollama pull llama3.2

# Premium option: Best quality (40GB, needs powerful hardware)
ollama pull llama3.1:70b
```

---

## 🔍 How to Check What You Have

```bash
# List installed models
ollama list

# Remove a model you don't need
ollama rm model-name

# Check disk space used
ollama list | awk '{print $2}' | tail -n +2
```

---

## 🏆 My Final Recommendation

**For your psychiatric clinical reports:**

```bash
# Primary model (best clinical understanding)
ollama pull meditron

# Backup model (faster, still good)
ollama pull llama3.1:8b
```

**Why?**
- Meditron understands depression, medications, psychiatric terminology
- Llama 3.1 is your fallback if Meditron is slow
- Both fit in 16GB RAM comfortably
- You can switch between them in the UI

**Storage needed:** ~7GB total
**RAM needed:** 12-16GB
**Time to download:** 10-20 minutes (depending on connection)

---

## 📚 Additional Resources

- **Ollama Models Library**: https://ollama.ai/library
- **Model Cards**: Check each model's page for training details
- **Meditron Paper**: https://arxiv.org/abs/2311.16079
- **BioMistral**: Based on medical PubMed corpus

---

## ❓ Quick FAQ

**Q: Can I use multiple models?**
Yes! Download several and switch in the UI dropdown.

**Q: Which is most accurate for depression notes?**
Meditron - it's trained specifically on clinical psych literature.

**Q: Which is fastest?**
llama3.2, but meditron is fast enough and more accurate.

**Q: Can I delete models?**
Yes: `ollama rm model-name`

**Q: Do models update?**
Yes, run `ollama pull model-name` again to update.

**Q: Is my data sent anywhere?**
NO - everything runs locally, HIPAA compliant.
