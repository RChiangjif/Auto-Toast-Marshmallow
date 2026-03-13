FROM arm64v8/debian:bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
 && curl -fsSL https://archive.raspberrypi.com/debian/raspberrypi.gpg.key | gpg --dearmor -o /usr/share/keyrings/raspberrypi.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/raspberrypi.gpg] http://archive.raspberrypi.com/debian/ bookworm main" > /etc/apt/sources.list.d/raspi.list \
 && apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-flask \
    python3-picamera2 \
    python3-pil \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the entire application
COPY app.py /app/
COPY servo.py /app/
COPY toasting_controller.py /app/
COPY core/ /app/core/
COPY hardware/ /app/hardware/
COPY vision/ /app/vision/
COPY web/ /app/web/

EXPOSE 8080

ENV PORT=8080
CMD ["python3", "app.py"]
