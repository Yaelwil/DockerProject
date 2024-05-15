FROM mongo:4.4.0

# Update package index and install required packages
# RUN apt-get update && \
#     apt-get install -y apt-transport-https ca-certificates curl software-properties-common
#
# # Install ngrok
# RUN curl -fsSL -o /usr/local/bin/ngrok https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip && \
#     chmod +x /usr/local/bin/ngrok

# Copy the script into the image
COPY set-replica.sh /usr/local/bin/set-replica.sh
# Make the script executable
RUN chmod +x /usr/local/bin/set-replica.sh

CMD ["/usr/local/bin/set-replica.sh"]
