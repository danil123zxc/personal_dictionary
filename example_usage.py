#!/usr/bin/env python3
"""
Example usage of the Continuous Learning Agent Architecture.

This script demonstrates how to:
1. Initialize an agent
2. Add information after launch
3. Submit feedback and corrections
4. Save and load agent state
"""

import asyncio
import json
from datetime import datetime

# Import the agent architecture
from app.agent_architecture import (
    ContinuousLearningAgent,
    AgentWorkflowManager,
    AgentUpdate,
    UpdateType
)

async def main():
    """Main example function."""
    
    print("🚀 Starting Continuous Learning Agent Example")
    print("=" * 50)
    
    # 1. Initialize the agent
    print("\n1. Initializing agent...")
    agent = ContinuousLearningAgent()
    workflow_manager = AgentWorkflowManager(agent)
    
    # Initial data
    initial_data = {
        "text": "Hello world, this is an example.",
        "src_language": "English",
        "tgt_language": "Spanish",
        "words": ["hello", "world"],
        "translations": {
            "hello": ["hola"],
            "world": ["mundo"]
        },
        "definitions": {
            "hello": ["A greeting"],
            "world": ["The earth and all life upon it"]
        },
        "examples": {
            "hello": ["Hello, how are you?"],
            "world": ["The world is beautiful"]
        }
    }
    
    # Run initial workflow
    result = await workflow_manager.run_initial_workflow(initial_data)
    print(f"✅ Agent initialized with session ID: {result['session_id']}")
    
    # 2. Add new words after launch
    print("\n2. Adding new words after launch...")
    new_words_update = AgentUpdate(
        update_type=UpdateType.NEW_WORDS,
        data={"words": ["example", "learning", "agent"]},
        user_id="user123"
    )
    
    result = await agent.process_update(new_words_update)
    print(f"✅ Added {result['result']['words_added']} new words")
    print(f"   Total words: {result['result']['total_words']}")
    
    # 3. Add new translations
    print("\n3. Adding new translations...")
    new_translations_update = AgentUpdate(
        update_type=UpdateType.NEW_TRANSLATIONS,
        data={
            "translations": {
                "example": ["ejemplo"],
                "learning": ["aprendizaje"],
                "agent": ["agente"]
            }
        },
        user_id="user123"
    )
    
    result = await agent.process_update(new_translations_update)
    print(f"✅ Added {result['result']['translations_added']} new translations")
    
    # 4. Submit feedback
    print("\n4. Submitting feedback...")
    feedback_update = AgentUpdate(
        update_type=UpdateType.FEEDBACK,
        data={
            "type": "translation_quality",
            "content": "The translation for 'hello' should include 'buenos días' as well",
            "word": "hello"
        },
        user_id="user123"
    )
    
    result = await agent.process_update(feedback_update)
    print(f"✅ Feedback stored: {result['result']['feedback_type']}")
    
    # 5. Apply corrections
    print("\n5. Applying corrections...")
    correction_update = AgentUpdate(
        update_type=UpdateType.CORRECTION,
        data={
            "translations": {
                "hello": ["hola", "buenos días"]
            }
        },
        user_id="user123"
    )
    
    result = await agent.process_update(correction_update)
    print(f"✅ Applied {result['result']['corrections_applied']} corrections")
    
    # 6. Add learning progress
    print("\n6. Updating learning progress...")
    progress_update = AgentUpdate(
        update_type=UpdateType.LEARNING_PROGRESS,
        data={
            "words_learned": 5,
            "accuracy_score": 0.85,
            "study_time_minutes": 30
        },
        user_id="user123"
    )
    
    result = await agent.process_update(progress_update)
    print(f"✅ Updated {len(result['result']['updated_fields'])} progress fields")
    
    # 7. Display current state
    print("\n7. Current agent state:")
    state = agent.get_state()
    print(f"   Session ID: {state['session_id']}")
    print(f"   Total words: {len(state['current_state'].get('words', set()))}")
    print(f"   Total translations: {len(state['current_state'].get('translations', {}))}")
    print(f"   Update count: {state['update_count']}")
    print(f"   Last updated: {state['last_updated']}")
    
    # 8. Save agent state
    print("\n8. Saving agent state...")
    agent.save_state("example_agent_state.json")
    print("✅ Agent state saved to 'example_agent_state.json'")
    
    # 9. Create a new agent and load the state
    print("\n9. Creating new agent and loading saved state...")
    new_agent = ContinuousLearningAgent()
    new_agent.load_state("example_agent_state.json")
    
    new_state = new_agent.get_state()
    print(f"✅ New agent loaded with session ID: {new_state['session_id']}")
    print(f"   Total words: {len(new_state['current_state'].get('words', set()))}")
    
    # 10. Add more information to the loaded agent
    print("\n10. Adding more information to loaded agent...")
    additional_update = AgentUpdate(
        update_type=UpdateType.NEW_WORDS,
        data={"words": ["continuous", "learning"]},
        user_id="user456"
    )
    
    result = await new_agent.process_update(additional_update)
    print(f"✅ Added {result['result']['words_added']} more words")
    
    # 11. Display final state
    print("\n11. Final agent state:")
    final_state = new_agent.get_state()
    print(f"   Session ID: {final_state['session_id']}")
    print(f"   Total words: {len(final_state['current_state'].get('words', set()))}")
    print(f"   Update count: {final_state['update_count']}")
    
    # 12. Show update history
    print("\n12. Recent update history:")
    recent_updates = agent.agent_state.update_history[-5:]  # Last 5 updates
    for i, update in enumerate(recent_updates, 1):
        print(f"   {i}. {update.update_type.value} - {update.timestamp.strftime('%H:%M:%S')}")
    
    print("\n🎉 Example completed successfully!")
    print("=" * 50)

def demonstrate_api_usage():
    """Demonstrate how to use the API endpoints."""
    
    print("\n📡 API Usage Examples:")
    print("=" * 30)
    
    # Example API calls (these would be HTTP requests in practice)
    api_examples = {
        "Initialize Agent": {
            "method": "POST",
            "endpoint": "/agent/initialize",
            "body": {
                "text": "Hello world",
                "src_language": "English",
                "tgt_language": "Spanish",
                "user_id": "user123"
            }
        },
        "Add Words": {
            "method": "POST",
            "endpoint": "/agent/add-words",
            "body": {
                "words": ["hello", "world", "example"],
                "user_id": "user123"
            }
        },
        "Add Translations": {
            "method": "POST",
            "endpoint": "/agent/add-translations",
            "body": {
                "translations": {
                    "hello": ["hola", "buenos días"],
                    "world": ["mundo"],
                    "example": ["ejemplo"]
                },
                "user_id": "user123"
            }
        },
        "Submit Feedback": {
            "method": "POST",
            "endpoint": "/agent/feedback",
            "body": {
                "feedback_type": "translation_quality",
                "content": "The translation should be more formal",
                "word": "hello",
                "user_id": "user123"
            }
        },
        "Get State": {
            "method": "GET",
            "endpoint": "/agent/state"
        },
        "Save State": {
            "method": "POST",
            "endpoint": "/agent/save-state",
            "params": {"filepath": "my_agent_state.json"}
        }
    }
    
    for operation, details in api_examples.items():
        print(f"\n{operation}:")
        print(f"  {details['method']} {details['endpoint']}")
        if 'body' in details:
            print(f"  Body: {json.dumps(details['body'], indent=4)}")
        if 'params' in details:
            print(f"  Params: {details['params']}")

if __name__ == "__main__":
    # Run the async example
    asyncio.run(main())
    
    # Show API usage examples
    demonstrate_api_usage()
    
    print("\n💡 Key Features of this Architecture:")
    print("=" * 40)
    print("✅ Continuous Learning: Agent can learn from new data after launch")
    print("✅ State Persistence: Save and load agent state across sessions")
    print("✅ Feedback Integration: Accept and process user feedback")
    print("✅ Correction Handling: Apply corrections to existing data")
    print("✅ Progress Tracking: Monitor learning progress over time")
    print("✅ Modular Design: Easy to extend with new update types")
    print("✅ API Integration: RESTful API for external interactions")
    print("✅ Session Management: Track user sessions and interactions")
