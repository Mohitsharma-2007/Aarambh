"""
End-to-end verification script for the Ontology Generation + Build pipeline.
Tests the full lifecycle: Generate Ontology -> Build Graph
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
import os
import json
import time

BASE_URL = "http://localhost:5001/api/graph"

def test_generate():
    """Test ontology generation endpoint"""
    print("=" * 60)
    print("STEP 1: Testing Ontology Generation")
    print("=" * 60)
    
    test_file = "test_doc.txt"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("""
India's Press Information Bureau (PIB) released multiple reports this week.
The Ministry of Finance announced new economic reforms targeting GDP growth.
Prime Minister Modi held bilateral meetings with foreign leaders.
The Reserve Bank of India (RBI) maintained the repo rate at 6.5%.
ISRO successfully launched a new satellite for weather monitoring.
The Ministry of Education introduced new policies for higher education.
Several state governments announced infrastructure development projects.
The opposition party criticized the government's handling of inflation.
Social media discussions focused on unemployment and rising prices.
""")
    
    files = [('files', (test_file, open(test_file, 'rb'), 'text/plain'))]
    data = {
        'project_name': 'E2E Verification Test',
        'simulation_requirement': 'Analyze Indian government announcements and public reactions'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/ontology/generate", data=data, files=files, timeout=120)
        print(f"Status: {response.status_code}")
        
        result = response.json()
        if response.status_code == 200 and result.get("success"):
            project_id = result["data"]["project_id"]
            entity_count = len(result["data"]["ontology"].get("entity_types", []))
            edge_count = len(result["data"]["ontology"].get("edge_types", []))
            print(f"[OK] SUCCESS: Project={project_id}, Entities={entity_count}, Edges={edge_count}")
            
            for e in result["data"]["ontology"].get("entity_types", []):
                print(f"   Entity: {e.get('name', '?')}")
            for e in result["data"]["ontology"].get("edge_types", []):
                print(f"   Edge: {e.get('name', '?')}")
            
            return project_id
        else:
            print(f"[FAIL] FAILED: {result.get('error', 'Unknown error')}")
            if "traceback" in result:
                print(f"   Traceback: {result['traceback'][:500]}")
            return None
    except Exception as e:
        print(f"[FAIL] REQUEST FAILED: {e}")
        return None
    finally:
        for _, (path, f, _) in files:
            f.close()
        if os.path.exists(test_file):
            os.remove(test_file)

def test_build(project_id):
    """Test graph build endpoint"""
    print()
    print("=" * 60)
    print(f"STEP 2: Testing Graph Build (project: {project_id})")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/build",
            json={"project_id": project_id},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        
        result = response.json()
        if response.status_code == 200 and result.get("success"):
            task_id = result["data"].get("task_id", "?")
            print(f"[OK] Build started: task_id={task_id}")
            return task_id
        else:
            print(f"[FAIL] Build FAILED: {result.get('error', 'Unknown')}")
            return None
    except Exception as e:
        print(f"[FAIL] REQUEST FAILED: {e}")
        return None

def poll_task(task_id, max_polls=30):
    """Poll task status until completion"""
    print()
    print("=" * 60)
    print(f"STEP 3: Polling Task Status (task: {task_id})")
    print("=" * 60)
    
    for i in range(max_polls):
        try:
            response = requests.get(f"{BASE_URL}/task/{task_id}", timeout=10)
            result = response.json()
            
            if result.get("success"):
                task = result["data"]
                status = task.get("status", "unknown")
                progress = task.get("progress", 0)
                message = task.get("message", "")
                
                print(f"  [{i+1}/{max_polls}] Status: {status} | Progress: {progress}% | {message}")
                
                if status == "completed":
                    print(f"[OK] BUILD COMPLETED SUCCESSFULLY!")
                    return True
                elif status == "failed":
                    print(f"[FAIL] BUILD FAILED: {task.get('error', '?')}")
                    return False
            
            time.sleep(3)
        except Exception as e:
            print(f"  Poll error: {e}")
            time.sleep(3)
    
    print("[TIMEOUT] Build did not complete within polling window")
    return False

if __name__ == "__main__":
    print()
    print("AARAMBH Ontology Engine E2E Verification")
    print("=" * 60)
    
    project_id = test_generate()
    
    if project_id:
        task_id = test_build(project_id)
        
        if task_id:
            success = poll_task(task_id)
            
            if success:
                print()
                print("FULL E2E TEST PASSED!")
            else:
                print()
                print("Build phase had issues - check server logs")
        else:
            print("\nBuild phase could not start")
    else:
        print("\nGeneration phase failed - check server logs")
