#!/bin/bash

# Create main project structure
mkdir -p omni

# Create core module
mkdir -p omni/core

# Create services module with submodules
mkdir -p omni/services/speech/recognition
mkdir -p omni/services/speech/synthesis
mkdir -p omni/services/speech/wake_word
mkdir -p omni/services/intent/handlers
mkdir -p omni/services/edge/cache
mkdir -p omni/services/cloud/api

# Create models module
mkdir -p omni/models

# Create utils module
mkdir -p omni/utils

# Create __init__.py files
find omni -type d -exec touch {}/__init__.py \;

# Create core module files
touch omni/core/{app,config,state,exceptions}.py

# Create speech module files
touch omni/services/speech/recognition/{base,vosk,whisper}.py
touch omni/services/speech/synthesis/{base,local_tts,espeak}.py
touch omni/services/speech/wake_word/{base,porcupine}.py

# Create intent module files
touch omni/services/intent/{engine,local_sti}.py

# Create edge module files
touch omni/services/edge/processor.py
touch omni/services/edge/cache/{base,memory_cache}.py

# Create cloud module files
touch omni/services/cloud/llm.py

# Create models files
touch omni/models/{intent,command,response}.py

# Create utils files
touch omni/utils/{async_utils,logging,validators}.py

# Create main application file
touch omni/main.py