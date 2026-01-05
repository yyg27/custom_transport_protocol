#!/bin/bash

echo "=========================================="
echo "Custom Transport & Secure Application Protocol - Test Suite"
echo "=========================================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' #no color

PASSED=0
FAILED=0

run_test() {
    local test_name=$1
    local command=$2
    
    echo -n "Testing $test_name... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
    fi
}

echo "1. Testing Transport Layer Modules"
echo "-----------------------------------"
run_test "Header module" "python -m transport.header"
run_test "Checksum module" "python -m transport.checksum"
echo ""

echo "2. Testing Application Layer Modules"
echo "-------------------------------------"
run_test "Messages module" "python -m application.messages"
run_test "Encryption module" "python -m application.encryption"
run_test "Protocol module" "python -m application.protocol"
echo ""

echo "3. Import Tests"
echo "---------------"
run_test "Import transport" "python -c 'import transport'"
run_test "Import application" "python -c 'import application'"
run_test "Import config" "python -c 'import config'"
echo ""

echo "=========================================="
echo "Test Results"
echo "=========================================="
echo -e "Passed: ${GREEN}${PASSED}${NC}"
echo -e "Failed: ${RED}${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    echo ""
    echo "You can now run:"
    echo "  Terminal 1: python server.py --mode default"
    echo "  Terminal 2: python client.py --mode default"
else
    echo -e "${RED}Some tests failed. Please check the errors.${NC}"
    exit 1
fi