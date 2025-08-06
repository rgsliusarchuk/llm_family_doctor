# Knowledge Base Usage Guide

## Overview

The doctor-approved answers serve as a comprehensive knowledge base that can be used in multiple ways:

1. **Semantic Search**: Find similar cases and diagnoses
2. **Exact Matching**: Get precise matches for identical symptoms
3. **Doctor Attribution**: Track which doctor approved which diagnosis
4. **Audit Trail**: Full history of all approved diagnoses
5. **Learning Resource**: Training data for improving the system

## API Endpoints

### 1. Get Knowledge Base Statistics

```bash
GET /knowledge-base/
```

**Response:**
```json
{
  "total_entries": 150,
  "approved_entries": 142,
  "total_doctors": 8,
  "latest_entry": "2024-01-15T14:30:00Z",
  "most_active_doctor": "Dr. Іван Петренко"
}
```

### 2. Search Knowledge Base

```bash
POST /knowledge-base/search
```

**Request:**
```json
{
  "query": "headache fever",
  "top_k": 5,
  "min_similarity": 0.8
}
```

**Response:**
```json
{
  "query": "headache fever",
  "results": [
    {
      "id": 123,
      "symptoms_hash": "abc123...",
      "answer_md": "## ✍️ 1. Коротка відповідь для пацієнта\n\nЙмовірний діагноз: Грип...",
      "approved": true,
      "doctor_id": 1,
      "doctor_name": "Dr. Іван Петренко",
      "doctor_position": "Сімейний лікар",
      "created_at": "2024-01-15T14:30:00Z",
      "similarity_score": 0.95
    }
  ],
  "total_found": 1,
  "search_method": "semantic"
}
```

### 3. List All Entries

```bash
GET /knowledge-base/entries?limit=50&offset=0&approved_only=true
```

### 4. Get Specific Entry

```bash
GET /knowledge-base/entries/123
```

### 5. Get Doctor's Entries

```bash
GET /knowledge-base/doctors/1/entries?limit=20&offset=0
```

## Use Cases

### 1. **Medical Training & Education**

```python
# Get all diagnoses by a specific doctor for training
import requests

def get_doctor_diagnoses(doctor_id: int):
    response = requests.get(f"/knowledge-base/doctors/{doctor_id}/entries")
    return response.json()

# Analyze patterns in diagnoses
doctor_entries = get_doctor_diagnoses(1)
for entry in doctor_entries:
    print(f"Diagnosis: {entry['answer_md'][:100]}...")
    print(f"Date: {entry['created_at']}")
```

### 2. **Quality Assurance**

```python
# Monitor approval rates and doctor activity
def get_qa_stats():
    response = requests.get("/knowledge-base/")
    stats = response.json()
    
    approval_rate = stats['approved_entries'] / stats['total_entries']
    print(f"Approval rate: {approval_rate:.2%}")
    print(f"Most active doctor: {stats['most_active_doctor']}")
```

### 3. **Research & Analytics**

```python
# Analyze diagnosis patterns over time
def analyze_trends():
    entries = requests.get("/knowledge-base/entries?limit=1000").json()
    
    # Group by month
    monthly_counts = {}
    for entry in entries:
        month = entry['created_at'][:7]  # YYYY-MM
        monthly_counts[month] = monthly_counts.get(month, 0) + 1
    
    return monthly_counts
```

### 4. **Patient Care Improvement**

```python
# Find similar cases for better diagnosis
def find_similar_cases(symptoms: str):
    response = requests.post("/knowledge-base/search", json={
        "query": symptoms,
        "top_k": 3,
        "min_similarity": 0.85
    })
    
    return response.json()['results']
```

## Integration Examples

### 1. **Telegram Bot Enhancement**

```python
# Add knowledge base search to Telegram bot
async def handle_knowledge_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    
    # Search knowledge base
    response = await api_client.search_knowledge_base({
        "query": query,
        "top_k": 3
    })
    
    if response['results']:
        message = "🔍 **Знайдені схожі випадки:**\n\n"
        for result in response['results']:
            message += f"• {result['answer_md'][:100]}...\n"
            message += f"  _Лікар: {result['doctor_name']}_\n\n"
    else:
        message = "❌ Схожих випадків не знайдено."
    
    await update.message.reply_text(message, parse_mode='Markdown')
```

### 2. **Web Dashboard**

```python
# Flask/FastAPI web dashboard
@app.route('/dashboard')
def dashboard():
    # Get knowledge base stats
    stats = requests.get("/knowledge-base/").json()
    
    # Get recent entries
    recent_entries = requests.get("/knowledge-base/entries?limit=10").json()
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         entries=recent_entries)
```

### 3. **Export for Analysis**

```python
# Export knowledge base for external analysis
def export_knowledge_base():
    entries = requests.get("/knowledge-base/entries?limit=10000").json()
    
    # Convert to CSV
    import csv
    with open('knowledge_base_export.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Symptoms Hash', 'Diagnosis', 'Doctor', 'Date'])
        
        for entry in entries:
            writer.writerow([
                entry['id'],
                entry['symptoms_hash'],
                entry['answer_md'],
                entry['doctor_name'],
                entry['created_at']
            ])
```

## Advanced Features

### 1. **Semantic Search Enhancement**

```python
# Improve semantic search with custom thresholds
def enhanced_search(query: str, specialty: str = None):
    # Adjust similarity threshold based on specialty
    min_similarity = 0.9 if specialty == "emergency" else 0.8
    
    response = requests.post("/knowledge-base/search", json={
        "query": query,
        "top_k": 5,
        "min_similarity": min_similarity
    })
    
    return response.json()
```

### 2. **Knowledge Base Analytics**

```python
# Analyze knowledge base quality
def analyze_knowledge_quality():
    stats = requests.get("/knowledge-base/").json()
    
    # Calculate metrics
    metrics = {
        "total_cases": stats['total_entries'],
        "approval_rate": stats['approved_entries'] / stats['total_entries'],
        "doctor_participation": stats['total_doctors'],
        "avg_cases_per_doctor": stats['approved_entries'] / stats['total_doctors']
    }
    
    return metrics
```

### 3. **Automated Quality Checks**

```python
# Check for potential issues in knowledge base
def quality_check():
    entries = requests.get("/knowledge-base/entries?limit=1000").json()
    
    issues = []
    for entry in entries:
        # Check for very short diagnoses
        if len(entry['answer_md']) < 50:
            issues.append(f"Entry {entry['id']}: Very short diagnosis")
        
        # Check for missing doctor attribution
        if not entry['doctor_name']:
            issues.append(f"Entry {entry['id']}: Missing doctor attribution")
    
    return issues
```

## Best Practices

1. **Regular Backups**: Export knowledge base regularly for backup
2. **Quality Monitoring**: Monitor approval rates and doctor activity
3. **Search Optimization**: Use appropriate similarity thresholds
4. **Data Privacy**: Ensure patient data is properly anonymized
5. **Performance**: Use pagination for large datasets

## Future Enhancements

1. **Machine Learning**: Use knowledge base to train better models
2. **Automated Categorization**: Categorize diagnoses by specialty
3. **Trend Analysis**: Identify emerging health patterns
4. **Integration**: Connect with external medical databases
5. **Real-time Updates**: WebSocket updates for new approvals 