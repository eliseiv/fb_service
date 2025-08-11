# SeleniumBase Docker Image using a Virtual Environment
FROM ubuntu:22.04
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8

#-------------------------------------
# Install system dependencies, locale, fonts, and utilities
#-------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      tzdata locales \
      fonts-liberation fonts-liberation2 fonts-font-awesome fonts-ubuntu fonts-terminus fonts-powerline fonts-open-sans fonts-mononoki fonts-roboto fonts-lato \
      libpq-dev libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 libnss3 libu2f-udev libvulkan1 libwayland-client0 libxcomposite1 libxdamage1 libxfixes3 libxkbcommon0 libxrandr2 \
      xdg-utils ca-certificates \
      curl sudo unzip vim wget xvfb gcc gnupg2 \
      python3 python3-pip python3-setuptools python3-dev python3-tk python3-venv && \
    rm -rf /var/lib/apt/lists/*

#-------------------------------------
# Configure timezone and locale
#-------------------------------------
RUN ln -snf /usr/share/zoneinfo/America/New_York /etc/localtime && \
    echo "America/New_York" > /etc/timezone && \
    sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen en_US.UTF-8 && \
    update-locale LANG=en_US.UTF-8

#-------------------------------------
# Install Google Chrome
#-------------------------------------
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get update && \
    apt-get install -y --no-install-recommends ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb && \
    rm -rf /var/lib/apt/lists/*

#-------------------------------------
# Create non-root user and working directory
#-------------------------------------
RUN useradd -ms /bin/bash seleniumuser && \
    mkdir -p /home/seleniumuser/workdir && \
    chown -R seleniumuser:seleniumuser /home/seleniumuser/workdir

# Switch to non-root user and set working directory
USER seleniumuser
WORKDIR /home/seleniumuser/workdir

#-------------------------------------
# Create a virtual environment and update PATH
#-------------------------------------
RUN python3 -m venv venv
ENV PATH="/home/seleniumuser/workdir/venv/bin:$PATH"

#-------------------------------------
# Copy the requirements file and install Python packages in the virtual environment
#-------------------------------------
COPY --chown=seleniumuser:seleniumuser r.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

#-------------------------------------
# Download chromedriver using SeleniumBase (chromedriver is saved in SeleniumBase's default driver directory)
#-------------------------------------
RUN seleniumbase get chromedriver

#-------------------------------------
# Copy application files and create a logs directory
#-------------------------------------
COPY --chown=seleniumuser:seleniumuser main.py .
COPY --chown=seleniumuser:seleniumuser manage.py .
COPY --chown=seleniumuser:seleniumuser update_proto_files.py .
COPY --chown=seleniumuser:seleniumuser .env .
COPY --chown=seleniumuser:seleniumuser ./app ./app
COPY --chown=seleniumuser:seleniumuser ./logs ./logs

