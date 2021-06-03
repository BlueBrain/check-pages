# Start with a default ubuntu image
FROM python:3.8-buster

RUN apt-get update
RUN apt-get install -y unzip curl software-properties-common  vim git  


# Install google-chrome and the chomedriver
RUN curl https://dl-ssl.google.com/linux/linux_signing_key.pub -o /tmp/google.pub
RUN cat /tmp/google.pub | apt-key add -
RUN rm /tmp/google.pub
RUN echo 'deb http://dl.google.com/linux/chrome/deb/ stable main' > /etc/apt/sources.list.d/google.list
RUN mkdir -p /usr/share/desktop-directories
RUN apt-get -y update && apt-get install -y google-chrome-stable
RUN dpkg-divert --add --rename --divert /opt/google/chrome/google-chrome.real /opt/google/chrome/google-chrome
RUN echo "#!/bin/bash\nexec /opt/google/chrome/google-chrome.real --no-sandbox --disable-setuid-sandbox \"\$@\"" > /opt/google/chrome/google-chrome
RUN chmod 755 /opt/google/chrome/google-chrome


RUN google-chrome --version
