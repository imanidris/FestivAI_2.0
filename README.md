# FestivAI 2.0

**AI-Powered Personalized Festival Poster Generation Platform**

FestivAI automatically creates personalized promotional posters for festival attendees by combining their favorite artists with AI-generated copy and professional festival templates. Built for scale with a clean, maintainable architecture.

## **What It Does**

Given user data, FestivAI:
1. **Finds each user's favorite artists** at festivals they can attend
2. **Generates personalized copy** using AI (Mistral) for each artist-festival combination
3. **Assembles custom posters** with artist photos, dates, and branded templates
4. **Exports ready-to-use PNGs** with intelligent text wrapping and perfect alignment

**Example Output:** Elena gets 3 personalized Pukkelpop posters for her favorite artists Mau P, Salute, and Levity—each with AI-generated copy tailored to her and the specific performance dates.

## **Key Features**

- **Multi-Festival Support** - Users get posters for all relevant artist-festival combinations
- **Location-Aware** - Only generates posters for festivals users can actually attend
- **AI Copy Generation** - Personalized promotional text via Ollama Mistral LLM
- **SVG Template System** - Professional festival branding with pixel-perfect zones
- **Smart Caching** - Avoids regenerating content unnecessarily
- **Comprehensive Validation** - Checks assets before generation starts
- **Detailed Manifest** - Tracks every generated poster with metadata
- **Intelligent Text Wrapping** - Multi-line text that respects pixel boundaries
- **Perfect Text Alignment** - Center-aligned text with custom anchor points

## **Architecture**

FestivAI uses a clean **5-step pipeline** that's easy to understand, debug, and extend:

```
Step 1: Personalization     → Load data + match users to artists/festivals
Step 2: Validation          → Check assets exist + templates parse correctly
Step 3: Content Generation  → Generate AI copy for each poster combination
Step 4: Poster Assembly     → Insert content into SVG templates
Step 5: Rendering & Export  → Convert to PNG + generate manifest
```

## **Project Structure**

```
festiv-ai/
├── README.md                    ← You are here
├── requirements.txt             ← Python dependencies
├── .gitignore                   ← Git exclusions
│
├── assets/                      ← Design assets
│   ├── templates/               ← Festival SVG templates + fonts
│   │   └── Pukkelpop_Festival/
│   │       ├── SVG/pkp_template.svg
│   │       └── Fonts/
│   └── artists/                 ← Artist photos (PNG/JPG)
│
├── data/                        ← Source data (CSV)
│   ├── festivals.csv            ← Festival info + template paths
│   ├── artists.csv              ← Artists + performance details
│   └── users.csv                ← Users + preferences + locations
│
├── output/                      ← Generated files (git-ignored)
│   ├── posters/                 ← Final PNG posters
│   ├── manifest.csv             ← Generation tracking
│   └── copy_cache.json          ← LLM response cache
│
└── src/                         ← Clean 5-step pipeline
    ├── main.py                  ← CLI + orchestration
    ├── config.py                ← Centralized configuration
    ├── step1_personalization.py ← Data loading + matching
    ├── step2_validation.py      ← Asset + template validation
    ├── step3_content_generation.py ← AI copy generation
    ├── step4_poster_assembly.py ← SVG template assembly
    └── step5_rendering.py       ← PNG rendering + manifest
```

## **Quick Start**

### **1. Installation**

```bash
# Clone repository
git clone <repository-url>
cd FestivAI_2.0

# Setup virtual environment
python -m venv festiv
source festiv/bin/activate  # On Windows: festiv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dependencies with conda (recommended)
conda install --file requirements.txt
```

### **2. Setup Ollama (for AI copy generation)**

```bash
# Install Ollama via package manager (recommended)
brew install ollama

# Pull AI model (Mistral - fast and efficient)
ollama pull mistral

# Start Ollama server (keep running)
ollama serve
```

### **3. Run FestivAI**

```bash
# Basic usage - generates all posters
python -m src.main

# Skip validation for testing
python -m src.main --skip-validation

# Custom options
python -m src.main --max-words 8 --variants 5
```

### **4. Check Results**

```bash
ls output/posters/          # Your generated PNG files (77 posters)
cat output/manifest.csv     # Generation details and metadata
```

**Current Project Status:**
- **18 Users** with realistic music preferences
- **45 Artist performances** at Pukkelpop 2025
- **77 Unique poster combinations** ready for generation
- **Pixel-perfect text positioning** with intelligent wrapping
- **AI-generated copy** using Mistral LLM
- **Professional festival branding** with Pukkelpop template

## **Configuration Options**

```bash
python -m src.main --help
```

| Option | Description | Default |
|--------|-------------|---------|
| `--data-dir` | Override data directory | `data/` |
| `--output-dir` | Override output directory | `output/posters/` |
| `--skip-validation` | Skip asset validation | `False` |
| `--ollama-host` | LLM server host | `http://localhost:11434` |
| `--ollama-model` | AI model name | `llama3.1:8b` |
| `--max-words` | Copy length limit | `12` |
| `--variants` | Copy variants per poster | `3` |

## 📊 **Data Schemas**

### **festivals.csv**
```csv
festival_id,name,date_range,location,template_path,font_paths
pkp2025,Pukkelpop 2025,"July 31 - August 3, 2025",Belgium,assets/templates/Pukkelpop_Festival/SVG/pkp_template.svg,"neutra-text-bold.otf,Montserrat-VariableFont_wght.ttf"
```

### **artists.csv**
```csv
artist_id,name,genre,image_path,festival_id,performance_date
mau_p,Mau P,"tech house, house, electronic",assets/artists/Mau P.png,pkp2025,"July 31, 2025"
```

### **users.csv**
```csv
user_id,name,favorite_artist_ids,preferred_location
u001,Elena,"mau_p,salute,levity","Spain,Belgium,France"
```

## 🎨 **Template System**

FestivAI uses **SVG templates** with intelligent zone detection:

- **Image Zone**: Gray rectangle (`#2d2d2d`) → Replaced with artist photo
- **Text Zones**: Placeholder strings → Replaced with content
  - `{{ARTIST_NAME}}` → Artist name (uppercase)
  - `{{DATE}}` → Performance date
  - `{{COPY}}` → AI-generated promotional copy

Templates support CSS styling and preserve all design attributes.

## 📈 **Scaling & Customization**

### **Adding New Festivals**
1. Add SVG template to `assets/templates/{festival_name}/`
2. Add festival row to `festivals.csv`
3. Add artist performances to `artists.csv` with new `festival_id`

### **Adding New Templates**
1. Export SVG from Illustrator with placeholder zones
2. Use gray rectangle (`#2d2d2d`) for artist image placement
3. Add placeholder text: `{{ARTIST_NAME}}`, `{{DATE}}`, `{{COPY}}`

### **Custom Copy Generation**
Modify `step3_content_generation.py` to:
- Use different LLM models/providers
- Implement custom scoring functions
- Add genre-specific copy styles
- Integrate with marketing APIs

## 🧪 **Current Demo Data**

- **1 Festival**: Pukkelpop 2025 (Belgium)
- **45 Artist Performances**: Across July 31 - August 3
- **18 Users**: From diverse global locations
- **77 Poster Combinations**: Average 4.3 posters per user

## 🛠️ **Development**

### **Testing Individual Steps**
```python
from src.step1_personalization import run_step1
from pathlib import Path

matches, summary = run_step1(Path("data"))
print(f"Found {len(matches)} personalized matches")
```

### **Custom Pipeline**
```python
from src.main import run_pipeline

run_pipeline(
    data_dir=Path("custom_data"),
    skip_validation=True,
    max_words=8
)
```

## 🎯 **Use Cases**

- **Festival Marketing**: Personalized social media campaigns
- **Email Marketing**: Custom poster attachments per user
- **Event Promotion**: Print materials tailored to attendee preferences
- **Artist Promotion**: Cross-promotional content across multiple festivals
- **Agency Workflows**: Automated asset generation for music industry clients

## 📋 **Requirements**

- **Python**: 3.11+
- **LLM**: Ollama + llama3.1:8b (or compatible model)
- **SVG Rasterizer**: resvg-py (recommended) or cairosvg
- **Templates**: SVG files with placeholder zones
- **Assets**: Artist photos (PNG/JPG)

## 🤝 **Contributing**

The modular 5-step architecture makes contributions straightforward:

1. **Step improvements**: Enhance individual pipeline steps
2. **Template support**: Add new festival template formats
3. **LLM integration**: Support additional AI providers
4. **Data connectors**: Add APIs for live festival/artist data
5. **Output formats**: Support additional export formats

## 📜 **License**

MIT License - see LICENSE file for details.

---

**Built for music industry professionals who need scalable, personalized marketing assets at festival scale.** 🎵✨