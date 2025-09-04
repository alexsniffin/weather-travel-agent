# Weather Travel Agent

A generative AI Agent that provides travel recommendations and weather forecast along a route.

## Features

- [A2A interface](https://a2aprotocol.ai/docs/) for agentic interoperability
  - Get a route from Google API for a single origin and destination
  - Get weather forecasts using OpenWeather at points along the route
  - Receive travel recommendations based on weather conditions
- Gradio UI with Google Map integration for demos

### Demo

See a demo [here](./demo/) for more details on how it works.

## Setup with uv

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management.

### Prerequisites

1. Install uv:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/alexsniffin/weather-travel-agent.git
   cd weather-travel-agent
   ```

2. Install dependencies with uv:
   ```bash
   make install
   ```

3. (Optional) Install development dependencies:
   ```bash
   make install-dev
   ```

### Usage

Run the application:
```bash
make run
```

## Development

### Running tests
```bash
make test
```

### Code formatting
```bash
make format
```

### Linting
```bash
make lint
```

## Environment Variables

Create a `.env` file in the project root using the `.env.example`.
