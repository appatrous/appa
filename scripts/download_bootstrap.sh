#!/bin/bash
#
# Bootstrap 5 Download Script
# Downloads Bootstrap 5.3.0 files for offline use
#

set -e

BOOTSTRAP_VERSION="5.3.0"
STATIC_CSS_DIR="$(dirname "$0")/../static/css"
STATIC_JS_DIR="$(dirname "$0")/../static/js"

echo "Downloading Bootstrap ${BOOTSTRAP_VERSION}..."

# Download CSS
echo "Downloading Bootstrap CSS..."
curl -L -o "${STATIC_CSS_DIR}/bootstrap.min.css" \
    "https://cdn.jsdelivr.net/npm/bootstrap@${BOOTSTRAP_VERSION}/dist/css/bootstrap.min.css"

echo "Downloading Bootstrap CSS Map..."
curl -L -o "${STATIC_CSS_DIR}/bootstrap.min.css.map" \
    "https://cdn.jsdelivr.net/npm/bootstrap@${BOOTSTRAP_VERSION}/dist/css/bootstrap.min.css.map"

# Download JS
echo "Downloading Bootstrap JS Bundle..."
curl -L -o "${STATIC_JS_DIR}/bootstrap.bundle.min.js" \
    "https://cdn.jsdelivr.net/npm/bootstrap@${BOOTSTRAP_VERSION}/dist/js/bootstrap.bundle.min.js"

echo "Downloading Bootstrap JS Map..."
curl -L -o "${STATIC_JS_DIR}/bootstrap.bundle.min.js.map" \
    "https://cdn.jsdelivr.net/npm/bootstrap@${BOOTSTRAP_VERSION}/dist/js/bootstrap.bundle.min.js.map"

echo "✅ Bootstrap ${BOOTSTRAP_VERSION} downloaded successfully!"
echo ""
echo "Files saved to:"
echo "  - ${STATIC_CSS_DIR}/bootstrap.min.css"
echo "  - ${STATIC_JS_DIR}/bootstrap.bundle.min.js"
