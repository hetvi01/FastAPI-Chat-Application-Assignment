import random
import asyncio
from typing import Dict, List, Any

# Mock responses based on keywords
MOCK_RESPONSES = {
    "hello": [
        "Hello! How can I help you today?",
        "Hi there! What's on your mind?",
        "Greetings! How may I assist you?"
    ],
    "help": [
        "I'm here to help. What do you need assistance with?",
        "I'd be happy to help you. What's the issue?",
        "How can I be of assistance today?"
    ],
    "weather": [
        "I don't have real-time weather data, but I can tell you it's always sunny in the digital world!",
        "The weather forecast shows digital clouds with a chance of binary rain.",
        "Today's temperature is 101 in binary, quite pleasant!"
    ],
    "thanks": [
        "You're welcome!",
        "Happy to help!",
        "Anytime! Let me know if you need anything else."
    ],
    "bye": [
        "Goodbye! Have a great day!",
        "See you next time!",
        "Farewell! Come back soon."
    ]
}

# Default responses when no keywords match
DEFAULT_RESPONSES = [
    "That's an interesting question. Let me think about that...",
    "I don't have a specific answer for that, but I'm learning every day!",
    "I'm not sure I understand. Could you rephrase your question?",
    "That's beyond my current capabilities, but I'd be happy to help with something else.",
    "I'm processing your request... Here's what I can tell you: this is a simulated response."
]


async def generate_ai_response(question: str) -> Dict[str, Any]:
    """
    Simulates an AI service call by analyzing the question and returning 
    a relevant response based on keywords.
    
    Args:
        question: The user's question
        
    Returns:
        Dict with response and metadata
    """
    # Add a small delay to simulate network latency
    await asyncio.sleep(0.3)
    
    # Convert to lowercase for case-insensitive matching
    question_lower = question.lower()
    
    # Check for keywords in the question
    for keyword, responses in MOCK_RESPONSES.items():
        if keyword in question_lower:
            response = random.choice(responses)
            return {
                "response": response,
                "confidence": random.uniform(0.75, 0.98),
                "source": "mock_ai",
                "processing_time_ms": random.randint(50, 300)
            }
    
    # If no keywords match, return a default response
    return {
        "response": random.choice(DEFAULT_RESPONSES),
        "confidence": random.uniform(0.5, 0.7),
        "source": "mock_ai",
        "processing_time_ms": random.randint(100, 500)
    } 