# Algorithmic Trading Framework

This repository contains a Python-based framework for developing and running algorithmic trading strategies. It is designed to be extensible, allowing for the integration of multiple brokers and strategies.

## Project Structure

The project is organized into the following directories:

-   `brokers/`: Contains the different broker implementations. Each broker is responsible for handling authentication, order placement, and data retrieval for a specific brokerage platform.
    -   `flattrade.py`: An implementation for the Flattrade API.
    -   `base.py`: A base class for all broker implementations.
-   `tests/`: Contains the unit tests for the project.

## Getting Started

### Prerequisites

-   Python 3.10 or higher
-   pip

### Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

To use the Flattrade broker, you need to set the following environment variables with your API credentials:

```
export FLATTRADE_API_KEY="your_api_key"
export FLATTRADE_API_SECRET="your_api_secret"
export FLATTRADE_BROKER_ID="your_broker_id"
```

### Running Tests

To run the tests, execute the following command from the root of the project:

```bash
python3 tests/test_flattrade_auth.py
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue to discuss your ideas.