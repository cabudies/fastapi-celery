# Use the official Ubuntu base image
FROM ubuntu:latest

# Set non-interactive mode
ENV DEBIAN_FRONTEND=noninteractive

# Update and install necessary packages
RUN apt-get update -y && \
    apt-get install -y \
    wget \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    libnss3 \
    libfontconfig1 \
    libxrender1

ENV CHROME_VERSION=114.0.5735.198-1
RUN wget --no-check-certificate https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_${CHROME_VERSION}_amd64.deb
RUN dpkg -i google-chrome-stable_${CHROME_VERSION}_amd64.deb || apt -y -f install
RUN rm google-chrome-stable_${CHROME_VERSION}_amd64.deb;

RUN echo $(google-chrome --version)

RUN echo $(wget -qO - https://chromedriver.storage.googleapis.com/LATEST_RELEASE)

RUN wget -q "https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip" && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/ && \
    rm chromedriver_linux64.zip

# Install Selenium Python library
RUN apt-get install -y python3-pip && \
    pip3 install selenium

# Clean up
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set display environment variable
ENV DISPLAY=:99

# Define a working directory
WORKDIR /usr/src/app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Copy the rest of your application's code into the container
COPY . .
