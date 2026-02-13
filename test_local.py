#!/usr/bin/env python3
"""
FlowIQ Local Testing Script
Tests all endpoints to verify setup is working correctly
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8080"
TENANT_ID = None  # Will be set after tenant creation


def test_create_tenant():
    """Test tenant creation or get existing"""
    global TENANT_ID

    print_section("2. Testing Tenant Creation")

    # Get user input for Jira credentials
    print("\nPlease provide your Jira credentials:")
    company_name = input("Company name: ").strip() or "Test Company"
    jira_url = input("Jira URL (e.g., https://company.atlassian.net): ").strip()
    jira_email = input("Jira email: ").strip()
    jira_token = input("Jira API token: ").strip()

    if not all([jira_url, jira_email, jira_token]):
        print("❌ Missing required Jira credentials")
        return False

    payload = {
        "company_name": company_name,
        "jira_url": jira_url,
        "jira_email": jira_email,
        "jira_token": jira_token,
        "daily_rate_per_person": 2500.0
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/tenants",
            json=payload,
            timeout=10
        )

        if response.status_code in [200, 201]:
            data = response.json()
            TENANT_ID = data['id']
            print_result("Create tenant", True)
            print(f"\n   Tenant ID: {TENANT_ID}")
            print(f"   Company: {data['company_name']}")
            print(f"   Plan: {data['plan']}")
            print(f"   Status: {data['status']}")
            return True
        elif response.status_code == 400 and "already exists" in response.text:
            # Tenant exists - ask user for ID
            print("\nℹ️  Tenant already exists for this Jira URL.")
            print("Please get your tenant ID from the database:")
            print(
                '  docker-compose exec postgres psql -U flowiq -d flowiq -c "SELECT id FROM tenants WHERE jira_url = \'{}\\"'.format(jira_url))

            tenant_id = input("\nEnter your Tenant ID (UUID): ").strip()

            if not tenant_id:
                print("❌ No tenant ID provided")
                return False

            # Verify tenant exists
            verify_response = requests.get(f"{BASE_URL}/api/tenants/{tenant_id}", timeout=5)
            if verify_response.status_code == 200:
                TENANT_ID = tenant_id
                data = verify_response.json()
                print_result("Using existing tenant", True)
                print(f"\n   Tenant ID: {TENANT_ID}")
                print(f"   Company: {data['company_name']}")
                print(f"   Plan: {data['plan']}")
                print(f"   Status: {data['status']}")
                return True
            else:
                print("❌ Tenant ID not found")
                return False
        else:
            print_result("Create tenant", False, response.json())
            return False

    except Exception as e:
        print_result("Create tenant", False, {"detail": str(e)})
        return False

def print_section(title):
    """Print section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_result(test_name, success, response=None):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {test_name}")
    if response and not success:
        print(f"   Error: {response.get('detail', 'Unknown error')}")

def test_health():
    """Test health endpoint"""
    print_section("1. Testing Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        success = response.status_code == 200
        print_result("Health check", success, response.json())
        return success
    except Exception as e:
        print_result("Health check", False, {"detail": str(e)})
        return False

def test_get_tenant():
    """Test get tenant info"""
    print_section("3. Testing Get Tenant Info")
    
    if not TENANT_ID:
        print("❌ No tenant ID available")
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/tenants/{TENANT_ID}",
            timeout=5
        )
        success = response.status_code == 200
        print_result("Get tenant info", success, response.json() if not success else None)
        return success
    except Exception as e:
        print_result("Get tenant info", False, {"detail": str(e)})
        return False

def test_usage_stats():
    """Test usage statistics"""
    print_section("4. Testing Usage Statistics")
    
    if not TENANT_ID:
        print("❌ No tenant ID available")
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/tenants/{TENANT_ID}/usage",
            timeout=5
        )
        success = response.status_code == 200
        if success:
            data = response.json()
            print_result("Get usage stats", True)
            print(f"\n   Period: {data['period']}")
            print(f"   Issues analyzed: {data['issue_analyses']}/{data['issue_limit']}")
            print(f"   Sprints analyzed: {data['sprint_analyses']}/{data['sprint_limit']}")
            print(f"   Portfolios analyzed: {data['portfolio_analyses']}/{data['portfolio_limit']}")
        else:
            print_result("Get usage stats", False, response.json())
        return success
    except Exception as e:
        print_result("Get usage stats", False, {"detail": str(e)})
        return False

def test_analyze_issue():
    """Test issue analysis"""
    print_section("5. Testing Issue Analysis")
    
    if not TENANT_ID:
        print("❌ No tenant ID available")
        return False
    
    issue_key = input("\nEnter a Jira issue key to analyze (e.g., ENG-123): ").strip()
    
    if not issue_key:
        print("❌ No issue key provided")
        return False
    
    payload = {
        "issue_key": issue_key,
        "template": "executive",
        "store_history": True
    }
    
    headers = {
        "X-Tenant-ID": TENANT_ID
    }
    
    try:
        print(f"\n⏳ Analyzing {issue_key}...")
        response = requests.post(
            f"{BASE_URL}/api/analyze/issue",
            json=payload,
            headers=headers,
            timeout=60  # Analysis can take time
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result("Analyze issue", True)
            print(f"\n   Issue: {data['issue_key']}")
            print(f"   Risk Score: {data['risk_score']}/100")
            print(f"   Daily Cost: ${data['daily_cost']:,.0f}")
            print(f"   Blockers: {data['blocker_count']}")
            print(f"\n   Executive Summary:")
            print("   " + "\n   ".join(data['report'].split('\n')[:10]))
            return True
        else:
            print_result("Analyze issue", False, response.json())
            return False
            
    except Exception as e:
        print_result("Analyze issue", False, {"detail": str(e)})
        return False

def test_analyze_raw():
    """Test raw analysis endpoint"""
    print_section("6. Testing Raw Analysis API")
    
    if not TENANT_ID:
        print("❌ No tenant ID available")
        return False
    
    issue_key = input("\nEnter a Jira issue key for raw analysis (or press Enter to skip): ").strip()
    
    if not issue_key:
        print("⏭️  Skipped")
        return True
    
    headers = {
        "X-Tenant-ID": TENANT_ID
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/analyze/issue/{issue_key}/raw",
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result("Raw analysis", True)
            print(f"\n   Issue: {data['issue_key']}")
            print(f"   Project: {data['project_key']}")
            print(f"   Risk: {data['risk_score']}")
            print(f"   Sentiment: {data['sentiment']['negative_pct']:.1f}% negative")
            print(f"   Timeline: {data['timeline']['age_days']} days old")
            return True
        else:
            print_result("Raw analysis", False, response.json())
            return False
            
    except Exception as e:
        print_result("Raw analysis", False, {"detail": str(e)})
        return False

def main():
    """Run all tests"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                     FlowIQ Local Testing Suite                            ║
║                         Week 1 Verification                                ║
╚════════════════════════════════════════════════════════════════════════════╝
""")
    
    print(f"Testing API at: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health()))
    
    if results[-1][1]:  # Only continue if health check passed
        results.append(("Create Tenant", test_create_tenant()))
        
        if results[-1][1]:  # Only continue if tenant created
            results.append(("Get Tenant", test_get_tenant()))
            results.append(("Usage Stats", test_usage_stats()))
            results.append(("Analyze Issue", test_analyze_issue()))
            results.append(("Raw Analysis", test_analyze_raw()))
    
    # Summary
    print_section("Test Summary")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! FlowIQ is ready for production.")
        print(f"\n💡 Your Tenant ID: {TENANT_ID}")
        print("   Save this - you'll need it for all API calls.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
