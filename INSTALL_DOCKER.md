# Docker Installation for FestivAI

Docker isn't currently installed on your system. Here's how to set it up:

## Install Docker on macOS

### Option 1: Docker Desktop (Recommended)
1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop/
2. Install the .dmg file
3. Start Docker Desktop application
4. Wait for Docker to start (whale icon in menu bar)

### Option 2: Homebrew
```bash
brew install --cask docker
# Then start Docker Desktop application
```

## Verify Installation
```bash
docker --version
docker compose --version
```

## After Installation - Run FestivAI
```bash
# Navigate to project directory
cd "03. Festiv-AI -Personalised ads system for music festivals/FestivAI_2.0"

# Start Ollama service
docker compose up -d ollama

# Setup Mistral model (first time only)
./setup-ollama.sh

# Run FestivAI
docker compose run --rm festiv-ai
```

## Benefits Once Installed

✅ **Environment Consistency**: Exact Python 3.12 + dependencies
✅ **Isolated LLM**: Ollama runs separately from your system
✅ **Persistent Models**: Downloaded models survive restarts
✅ **Easy Resuming**: Pick up exactly where you left off next week
✅ **No Dependency Conflicts**: Completely isolated from your system Python

## Alternative: Continue Without Docker

If you prefer not to install Docker now, your current setup will continue working:

```bash
# Your current workflow (still works)
python -m src.main
```

The Docker setup is completely optional - it just makes environment management easier for next week!