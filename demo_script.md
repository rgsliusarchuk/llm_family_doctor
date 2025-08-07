# LLM Family Doctor - Demo Script
## 5-Minute Demonstration Guide

---

## PRE-DEMO SETUP (Before Presentation)

### 1. System Preparation
```bash
# Start all services
make redis-start
docker-compose up -d

# Verify services are running
curl http://localhost:8000/health
```

### 2. Test Data Preparation
- Have Telegram bot running and ready
- Prepare sample medical queries
- Have API documentation page ready
- Test bot responsiveness and functionality

### 3. Backup Plans
- Screenshots of Telegram bot interactions (in case of technical issues)
- Pre-recorded demo video of bot functionality
- Static screenshots of bot responses

---

## DEMO SCRIPT (5 minutes total)

### PART 1: Telegram Bot Demo (3 minutes)

**Opening (30 seconds):**
"Let me start by showing you our Telegram bot interface. This is our conversational medical assistant that provides instant guidance through natural language interaction."

**Step 1: Bot Introduction and Setup (30 seconds)**
- Open Telegram and find your bot
- Show the welcome message and available commands
- Point out: "The bot provides a natural, conversational interface for medical guidance"

**Step 2: Intent Classification Demo (45 seconds)**
- Send message: "Привіт, де знаходиться ваша клініка?"
- Show the response with clinic information
- Point out: "Notice how the system automatically classified this as a clinic information request"
- Send: "Коли приймає лікар Іванов?"
- Show doctor schedule response
- Highlight: "The system intelligently routes different types of queries"

**Step 3: Medical Diagnosis Demo (1 minute)**
- Send: "У мене головний біль в скроневій ділянці"
- Show the medical diagnosis flow
- Point out: "The system collects patient information naturally through conversation"
- Show the evidence-based recommendations
- Highlight: "See how we provide specific guidance based on Ukrainian clinical protocols"

**Step 4: Complex Medical Query (45 seconds)**
- Send: "Кашель і температура 38°C, що робити?"
- Show the comprehensive response
- Point out: "The system handles complex medical queries with detailed guidance"

**Talking Points:**
- "The bot uses the same backend API for consistent responses"
- "Intent classification automatically routes user queries"
- "Natural language understanding makes it accessible to everyone"
- "All responses are based on official medical protocols"

### PART 2: Technical Features Demo (2 minutes)

**Transition (15 seconds):**
"Now let me show you the technical infrastructure that powers our conversational medical assistant."

### PART 2: Technical Features Demo (2 minutes)

**Transition (15 seconds):**
"Let me show you some of the technical features that make this system production-ready."

**Step 1: API Documentation (45 seconds)**
- Open `http://localhost:8000/docs`
- Show the auto-generated FastAPI documentation
- Point out: "Complete API documentation with interactive testing"
- Show the `/assistant/message` endpoint that powers the bot

**Step 2: Caching System (30 seconds)**
- Show Redis cache status
- Demonstrate response speed improvement
- Point out: "Multi-layer caching reduces costs and improves performance"

**Step 3: Vector Search Results (30 seconds)**
- Show FAISS index statistics
- Display sample search results
- Point out: "Semantic search across 30+ clinical protocols"

**Step 4: Monitoring (15 seconds)**
- Show LangSmith tracing (if configured)
- Point out: "Complete observability and monitoring"

**Talking Points:**
- "Production-ready with comprehensive monitoring"
- "Cost optimization through intelligent caching"
- "Scalable architecture ready for enterprise deployment"

---

## DEMO TALKING POINTS & KEY MESSAGES

### Technical Excellence
- "Built with modern, scalable technologies"
- "Production-ready with CI/CD pipeline"
- "Comprehensive testing and monitoring"
- "Cost-optimized through intelligent caching"

### Business Value
- "Solves real healthcare access problems"
- "Based on official medical protocols"
- "Available 24/7 through conversational interface"
- "Ready for immediate deployment"

### Competitive Advantages
- "Official Ukrainian clinical protocols"
- "Multilingual support with medical terminology"
- "Conversational interface accessibility"
- "Production-ready infrastructure"

---

## DEMO TROUBLESHOOTING

### If Telegram Bot Doesn't Respond
- "Let me show you a screenshot of the bot interface"
- "The system is designed with a natural, conversational UI"
- "Users can easily ask questions and receive guidance"

### If API Documentation Doesn't Load
- "Our API provides comprehensive endpoints"
- "Here's the endpoint structure"
- "The system is fully documented and ready for integration"

---

## POST-DEMO TRANSITION

**Closing Statement (30 seconds):**
"As you can see, LLM Family Doctor provides instant, evidence-based medical guidance through an intelligent conversational interface. The system is production-ready, cost-efficient, and ready to help millions of Ukrainians access reliable medical information through natural language interaction."

**Transition to Q&A:**
"Now I'm ready to answer any questions about the technical implementation, business model, or future development plans."

---

## DEMO CHECKLIST

### Before Demo:
- [ ] Telegram bot running and tested
- [ ] Sample medical queries prepared
- [ ] Backup screenshots ready
- [ ] API documentation accessible
- [ ] Bot responsiveness verified

### During Demo:
- [ ] Keep to time limits
- [ ] Speak clearly and confidently
- [ ] Highlight key technical features
- [ ] Show real functionality
- [ ] Address any technical issues gracefully

### After Demo:
- [ ] Be ready for technical questions
- [ ] Have business metrics ready
- [ ] Prepare for architecture questions
- [ ] Know your competitive advantages
