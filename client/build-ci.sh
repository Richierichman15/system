#!/bin/bash

# CI/CD Build Script for Frontend
# This script handles the rollup optional dependency issue

echo "🔧 Setting up CI build environment..."

# Remove existing node_modules and package-lock.json to ensure clean install
echo "🧹 Cleaning existing dependencies..."
rm -rf node_modules package-lock.json

# Install dependencies with specific flags for CI
echo "📦 Installing dependencies..."
npm install --no-optional --legacy-peer-deps

# If rollup is still missing, install it explicitly
if ! npm list rollup > /dev/null 2>&1; then
    echo "🔧 Installing rollup explicitly..."
    npm install rollup@^4.0.0 --save-dev
fi

# Build the project
echo "🏗️ Building project..."
npm run build

echo "✅ Build completed successfully!"
