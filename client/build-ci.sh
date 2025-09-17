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

# Build the project
echo "🏗️ Building project..."
npm run build

echo "✅ Build completed successfully!"
