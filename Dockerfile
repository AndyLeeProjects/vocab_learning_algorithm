FROM apache/airflow:2.2.0

# Copy DAGs, plugins, and other necessary files
COPY dags/ /opt/airflow/dags/
COPY plugins/ /opt/airflow/plugins/
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Airflow ports
EXPOSE 8000 5555 8793

# Start Airflow webserver and scheduler
CMD ["airflow", "webserver", "--port", "8000"]
