# Vector Store Setup Guide

## Issue
The `add_data.py` script requires OpenAI's Assistants API with Vector Stores support to upload and index the Contoso Pizza documents.

## Current Status
✅ **Code is working correctly** - it gracefully handles the API limitation and provides helpful error messages.

❌ **Vector stores not supported** by:
- Synthetic API (api.synthetic.new)
- DeepSeek API (api.deepseek.com)

## Solutions

### Option 1: Use Real OpenAI API (Recommended)
1. Get an API key from https://platform.openai.com/api-keys
2. Update your `.env` file:
```env
OPENAI_API_KEY=sk-your-real-openai-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL_ID=gpt-4o-mini
```
3. Run the script: `python add_data.py`

### Option 2: Use Azure OpenAI Service
1. Set up Azure OpenAI with Assistants API enabled
2. Update your `.env` file with Azure credentials:
```env
OPENAI_API_KEY=your-azure-api-key
OPENAI_BASE_URL=https://your-resource.openai.azure.com/openai
OPENAI_MODEL_ID=your-deployment-name
```

### Option 3: Use Azure AI Projects (Advanced)
1. Create an Azure AI Project
2. Get the connection string
3. Add to `.env`:
```env
PROJECT_CONNECTION_STRING=your-connection-string
```

## What the Script Does
When properly configured with OpenAI API, the script will:
1. ✅ Read all files from `./documents/` folder (20 Contoso Pizza location files)
2. ✅ Upload each file to OpenAI's file storage
3. ✅ Create a vector store named "contoso-pizza-store-information"
4. ✅ Index all files in the vector store for semantic search
5. ✅ Create an agent with file search capability
6. ✅ Test the agent with a query about store hours
7. ✅ Clean up by deleting the vector store and uploaded files

## Files Ready for Upload
The script is configured to upload these 20 markdown files:
- contoso_pizza_amsterdam.md
- contoso_pizza_boston.md
- contoso_pizza_chicago.md
- contoso_pizza_cologne.md
- contoso_pizza_delhi.md
- contoso_pizza_dubai.md
- contoso_pizza_ho_chi_minh_city.md
- contoso_pizza_hyderabad.md
- contoso_pizza_kampala.md
- contoso_pizza_mexico_city.md
- contoso_pizza_milwaukee.md
- contoso_pizza_mukono.md
- contoso_pizza_new_york.md
- contoso_pizza_perth.md
- contoso_pizza_pune.md
- contoso_pizza_san_francisco.md
- contoso_pizza_sao_paulo.md
- contoso_pizza_seattle.md
- contoso_pizza_singapore.md
- contoso_pizza_washington_dc.md

## Testing Without Vector Stores
If you want to test the agent without vector stores, use `main.py` instead:
```bash
python main.py
```

This will run a basic pizza bot without document search capabilities.

