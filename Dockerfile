FROM python:alpine

# Set the working directory
WORKDIR /archiver

RUN apk add --no-cache git

# Copy the current directory contents into the container at /archiver
COPY requirements.txt /archiver

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /archiver
COPY . /archiver

# Run app.py when the container launches
CMD ["python", "-u", "main.py"]