# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the scraping component of the Fridge2Fork project, a web scraping system designed to collect Korean recipe data from various cooking websites. The project uses MCP (Model Context Protocol) servers for enhanced functionality, particularly Playwright for browser automation and Sequential Thinking for complex analysis.

## Project Structure

This is part of a larger multi-component project:
- `/scrape` (this directory) - Web scraping component for recipe data collection
- `/server` - FastAPI backend server with PostgreSQL database
- `/mobile` - Flutter multi-platform mobile application

## Current State

The scraping directory is in a transition state with most Python files and documentation removed (as shown in git status). The focus has shifted to MCP-based automation tools configured in `.mcp.json`.

## MCP Configuration

The project is configured with two MCP servers:
- **playwright-server**: Browser automation for web scraping (`@playwright/mcp@latest`)
- **sequential-thinking**: Complex reasoning and analysis (`@modelcontextprotocol/server-sequential-thinking`)

## Development Context

### Target Data Sources
Based on project history, this scraping system is designed to collect Korean recipe data, likely from sites like "만개의레시피" (10,000 Recipes) and similar Korean cooking websites.

### Data Requirements
The scraped data should align with the API schema defined in `/docs/API_PLAN.md`, including:
- Recipe metadata (name, description, cooking time, difficulty, category)
- Ingredient lists with categorization
- Cooking steps and instructions
- Images and rating information

### Architecture Integration
Scraped data should be compatible with:
- FastAPI server endpoints (`/v1/recipes`)
- Flutter mobile app data models
- PostgreSQL database schema

## Related Documentation

Important reference documents:
- `/docs/API_PLAN.md` - Complete API endpoint specifications with Korean documentation
- `/docs/CURSOR.md` - Mobile app architecture and data model specifications
- `../server/README.md` - Server setup and architecture information

## Korean Development Context

This project includes extensive Korean documentation and targets Korean recipe content. When working with this codebase:
- Expect Korean comments and documentation
- Recipe categories follow Korean cooking classification (찜, 볶음, 밑반찬, 밥, 김치, 국/탕, 면)
- Ingredient names will be in Korean

## Session Management

The scraping system should support session-based operation to work with the API's session_id system for fridge management, allowing both authenticated and anonymous usage patterns.