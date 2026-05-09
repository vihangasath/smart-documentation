# Smart Documentation Architect

Smart Documentation Architect is a multi-agent orchestration system designed to automatically analyze Software Requirement Specification (SRS) documents and generate system architecture, Mermaid.js diagrams, and project boilerplate. 

## Overview

The system consists of two main components:
- **Backend (FastAPI)**: Built using Hexagonal Architecture (Ports and Adapters), it handles document parsing, multi-agent orchestration using the Gemini API, and serves outputs via a REST API with real-time Server-Sent Events (SSE) streaming for progress updates.
- **Frontend (React + Vite + TypeScript)**: A modern, responsive UI that allows users to upload SRS documents, view real-time analysis progress, and visualize extracted entities, relationships, and Mermaid.js diagrams.

## Features

- **SRS Document Upload**: Supports uploading text and SRS documents for analysis.
- **Multi-Agent Pipeline**: Extracts architectural insights, entities, and actions.
- **Real-Time Streaming (SSE)**: Live updates of the agent pipeline's progress.
- **Architecture Visualization**: Generates and renders interactive Mermaid.js diagrams.
- **Project Boilerplate Scaffolding**: Automatically scaffolds project structures based on architectural analysis.

## Getting Started

### Backend
1. Navigate to the `backend` directory.
2. Install dependencies.
3. Set up your `.env` file with necessary API keys (e.g., Gemini API key).
4. Run the development server: `uvicorn app.main:app --reload`

### Frontend
1. Navigate to the `frontend` directory.
2. Install dependencies using `npm install`.
3. Start the development server: `npm run dev`

## Architecture

This project follows a Hexagonal Architecture on the backend to separate concerns and ensure maintainability. The multi-agent orchestration system uses LLMs to parse and structure unstructured document data into actionable technical artifacts.
