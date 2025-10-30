# Getting Started

This document provides instructions on how to set up and run the CARLA Foundations project.

## Prerequisites

- Python 3.10 or 3.11
- Node.js and npm
- CARLA Simulator (please refer to the official CARLA documentation for installation instructions)

## Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/carla-foundations.git
    cd carla-foundations
    ```

2.  **Install Python dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Node.js dependencies:**

    ```bash
    cd web
    npm install
    cd ..
    ```

4.  **Set up pre-commit hooks:**

    ```bash
    pre-commit install
    ```

## Running the application

1.  **Start the CARLA Simulator.**

2.  **Run the Flask API:**

    ```bash
    python -m api.app
    ```

3.  **Run the React UI:**

    ```bash
    cd web
    npm run dev
    ```

4.  **Run a smoke test:**

    ```bash
    python -m orchestration.runner smoke
    ```

5.  **Check the health of the CARLA server:**

    ```bash
    python -m orchestration.runner health
    ```
