#!/usr/bin/env python3
"""
Test script for the ERP Copilot Flask Application
"""

import sys
import os
import requests
import json
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint."""
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_copilot_status():
    """Test the copilot status endpoint."""
    print("\nTesting /copilot/status endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/copilot/status")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Copilot status check failed: {e}")
        return False

def test_action_endpoint():
    """Test the action endpoint with sample data."""
    print("\nTesting /action endpoint...")
    try:
        sample_action = {
            "session_id": "test_session_123",
            "action": {
                "type": "open_screen",
                "payload": {
                    "screen": "SalesOrder"
                }
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/action",
            json=sample_action,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        response_data = response.json()
        print(f"Response: {json.dumps(response_data, indent=2)}")
        
        # Check if AI suggestion was provided
        ai_suggestion = response_data.get("ai_suggestion")
        if ai_suggestion:
            print(f"\n🤖 AI Suggestion received:")
            print(f"   Business Suggestion: {ai_suggestion.get('business_suggestion', 'N/A')}")
            print(f"   Requires Confirmation: {ai_suggestion.get('requires_confirmation', False)}")
            if ai_suggestion.get('action_id'):
                print(f"   Action ID: {ai_suggestion.get('action_id')}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Action endpoint test failed: {e}")
        return False

def test_pending_actions_workflow():
    """Test the complete pending actions workflow."""
    print("\nTesting pending actions workflow...")
    try:
        session_id = "test_workflow_session"
        
        # Step 1: Trigger an action that might generate AI suggestion
        action_data = {
            "session_id": session_id,
            "action": {
                "type": "open_screen",
                "payload": {
                    "screen": "PurchaseOrder"
                }
            }
        }
        
        print("Step 1: Triggering action...")
        response = requests.post(f"{BASE_URL}/action", json=action_data)
        
        if response.status_code != 200:
            print(f"❌ Action failed: {response.status_code}")
            return False
        
        response_data = response.json()
        ai_suggestion = response_data.get("ai_suggestion")
        
        if not ai_suggestion or not ai_suggestion.get("requires_confirmation"):
            print("ℹ️  No confirmable AI suggestion generated - this is normal")
            return True
        
        action_id = ai_suggestion.get("action_id")
        print(f"✅ AI suggestion generated with action_id: {action_id}")
        
        # Step 2: Get pending actions
        print("\nStep 2: Getting pending actions...")
        pending_response = requests.get(f"{BASE_URL}/action/pending?session_id={session_id}")
        pending_data = pending_response.json()
        print(f"Pending actions: {pending_data.get('count', 0)}")
        
        # Step 3: Get action details
        print(f"\nStep 3: Getting action details for {action_id}...")
        details_response = requests.get(f"{BASE_URL}/action/details/{action_id}")
        if details_response.status_code == 200:
            details = details_response.json()
            print(f"Action details: {details.get('business_suggestion', 'N/A')}")
        
        # Step 4: Test rejection
        print(f"\nStep 4: Testing action rejection...")
        reject_response = requests.post(f"{BASE_URL}/action/reject", json={
            "action_id": action_id,
            "reason": "Testing workflow"
        })
        
        if reject_response.status_code == 200:
            print("✅ Action rejected successfully")
            return True
        else:
            print(f"❌ Rejection failed: {reject_response.status_code}")
            return False
            
    except Exception as e:
        print(f"Pending actions workflow test failed: {e}")
        return False

def test_store_endpoints():
    """Test the store endpoints."""
    print("\nTesting /store endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/store")
        print(f"Status: {response.status_code}")
        store_data = response.json()
        print(f"Store keys: {store_data.get('keys', [])}")
        
        # Test getting a specific key if any exist
        if store_data.get('keys'):
            key = store_data['keys'][0]
            print(f"\nTesting /store/{key} endpoint...")
            detail_response = requests.get(f"{BASE_URL}/store/{key}")
            print(f"Status: {detail_response.status_code}")
            print(f"Details available: {len(detail_response.json())}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Store endpoints test failed: {e}")
        return False

def test_endpoints_management():
    """Test the endpoints management functionality."""
    print("\nTesting endpoints management...")
    try:
        # Test getting endpoints
        response = requests.get(f"{BASE_URL}/endpoints")
        print(f"Endpoints status: {response.status_code}")
        
        if response.status_code == 200:
            endpoints_data = response.json()
            print(f"Available endpoints: {endpoints_data.get('endpoint_names', [])}")
            print(f"Total endpoints: {endpoints_data.get('total_endpoints', 0)}")
        
        # Test reloading endpoints
        print("\nTesting endpoints reload...")
        reload_response = requests.post(f"{BASE_URL}/endpoints/reload")
        print(f"Reload status: {reload_response.status_code}")
        
        if reload_response.status_code == 200:
            reload_data = reload_response.json()
            print(f"Reload result: {reload_data.get('message', 'No message')}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Endpoints management test failed: {e}")
        return False

def test_learning_endpoints():
    """Test the learning database endpoints."""
    print("\nTesting learning endpoints...")
    try:
        # Test getting learning statistics
        print("Testing learning statistics...")
        stats_response = requests.get(f"{BASE_URL}/learning/statistics")
        print(f"Learning statistics status: {stats_response.status_code}")
        
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            print(f"Learning data available: {stats_data.get('status') == 'success'}")
            if stats_data.get('statistics'):
                print(f"Total suggestions tracked: {stats_data['statistics'].get('total_suggestions_tracked', 0)}")
        
        # Test getting learning patterns
        print("\nTesting learning patterns...")
        patterns_response = requests.get(f"{BASE_URL}/learning/patterns")
        print(f"Learning patterns status: {patterns_response.status_code}")
        
        if patterns_response.status_code == 200:
            patterns_data = patterns_response.json()
            print(f"Total patterns: {patterns_data.get('total_patterns', 0)}")
        
        # Test learning guidance (requires parameters)
        print("\nTesting learning guidance...")
        guidance_params = {
            "current_action": json.dumps({
                "type": "open_screen",
                "payload": {"screen": "SalesOrder"}
            }),
            "business_context": json.dumps({
                "session_length": 5,
                "most_common_screens": ["SalesOrder", "PurchaseOrder"]
            })
        }
        
        guidance_response = requests.get(f"{BASE_URL}/learning/guidance", params=guidance_params)
        print(f"Learning guidance status: {guidance_response.status_code}")
        
        if guidance_response.status_code == 200:
            guidance_data = guidance_response.json()
            print(f"Guidance received: {guidance_data.get('status') == 'success'}")
            if guidance_data.get('guidance'):
                print(f"Should suggest: {guidance_data['guidance'].get('should_suggest')}")
                print(f"Confidence score: {guidance_data['guidance'].get('confidence_score', 0):.2f}")
        
        return stats_response.status_code == 200
        
    except Exception as e:
        print(f"Learning endpoints test failed: {e}")
        return False

def test_feedback_workflow():
    """Test the complete feedback workflow with learning."""
    print("\nTesting feedback workflow with learning...")
    try:
        session_id = "test_learning_session"
        
        # Step 1: Generate a suggestion
        action_data = {
            "session_id": session_id,
            "action": {
                "type": "open_screen",
                "payload": {
                    "screen": "SalesOrder"
                }
            }
        }
        
        print("Step 1: Generating suggestion...")
        response = requests.post(f"{BASE_URL}/action", json=action_data)
        
        if response.status_code != 200:
            print(f"❌ Action failed: {response.status_code}")
            return False
        
        response_data = response.json()
        ai_suggestion = response_data.get("ai_suggestion")
        
        if not ai_suggestion or not ai_suggestion.get("requires_confirmation"):
            print("ℹ️  No confirmable AI suggestion generated")
            
            # Test manual feedback recording
            print("\nStep 2: Testing manual feedback recording...")
            feedback_data = {
                "action_id": "manual_test_123",
                "user_action": "rejected",
                "feedback_reason": "Not relevant to current task",
                "suggestion_context": {
                    "original_action": action_data["action"],
                    "business_suggestion": "Test business suggestion",
                    "suggested_action": None,
                    "business_context": {}
                }
            }
            
            feedback_response = requests.post(f"{BASE_URL}/learning/feedback", json=feedback_data)
            print(f"Manual feedback status: {feedback_response.status_code}")
            
            if feedback_response.status_code == 200:
                feedback_result = feedback_response.json()
                print(f"✅ Manual feedback recorded: {feedback_result.get('feedback_id')}")
                return True
            else:
                print(f"❌ Manual feedback failed: {feedback_response.status_code}")
                return False
        
        action_id = ai_suggestion.get("action_id")
        print(f"✅ AI suggestion generated with action_id: {action_id}")
        
        # Step 2: Test rejection with learning
        print(f"\nStep 2: Testing rejection with learning feedback...")
        reject_response = requests.post(f"{BASE_URL}/action/reject", json={
            "action_id": action_id,
            "reason": "Testing learning system - not relevant"
        })
        
        if reject_response.status_code == 200:
            print("✅ Action rejected and learning feedback recorded")
            
            # Step 3: Check if learning statistics updated
            print("\nStep 3: Checking learning statistics after feedback...")
            stats_response = requests.get(f"{BASE_URL}/learning/statistics")
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                if stats_data.get('statistics'):
                    rejection_rate = stats_data['statistics'].get('overall_rejection_rate', 0)
                    print(f"Current rejection rate: {rejection_rate:.1%}")
            
            return True
        else:
            print(f"❌ Rejection failed: {reject_response.status_code}")
            return False
            
    except Exception as e:
        print(f"Feedback workflow test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("ERP Copilot Flask Application Test Suite")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Copilot Status", test_copilot_status),
        ("Action Endpoint", test_action_endpoint),
        ("Store Endpoints", test_store_endpoints),
        ("Endpoints Management", test_endpoints_management),
        ("Learning Endpoints", test_learning_endpoints),
        ("Pending Actions Workflow", test_pending_actions_workflow),
        ("Feedback Learning Workflow", test_feedback_workflow)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "="*50)
    print("TEST RESULTS SUMMARY")
    print("="*50)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your Flask application is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
