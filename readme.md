# KlassIQ API Integration Documentation

## Overview

KlassIQ provides a comprehensive RESTful API for integrating Nigerian curriculum-aligned lesson planning into your educational applications. Our API offers access to structured curriculum data and AI-powered lesson plan generation.

## Base URL

**Production**: `https://klassiq.onrender.com`
**Staging**: Contact us for staging environment access

## Authentication

Currently, no authentication is required for basic API access. API keys will be introduced for production usage limits.

## Core Endpoints

### Health Check
```
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "message": "KlassIQ backend is running smoothly.",
  "curriculum_map_exists": true,
  "curriculum_grades": 3,
  "curriculum_subjects": 19
}
```

### Get Available Grades
```
GET /curriculum/grades
```

**Response:**
```json
{
  "grades": [
    "Junior Secondary 1–3", 
    "Primary 1–3", 
    "Primary 4–6"
  ]
}
```

### Get Subjects for Grade
```
GET /curriculum/{grade}/subjects
```

**Parameters:**
- `grade`: URL-encoded grade level (e.g., `Junior%20Secondary%201–3`)

**Response:**
```json
{
  "grade": "Junior Secondary 1–3",
  "subjects": [
    "cca", 
    "crs", 
    "english_studies", 
    "history", 
    "islamic", 
    "nvc", 
    "prevoc"
  ]
}
```

### Get Topics for Subject
```
GET /curriculum/{grade}/{subject}/topics
```

**Parameters:**
- `grade`: URL-encoded grade level
- `subject`: Subject identifier

**Response:**
```json
{
  "grade": "Junior Secondary 1–3",
  "subject": "english_studies",
  "topics": [
    "Reading for maximum retention and recall (intensive reading)",
    "Reading for main and supporting ideas",
    "Parts of Speech: Nouns, Verbs and Adjectives"
  ]
}
```

### Get Curriculum Data
```
POST /curriculum
Content-Type: application/json
```

**Request Body:**
```json
{
  "grade": "Junior Secondary 1–3",
  "subject": "english_studies",
  "topic": "Parts of Speech"
}
```

**Response:**
```json
{
  "grade": "Junior Secondary 1–3",
  "subject": "english_studies",
  "topic": "Parts of Speech",
  "curriculum_data": {
    "objectives": [
      "identify the features of nouns, verbs and adjectives in a given passage",
      "use nouns, verbs and adjectives correctly in sentences"
    ],
    "content": [
      "Parts of Speech: Nouns, Verbs and Adjectives",
      "Definition and examples of each part of speech"
    ],
    "teacher_activities": [
      "Explains what parts of speech are",
      "Gives examples of nouns, verbs and adjectives"
    ],
    "student_activities": [
      "Listen attentively to teacher's explanation",
      "Participate in identifying parts of speech"
    ],
    "resources": [
      "Recommended English textbook",
      "Chalkboard",
      "Exercise books"
    ],
    "topic_name": "Parts of Speech: Nouns, Verbs and Adjectives"
  }
}
```

### Generate Lesson Plan
```
POST /generate-plan
Content-Type: application/json
```

**Request Body:**
```json
{
  "grade": "JSS 1",
  "subject": "English",
  "topic": "reading comprehension",
  "teacher_input": "We have basic classroom materials like chalk and blackboard"
}
```

**Response:**
```json
{
  "grade": "JSS 1",
  "subject": "English", 
  "topic": "reading comprehension",
  "lesson_plan": {
    "title": "Reading Comprehension for JSS 1",
    "objectives": [
      "Students will identify main ideas in passages",
      "Students will answer comprehension questions"
    ],
    "learning_outcomes": [
      "Read passages fluently",
      "Extract key information from texts"
    ],
    "introduction": "Begin by asking students about their reading habits...",
    "activities": [
      "Warm-up: Discussion about reading (5 minutes)",
      "Main activity: Reading and comprehension exercise (20 minutes)",
      "Group work: Discuss passage themes (10 minutes)"
    ],
    "assessment": [
      "Students answer comprehension questions",
      "Peer assessment of reading fluency"
    ],
    "materials": [
      "Reading passages",
      "Chalkboard", 
      "Exercise books"
    ],
    "classroom_management": [
      "Ensure all students can see the board",
      "Use clear voice projection"
    ]
  },
  "from_cache": false
}
```

## Smart Input Handling

The API intelligently handles various input formats:

### Grade Formats (All Accepted)
- `"JSS 1"` → `"Junior Secondary 1–3"`
- `"Junior Secondary 1"` → `"Junior Secondary 1–3"`
- `"Primary 4"` → `"Primary 4–6"`
- `"Pri 2"` → `"Primary 1–3"`

### Subject Formats (All Accepted)
- `"English"` → `"english_studies"`
- `"Mathematics"` → `"maths"`
- `"Science"` → `"basic_science_technology"`
- `"Creative Arts"` → `"cca"`

### Topic Matching
- Partial matches supported (case-insensitive)
- `"reading"` matches `"Reading for maximum retention and recall"`
- `"parts of speech"` matches `"Parts of Speech: Nouns, Verbs and Adjectives"`

## Integration Examples

### JavaScript/Node.js
```javascript
const fetch = require('node-fetch');

class KlassIQClient {
  constructor(baseUrl = 'https://klassiq.onrender.com') {
    this.baseUrl = baseUrl;
  }

  async getGrades() {
    const response = await fetch(`${this.baseUrl}/curriculum/grades`);
    return response.json();
  }

  async generateLessonPlan(grade, subject, topic, teacherInput = '') {
    const response = await fetch(`${this.baseUrl}/generate-plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ grade, subject, topic, teacher_input: teacherInput })
    });
    return response.json();
  }
}

// Usage
const client = new KlassIQClient();
const lessonPlan = await client.generateLessonPlan('JSS 1', 'English', 'Reading');
```

### Python
```python
import requests

class KlassIQClient:
    def __init__(self, base_url='https://klassiq.onrender.com'):
        self.base_url = base_url
    
    def get_grades(self):
        response = requests.get(f'{self.base_url}/curriculum/grades')
        return response.json()
    
    def generate_lesson_plan(self, grade, subject, topic, teacher_input=''):
        payload = {
            'grade': grade,
            'subject': subject, 
            'topic': topic,
            'teacher_input': teacher_input
        }
        response = requests.post(f'{self.base_url}/generate-plan', json=payload)
        return response.json()

# Usage
client = KlassIQClient()
lesson_plan = client.generate_lesson_plan('JSS 1', 'English', 'Reading')
```

### PHP
```php
<?php

class KlassIQClient {
    private $baseUrl;
    
    public function __construct($baseUrl = 'https://klassiq.onrender.com') {
        $this->baseUrl = $baseUrl;
    }
    
    public function getGrades() {
        $response = file_get_contents($this->baseUrl . '/curriculum/grades');
        return json_decode($response, true);
    }
    
    public function generateLessonPlan($grade, $subject, $topic, $teacherInput = '') {
        $data = array(
            'grade' => $grade,
            'subject' => $subject,
            'topic' => $topic,
            'teacher_input' => $teacherInput
        );
        
        $options = array(
            'http' => array(
                'header'  => "Content-type: application/json\r\n",
                'method'  => 'POST',
                'content' => json_encode($data)
            )
        );
        
        $context = stream_context_create($options);
        $response = file_get_contents($this->baseUrl . '/generate-plan', false, $context);
        return json_decode($response, true);
    }
}

// Usage
$client = new KlassIQClient();
$lessonPlan = $client->generateLessonPlan('JSS 1', 'English', 'Reading');
?>
```

## Error Handling

### HTTP Status Codes
- `200`: Success
- `404`: Resource not found (invalid grade/subject/topic combination)
- `500`: Internal server error

### Error Response Format
```json
{
  "detail": "Error description explaining what went wrong"
}
```

### Common Errors
- `Grade 'XYZ' not found. Available grades: [...]`
- `Subject 'XYZ' not found in Grade. Available subjects: [...]`
- `Topic 'XYZ' not found in subject for grade`

## Rate Limits

Currently no rate limits are enforced. Production usage will implement:
- 100 requests per minute for free tier
- 1000 requests per minute for premium tier

## Support

For integration support, API issues, or feature requests:
- Email: support@klassiq.com
- Documentation: https://docs.klassiq.com
- Status Page: https://status.klassiq.com

## Changelog

### Version 1.0.0
- Initial API release
- Curriculum data access endpoints
- AI lesson plan generation
- Smart input normalization
- Nigerian curriculum coverage for Primary 1-6 and JSS 1-3