GET INN Restaurant Platform Documentation
==========================================

.. image:: https://img.shields.io/badge/version-1.0-blue.svg
   :alt: Version 1.0

.. image:: https://img.shields.io/badge/Python-3.9+-blue.svg
   :alt: Python 3.9+

.. image:: https://img.shields.io/badge/FastAPI-0.104+-green.svg
   :alt: FastAPI

Welcome to the GET INN Restaurant Platform documentation. This platform provides comprehensive 
restaurant management capabilities including bot-driven staff onboarding, labor management, 
procurement optimization, and multi-platform integrations.

🚀 Quick Start
==============

* **🛠️ Development Setup** - Get your development environment up and running quickly
* **🏗️ Architecture Overview** - Understand the platform's architecture and design principles  
* **🤖 Bot Management** - Learn about our conversational bot system
* **📚 API Reference** - Complete API documentation with examples

🏗️ Platform Overview
====================

The GET INN Restaurant Platform is built on a modern, scalable architecture designed for restaurant operations::

   FastAPI Backend
   ├── Bot Management System
   │   ├── Telegram
   │   └── WhatsApp
   ├── Labor Management
   ├── Procurement System
   ├── Integration Layer
   │   ├── iiko POS
   │   ├── Azure OpenAI
   │   └── External APIs
   ├── PostgreSQL Database
   ├── Redis Cache
   └── Celery Workers

Key Features
------------

**🤖 Multi-Platform Bot System**
   Conversational interfaces across Telegram, WhatsApp, and other platforms with advanced scenario management.

**👥 Labor Management**
   Automated staff onboarding, training tracking, and HR integrations.

**📦 Procurement & Inventory**
   Smart supplier management, automated reconciliation, and cost optimization.

**🔗 Restaurant Integrations**
   Seamless connections with POS systems (iiko), payment processors, and delivery platforms.

**🧠 AI-Powered Features**
   Document processing, intelligent recommendations, and automated decision support.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started
   :hidden:

   getting-started/installation
   getting-started/development-environment
   getting-started/testing

.. toctree::
   :maxdepth: 2
   :caption: Architecture
   :hidden:

   architecture/overview
   architecture/project-structure
   architecture/api-structure
   architecture/database-schema
   architecture/legal_entities_specification

.. toctree::
   :maxdepth: 2
   :caption: API Reference
   :hidden:

   api/index
   api/bot-management

.. toctree::
   :maxdepth: 2
   :caption: Bot Management
   :hidden:

   modules/bot-management/overview
   modules/bot-management/codebase-analysis
   modules/bot-management/scenario-format
   modules/bot-management/conversation-logging
   modules/bot-management/webhook-management
   modules/bot-management/media-system
   modules/bot-management/auto-transitions
   modules/bot-management/media-storage-db-migration

.. toctree::
   :maxdepth: 2
   :caption: AI Tools
   :hidden:

   modules/ai-tools/azure-openai
   modules/ai-tools/document-processing

.. toctree::
   :maxdepth: 2
   :caption: Integrations
   :hidden:

   modules/integrations/telegram
   modules/integrations/iiko

.. toctree::
   :maxdepth: 2
   :caption: Development Guides
   :hidden:

   guides/creating-api-endpoints
   guides/database-migrations
   guides/adding-bot-features


Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`