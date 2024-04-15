# Use the small Python Alpine image as the base
FROM python:3.12.2-alpine3.19

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Disable pip version check
ENV PIP_DISABLE_PIP_VERSION_CHECK 1


# Install Gunicorn
RUN pip --no-cache-dir install gunicorn

# Set the working directory in the container
WORKDIR /IFPS

# Install dependencies
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /IFPS
COPY . .

# Make sure DEBUG is False
RUN sed -i 's/DEBUG=True/DEBUG=False/' .env

# Run Django migrations and collect static files
RUN python manage.py migrate
RUN python manage.py collectstatic --noinput

# Expose the port on which your Django app will run
EXPOSE 8000

# Define the command to run your Django app
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
