# A simple Prometheus exporter for Transmission in Python

This project aims at providing a [Prometheus](https://prometheus.io/) exporter for the [Transmission](https://transmissionbt.com/) client.

## Configuration

You can use environment variables when starting the container:

| Variable                    | Value                                                                |
| --------------------------- | -------------------------------------------------------------------- |
| `TRANSMISSION_HOST`         | the hostname where Transmission RPC is running (default `localhost`) |
| `TRANSMISSION_PORT`         | the port where Transmission RPC is listening (default `9091`)        |
| `TRANSMISSION_USERNAME`     | the username to connect to Transmission RPC (optionnal)              |
| `TRANSMISSION_PASSWORD`     | the password to connect to Transmission RPC (optionnal)              |
| `EXPORTER_COLLECT_INTERVAL` | seconds between 2 Transmission scraping (default `30`)               |
| `METRIC_NAMESPACE`          | prefix for metrics name (default `transmission`)                     |

The exporter is listenning on port 8000.
