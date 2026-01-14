# Use the official Playwright image which includes Python and necessary browser binaries
# Using jammy (Ubuntu 22.04) as base
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5001 \
    HOST=0.0.0.0 \
    PYTHONPATH=/app/backend

# Set the working directory in the container
WORKDIR /app

# Copy the backend requirements file first to leverage Docker cache
COPY backend/requirements.txt backend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Install Playwright browsers (chromium is usually sufficient for this app)
# The base image has them, but this ensures the python package is linked correctly
RUN playwright install chromium

# Copy the backend code
COPY backend/ backend/

# Copy the frontend and other root files
COPY index.html .
COPY css/ css/
COPY js/ js/
COPY template.xlsx .

# Copy assets if they exist (handling potentially missing directories gracefully in copy is tricky, 
# but COPY instruction works if source exists. Given the file list, assets/ exists.)
COPY assets/ assets/

# Create necessary directories for runtime
RUN mkdir -p logs temp/maps output

# Expose the port
EXPOSE 5001

# Command to run the application
CMD ["python", "backend/main.py"]
