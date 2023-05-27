# Use a base image with Python pre-installed
FROM python:3.8-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask app code into the container
COPY . .

# Expose the port that the Flask app listens on
EXPOSE 8080

ENTRYPOINT ["python"]

# Set the entrypoint command to run the Flask app
CMD ["app.py"]
