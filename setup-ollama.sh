#!/bin/bash

# Setup script to pull the Mistral model in Ollama container
echo "Setting up Ollama with Mistral model..."

# Wait for Ollama service to be ready
echo "Waiting for Ollama service..."
until docker exec festiv-ollama ollama list >/dev/null 2>&1; do
    echo "Waiting for Ollama to start..."
    sleep 5
done

# Pull the Mistral model
echo "Pulling Mistral model..."
docker exec festiv-ollama ollama pull mistral:latest

echo "Setup complete! Ollama is ready with Mistral model."
echo "You can now run: docker-compose up festiv-ai"