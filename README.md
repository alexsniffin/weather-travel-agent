# Weather Travel Agent

A GenAI Agent that provides weather-based travel recommendations along a route.

## Features

- Get weather forecasts for travel destinations
- Receive personalized travel recommendations based on weather conditions
- [A2A Interface](https://a2aprotocol.ai/docs/)

## Demo

See a demo under [demo](./demo/) for more details on how it works!

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
   git clone <your-repo-url>
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
