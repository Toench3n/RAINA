# Retrieved from https://rasa.com/docs/rasa/how-to-deploy
# Extend the official Rasa SDK image
FROM rasa/rasa-sdk:2.8.2

# Use subdirectory as working directory
WORKDIR /app

# Copy any additional custom requirements, if necessary (uncomment next line)
COPY actions/requirements.txt ./

# Change back to root user to install dependencies
USER root

# Install extra requirements for actions code, if necessary (uncomment next line)
RUN pip install -r requirements.txt

# Copy actions folder to working directory
COPY ./actions /app/actions

# Make backlog folder accessible
RUN chmod 777 /app/actions/custom/images/backlog

# Create mount point for database
VOLUME /app/actions/db

# By best practices, don't run the code with root user
USER 1001