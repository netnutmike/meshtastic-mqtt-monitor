#!/bin/bash
# Test script to verify package installation from source

echo "Testing Meshtastic MQTT Monitor installation..."
echo

# Test 1: Build wheel
echo "1. Building wheel package..."
python3 -m build --wheel --outdir /tmp 2>&1 | grep -E "(Successfully|error)"
if [ $? -eq 0 ]; then
    echo "✓ Wheel built successfully"
else
    echo "✗ Wheel build failed"
    exit 1
fi
echo

# Test 2: Install from wheel
echo "2. Installing from wheel..."
python3 -m pip install /tmp/meshtastic_mqtt_monitor-0.1.0-py3-none-any.whl --force-reinstall --quiet
if [ $? -eq 0 ]; then
    echo "✓ Package installed successfully"
else
    echo "✗ Package installation failed"
    exit 1
fi
echo

# Test 3: Verify command-line script
echo "3. Testing command-line script..."
meshtastic-monitor --version
if [ $? -eq 0 ]; then
    echo "✓ Command-line script works"
else
    echo "✗ Command-line script failed"
    exit 1
fi
echo

# Test 4: Test help output
echo "4. Testing help output..."
meshtastic-monitor --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Help output works"
else
    echo "✗ Help output failed"
    exit 1
fi
echo

echo "All installation tests passed!"
