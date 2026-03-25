# Practical Python Code Adventure

**Live at:** [https://adventure.practicalpython.org](https://adventure.practicalpython.org)

**Code Adventure** is a series of 10 interactive coding challenges (each with two parts), inspired by [Advent of Code](https://adventofcode.com/). Built with Flask, PostgreSQL, and Docker, the app is designed for members of the Practical Python Discord community. Solving both parts of a challenge grants access to a private discussion thread where participants can share their solutions and strategies.

The project is containerized and deployed on an AWS EC2 instance.

---

## Features

- **Interactive Challenges** – Solve progressively difficult problems across 10 themed challenges.
- **Two-Part Format** – Each challenge has two parts to deepen engagement and difficulty.
- **Discord Integration** – Authenticate with Discord and unlock private solution threads.
- **Progress Tracking** – See which challenges you've completed and continue where you left off.
- **Challenge Obfuscation** – IDs are masked to encourage creative problem-solving.
- **Admin Dashboard** – Browser-based interface for editing challenge data and managing users.
- **PostgreSQL Backend** – All data is stored and managed using a relational schema.

---

## Tech Stack

- Python 3.x
- Flask
- PostgreSQL
- SQLAlchemy
- Docker / Docker Compose
- Discord OAuth2

---

## Getting Started

### Prerequisites

- Python 3.x (for local development)
- Docker + Docker Compose
- PostgreSQL (via Docker or local install)

---

### Environment Variables

Create a `.env` file in the project root with the following contents:

```ini
# PostgreSQL
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="postgres"
POSTGRES_SERVER="db"         # Docker container name
POSTGRES_PORT="5432"
DATABASE_NAME="zorak"

# SQLAlchemy
SECRET_KEY="Something_secret_goes_here"

# Discord OAuth
DISCORD_ADMIN_USER_ID='ABCDE'
DISCORD_REDIRECT_URI="http://127.0.0.1:5002/callback"
CLIENT_ID='your_discord_client_id'
CLIENT_SECRET='your_discord_client_secret'
BOT_TOKEN='your_discord_bot_token'
```

The application internally constructs the database URL from these values:

```
postgresql://<POSTGRES_USER>:<POSTGRES_PASSWORD>@<POSTGRES_SERVER>:<POSTGRES_PORT>/<DATABASE_NAME>
```

---

## Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/JefeThePug/Practical-Python-Code-Adventure.git
   cd Practical-Python-Code-Adventure
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Ensure PostgreSQL is running**, and that your `.env` file matches the database configuration.

4. **Start the application**:
   ```bash
   python app.py
   ```

5. **Access the app**:
   Open your browser and visit: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Running with Docker

1. **Build and start the containers**:
   ```bash
   docker-compose up --build
   ```

2. **Visit the app**:
   Once running, go to: [http://localhost:5000](http://localhost:5000)

> The `db` hostname is used internally by the Flask app to connect to the PostgreSQL container, as defined by `POSTGRES_SERVER=db` in your `.env`.

---

## Usage

- **Login**: Users can log in using their Discord accounts, which allows the application to track their progress.
- **Challenges**: Navigate to the challenges through the main page. Each challenge will have two parts that can be solved independently.
- **Submit Solutions**: Users can submit their answers for each part of a challenge. Correct answers will update their progress and grant access to the discussion channel.
- **Collaborate**: Share and discuss solutions with others in the Discord server.

---

## Code Overview

### `app.py`

- Handles Flask routes for login, challenges, and admin tools.
- Uses SQLAlchemy for database interaction.
- Implements OAuth2 with Discord for authentication and role management.

### `models.py` 
- Defines the database schema using SQLAlchemy ORM. Models include:
  - `DiscordID`, `MainEntry`, `SubEntry`, `Progress`, `Solution`, `Obfuscation`, `Permissions`, and `Release`.

### `cache.py`
- Implements the `DataCache` class. This module loads and stores frequently accessed data (e.g., HTML content, permissions, obfuscations, and progress) into memory, reducing redundant database queries and improving runtime performance.

### `setup.py`
- Handles initial project setup, such as creating the database schema and optionally prepopulating data for development or testing. Run this file once before launching the app to ensure your environment is ready.

### `ending.js`

- Controls celebratory animations (confetti) triggered after completing challenges.

---

## License

This project is open-source and intended for educational and community-building use.

---

## Acknowledgments

- Inspired by [Advent of Code](https://adventofcode.com)
- Built for the [Practical Python Discord](https://github.com/practical-python-org)
