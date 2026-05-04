# FestivAI Docker Setup

This Docker configuration packages FestivAI with Ollama for easy deployment and consistent environments.

## Quick Start

### 1. Build and Start Services
```bash
# Build FestivAI and start Ollama
docker-compose up -d ollama

# Setup Mistral model (first time only)
./setup-ollama.sh

# Run FestivAI poster generation
docker-compose run --rm festiv-ai
```

### 2. Alternative: One-Command Setup
```bash
# Start everything and run generation
docker-compose up --build
```

## Services

### Ollama (LLM Service)
- **Port**: 11434
- **Model**: mistral:latest
- **Volume**: Persistent model storage in `ollama_data`
- **Health Check**: Automatically tested before FestivAI starts

### FestivAI (Main Application)
- **Depends on**: Ollama service
- **Volumes**:
  - `./output:/app/output` - Generated posters persist on host
  - `./data:/app/data` - Easy data updates
  - `./assets:/app/assets` - Easy asset updates

## Usage Commands

### Development Mode
```bash
# Keep containers running for debugging
docker-compose up -d

# Execute commands inside FestivAI container
docker exec -it festiv-ai python -m src.main --max-words 8
docker exec -it festiv-ai python -c "from src.step1_personalization import run_step1; print(run_step1('data'))"
```

### Production Mode
```bash
# Run generation and exit
docker-compose run --rm festiv-ai

# Custom options
docker-compose run --rm festiv-ai python -m src.main --max-words 8 --variants 5
```

### Model Management
```bash
# Check available models
docker exec festiv-ollama ollama list

# Pull different model
docker exec festiv-ollama ollama pull llama3.2

# Test model
docker exec festiv-ollama ollama run mistral "Hello world"
```

## File Structure
```
.
├── docker-compose.yml     # Multi-service configuration
├── Dockerfile            # FestivAI container definition
├── setup-ollama.sh       # Model setup script
├── .dockerignore         # Exclude unnecessary files
└── output/               # Generated posters (persisted)
```

## Volumes Explained

### Persistent Data
- **`ollama_data`**: Stores downloaded models (survives container restarts)
- **`./output`**: Generated posters saved to host filesystem

### Development Mounts
- **`./data`**: Mount for easy CSV updates
- **`./assets`**: Mount for template/image updates
- **`./src`**: Add this mount for live code editing

## Troubleshooting

### Ollama Connection Issues
```bash
# Check Ollama health
docker logs festiv-ollama
curl http://localhost:11434/api/tags

# Restart Ollama
docker-compose restart ollama
```

### Model Missing
```bash
# Re-run setup
./setup-ollama.sh

# Manual model pull
docker exec festiv-ollama ollama pull mistral:latest
```

### Permissions Issues
```bash
# Fix output permissions
sudo chown -R $USER:$USER output/
```

## Benefits of This Setup

1. **Consistent Environment**: Same Python/dependencies everywhere
2. **Isolated LLM**: Ollama runs in its own container
3. **Persistent Storage**: Models and outputs survive restarts
4. **Easy Development**: Mount volumes for live editing
5. **Simple Deployment**: One command deployment
6. **Version Lock**: Current working state preserved

## Next Week Workflow

```bash
# Pull latest changes
git pull

# Restart with any updates
docker-compose down
docker-compose up --build

# Your environment is exactly as you left it!
```