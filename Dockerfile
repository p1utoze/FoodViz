FROM ubuntu:22.04
LABEL authors="p1utoze"

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-setuptools \
    python3-venv \
    git \
    && apt-get clean

WORKDIR /app

# Install python packages
COPY requirements.txt /app/requirements.txt
RUN #python3 -m pip install torch --index-url https://download.pytorch.org/whl/cpu
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt

# Copy the Entry Point script
COPY app.py /app/app.py

COPY pages/ /app/pages
COPY data/ /app/data/
COPY .streamlit /app/.streamlit
COPY src/ /app/src

# Expose the port
EXPOSE 8501

# Command to run on container start
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
