# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Korean recipe scraper that extracts recipe data from 10000recipe.com (만개의 레시피). The project is designed for efficient, large-scale data collection with PostgreSQL storage and ingredient analysis capabilities.

## Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables (copy from env.example)
cp env.example .env
# Edit .env with your database credentials
```

### Running the Crawler
```bash
# Main execution
python crawler.py

# Docker execution
docker build -t recipe-crawler .
docker run recipe-crawler
```

### Environment Variables
Essential configuration in `.env`:
- `POSTGRES_*`: Database connection settings
- `TARGET_RECIPE_COUNT`: Number of recipes to scrape (default: 200000)
- `CONCURRENT_REQUESTS`: Async request limit (default: 2)
- `CHUNK_SIZE`: Memory-efficient processing batch size (default: 100)
- `REQUEST_DELAY`: Rate limiting delay in seconds (default: 3.0)

## Architecture

### Core Components

**crawler.py** - Main application with three distinct processing phases:
1. **URL Collection**: Synchronous pagination through recipe list pages
2. **Data Extraction**: Asynchronous scraping of individual recipe details
3. **Data Storage**: PostgreSQL batch insertion with transaction management

### Key Design Patterns

**Memory-Efficient Streaming**: Uses generator-based URL collection instead of loading all URLs into memory
- `get_recipe_urls_generator()` yields URLs on-demand
- `process_chunk()` handles data in configurable chunks
- Automatic garbage collection between chunks

**Ingredient Parsing**: Sophisticated text analysis for Korean recipe ingredients
- `parse_ingredient()` handles quantities, units, and vague expressions
- Supports fractional quantities (1/2), ranges (1~2), and Korean descriptors (약간, 적당히)
- Categorizes ingredients by importance (essential vs optional)

**Database Schema**: Normalized structure with three main tables:
- `recipes`: Core recipe metadata
- `ingredients`: Normalized ingredient catalog
- `recipe_ingredients`: Many-to-many relationship with quantities

### Async Architecture

- Uses `aiohttp.ClientSession` for concurrent HTTP requests
- Semaphore-controlled concurrency (`CONCURRENT_REQUESTS`)
- Built-in rate limiting and error recovery
- Chunk-based processing to prevent OOM issues

## Data Structure

### Recipe Data Format
```python
{
    "url": "https://www.10000recipe.com/recipe/1234567",
    "title": "Recipe Name",
    "image_url": "https://...",
    "description": "Recipe description",
    "ingredients": [
        {
            "name": "ingredient_name",
            "quantity_from": 1.0,
            "quantity_to": None,
            "unit": "큰술",
            "is_vague": False,
            "vague_description": None,
            "importance": "essential"
        }
    ]
}
```

### Output Files
- `recipes.json`: Array format for complete dataset
- `recipes.jsonl`: Line-delimited JSON for streaming
- PostgreSQL tables for normalized storage

## Performance Tuning

### Memory Management
- Adjust `CHUNK_SIZE` for memory constraints (50-100 for limited RAM)
- Increase `CHUNK_DELAY` for memory recovery time
- Monitor with built-in `psutil` memory logging

### Rate Limiting
- Decrease `CONCURRENT_REQUESTS` to reduce server load
- Increase `REQUEST_DELAY` to be more respectful to target site
- Batch database operations with `BATCH_SIZE`

### Database Optimization
- Uses connection pooling (`SimpleConnectionPool`)
- Batch upserts with conflict resolution
- Transaction-safe error handling

## Development Notes

### Error Handling
- Graceful degradation for individual recipe failures
- Automatic retry logic for network errors
- Comprehensive logging with structured output
- Memory usage monitoring and warnings

### Code Organization
- Synchronous functions for pagination and setup
- Asynchronous functions for concurrent data extraction
- Separate modules for database operations and parsing
- Configuration-driven behavior via environment variables

### Korean Language Support
- Handles Korean ingredient names and descriptions
- Parses Korean quantity expressions (큰술, 티스푼, etc.)
- Supports Korean vague quantity indicators (약간, 적당히)

This codebase prioritizes data quality, system reliability, and respectful scraping practices while maintaining high performance for large-scale recipe collection.