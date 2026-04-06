# Use your exact Python version
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy your files into the server
COPY . /app

# Install your libraries
RUN pip install --no-cache-dir -r requirements.txt

# Google Cloud Run defaults to port 8080
EXPOSE 8080

# The command to start your dashboard
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]