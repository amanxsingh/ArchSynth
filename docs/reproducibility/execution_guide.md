# ArchSynth v2.0 Execution & Reproducibility Guide

**Project**: ArchSynth v2.0 Research Platform  
**Document**: `docs/reproducibility/execution_guide.md`  

---

## 1. System Requirements

- **Operating System**: Ubuntu 22.04 LTS / 24.04 LTS or Windows 10/11 (PowerShell / Command Prompt)
- **Python Environment**: Python 3.10, 3.11, or 3.12
- **Hardware Prerequisites**: Minimum 8 GB RAM, 10 GB disk storage. GPU optional (only required if running local 70B models via Ollama; cloud Gemini requires zero local GPU).
- **Network**: Internet access required only for cloning remote repositories or calling Gemini / OpenAI APIs. If running in air-gapped defense mode, local Ollama requires no internet connection.

---

## 2. Environment Setup

### 2.1 Dependencies Installation
```bash
# Clone or unpack ArchSynth repository
cd archy

# Install Python dependencies
pip install -r requirements.txt

# Verify required core libraries
python -c "import pydantic, flask; print('Environment verified successfully!')"
```

### 2.2 Optional LLM API Configuration
ArchSynth can run fully statically without LLMs, or with local Ollama, or with cloud APIs. To enable cloud synthesis:
```bash
# In your .env file or shell environment:
export GEMINI_API_KEY="your-gemini-api-key"

# For local air-gapped execution via Ollama:
# 1. Install Ollama from https://ollama.com
# 2. Pull local model:
ollama pull llama3.1:70b
```

---

## 3. Running ArchSynth

### 3.1 Web Application Recovery Dashboard
To launch the interactive Glassmorphism Architecture Recovery Web Dashboard:
```bash
python app.py
```
Open your browser at:
- **Main Architecture Recovery Dashboard**: `http://localhost:5000/`
- **Research Benchmarking Suite**: `http://localhost:5000/benchmarks`
- **Interactive Presentation Deck**: `http://localhost:5000/presentation`

### 3.2 Command-Line Pipeline Execution
To run the end-to-end ArchSynth pipeline on any ROS 2 codebase via CLI:
```bash
# Analyze Navigation2
python -m src.main --repo case_studies/nav2 --output output/nav2_pipeline

# Analyze SLAM Toolbox
python -m src.main --repo case_studies/slam_toolbox --output output/slam_toolbox_pipeline

# Analyze with Evidence Validation enabled
python -m src.main --repo case_studies/nav2 --validate-evidence
```

---

## 4. Verification & Regression Testing

Execute the comprehensive 155-test verification suite:
```bash
python -m unittest tests.test_phase1_node_discovery tests.test_phase2_launch_analysis tests.test_phase3_interface_extraction tests.test_repository_isolation tests.test_slam_toolbox_launch tests.test_slam_toolbox_interfaces -v
```
Expected output:
```text
Ran 155 tests in ~5.9s
OK
```

---

## 5. Running Statistical Benchmarks
```bash
# Execute hypothesis testing and effect size calculations
python benchmarks/statistical_analysis/significance_tests.py
```
