#!/bin/bash

echo "Starting R Language Assistant..."

echo ""
echo "Checking Python..."
python3 --version
if [ $? -ne 0 ]; then
    echo "Python 3 is not installed or not in PATH"
    exit 1
fi

echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt

echo ""
echo "Setting up database..."
cd r_assistant
python3 manage.py makemigrations
python3 manage.py migrate

echo ""
read -p "Do you want to create a superuser? (y/N): " create_superuser
if [[ $create_superuser =~ ^[Yy]$ ]]; then
    python3 manage.py createsuperuser
fi

echo ""
echo "Starting development server..."
echo "Open http://127.0.0.1:8000 in your browser"
echo "Press Ctrl+C to stop the server"
python3 manage.py runserver