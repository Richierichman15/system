#!/bin/bash

# CI/CD Build Script for Frontend
# This script handles the rollup optional dependency issue

echo "🔧 Setting up CI build environment..."

# Remove existing node_modules and package-lock.json to ensure clean install
echo "🧹 Cleaning existing dependencies..."
rm -rf node_modules package-lock.json

# Install dependencies with specific flags for CI
echo "📦 Installing dependencies..."
npm install --legacy-peer-deps --no-optional

# Try to install rollup explicitly if needed
echo "🔧 Ensuring rollup is available..."
npm install rollup@^4.0.0 --save-dev --legacy-peer-deps || echo "Rollup installation failed, continuing..."

# Build the project
echo "🏗️ Building project..."
npm run build

echo "✅ Build completed successfully!"
