#!/usr/bin/env python3

# Imports
import os
import time
from transmission_rpc import Client
from prometheus_client import start_http_server, Gauge, REGISTRY, PROCESS_COLLECTOR, PLATFORM_COLLECTOR, GC_COLLECTOR

# Number of seconds between 2 metrics collection
COLLECT_INTERVAL = os.getenv('EXPORTER_COLLECT_INTERVAL', 30)
# Prefix for all metrics
METRIC_NAMESPACE = os.getenv('METRIC_NAMESPACE', 'transmission')

# Get Transmission information from env
TRANSMISSION_HOST = os.getenv('TRANSMISSION_HOST', 'localhost')
TRANSMISSION_PORT = os.getenv('TRANSMISSION_PORT', 9091)
TRANSMISSION_USERNAME = os.getenv('TRANSMISSION_USERNAME')
TRANSMISSION_PASSWORD = os.getenv('TRANSMISSION_PASSWORD')

# Remove unwanted Prometheus metrics
REGISTRY.unregister(GC_COLLECTOR)
REGISTRY.unregister(PLATFORM_COLLECTOR)
REGISTRY.unregister(PROCESS_COLLECTOR)

# Start Prometheus exporter server
start_http_server(8000)


#########################################
##### Initialize Prometheus metrics #####
#########################################

# Speeds gauges
download_speed_gauge = Gauge(f'{METRIC_NAMESPACE}_session_stats_download_speed_bytes', 'Current download speed in bytes')
upload_speed_gauge = Gauge(f'{METRIC_NAMESPACE}_session_stats_upload_speed_bytes', 'Current upload speed in bytes')

# Speed limit gauges
speed_limit_down_gauge = Gauge(f'{METRIC_NAMESPACE}_speed_limit_down_bytes', 'Max global download speed', ["enabled"])
speed_limit_up_gauge = Gauge(f'{METRIC_NAMESPACE}_speed_limit_up_bytes', 'Max global upload speed', ["enabled"])
alt_speed_limit_down_gauge = Gauge(f'{METRIC_NAMESPACE}_alt_speed_down', 'Alternative max global download speed', ["enabled"])
alt_speed_limit_up_gauge = Gauge(f'{METRIC_NAMESPACE}_alt_speed_up', 'Alternative max global upload speed', ["enabled"])

# Torrents count gauges
session_stats_torrents_active_gauge = Gauge(f'{METRIC_NAMESPACE}_session_stats_torrents_active', 'The number of active torrents')
session_stats_torrents_paused_gauge = Gauge(f'{METRIC_NAMESPACE}_session_stats_torrents_paused', 'The number of paused torrents')
session_stats_torrents_total_gauge = Gauge(f'{METRIC_NAMESPACE}_session_stats_torrents_total', 'The total number of torrents')

# Queue gauges
down_queue_size_gauge = Gauge(f'{METRIC_NAMESPACE}_down_queue_size', 'Max number of torrents to download at once', ["enabled"])
up_queue_size_gauge = Gauge(f'{METRIC_NAMESPACE}_up_queue_size', 'Max number of torrents to upload at once', ["enabled"])

# Volume gauges
session_stats_downloaded_bytes_gauge = Gauge(f'{METRIC_NAMESPACE}_session_stats_downloaded_bytes', 'The number of downloaded bytes', ['type'])
session_stats_uploaded_bytes_gauge = Gauge(f'{METRIC_NAMESPACE}_session_stats_uploaded_bytes', 'The number of uploaded bytes', ['type'])

# Peer limit gauges
global_peer_limit_gauge = Gauge(f'{METRIC_NAMESPACE}_global_peer_limit', 'Maximum global number of peers')
torrent_peer_limit_gauge = Gauge(f'{METRIC_NAMESPACE}_torrent_peer_limit', 'Maximum number of peers for a single torrent')

# Transmission gauges
session_stats_sessions_gauge = Gauge(f'{METRIC_NAMESPACE}_session_stats_sessions', 'Count of the times transmission started', ['type'])
session_stats_active_gauge = Gauge(f'{METRIC_NAMESPACE}_session_stats_active', 'The time transmission is active since', ['type'])

# Misc
seed_ratio_limit_gauge = Gauge(f'{METRIC_NAMESPACE}_seed_ratio_limit', 'The default seed ratio for torrents to use', ["enabled"])
cache_size_bytes_gauge = Gauge(f'{METRIC_NAMESPACE}_cache_size_bytes', 'Maximum size of the disk cache')
session_stats_files_added_gauge = Gauge(f'{METRIC_NAMESPACE}_session_stats_files_added', 'The number of files added', ['type'])


def transmission_connect():
    """
    Connect to Transmission
    """
    if TRANSMISSION_USERNAME is not None and TRANSMISSION_PASSWORD is not None:
        client = Client(host=TRANSMISSION_HOST, port=TRANSMISSION_PORT, username=TRANSMISSION_USERNAME, password=TRANSMISSION_PASSWORD)
    else:
        client = Client(host=TRANSMISSION_HOST, port=TRANSMISSION_PORT)

    return client

def refresh_metrics(client):
    """
    Refresh all Prometheus metrics from Transmission
    """

    # Get session and session stats
    session = client.get_session()
    stats = client.session_stats()

    # Refresh regular gauges
    download_speed_gauge.set(stats.download_speed)
    upload_speed_gauge.set(stats.upload_speed)
    session_stats_torrents_active_gauge.set(stats.active_torrent_count)
    session_stats_torrents_paused_gauge.set(stats.paused_torrent_count)
    session_stats_torrents_total_gauge.set(stats.torrent_count)
    cache_size_bytes_gauge.set(session.cache_size_mb*1000*1000)
    global_peer_limit_gauge.set(session.peer_limit_global)
    torrent_peer_limit_gauge.set(session.peer_limit_per_torrent)

    # Refresh session stats
    session_stats_active_gauge.labels(type="cumulative").set(stats.cumulative_stats.seconds_active)
    session_stats_active_gauge.labels(type="current").set(stats.current_stats.seconds_active)

    session_stats_downloaded_bytes_gauge.labels(type="cumulative").set(stats.cumulative_stats.downloaded_bytes)
    session_stats_downloaded_bytes_gauge.labels(type="current").set(stats.current_stats.downloaded_bytes)

    session_stats_uploaded_bytes_gauge.labels(type="cumulative").set(stats.cumulative_stats.uploaded_bytes)
    session_stats_uploaded_bytes_gauge.labels(type="current").set(stats.current_stats.uploaded_bytes)

    session_stats_files_added_gauge.labels(type="cumulative").set(stats.cumulative_stats.files_added)
    session_stats_files_added_gauge.labels(type="current").set(stats.current_stats.files_added)

    session_stats_sessions_gauge.labels(type="cumulative").set(stats.cumulative_stats.session_count)
    session_stats_sessions_gauge.labels(type="current").set(stats.current_stats.session_count)

    # Refresh conditionnaly enable speed limits, queue size and ratio
    if session.speed_limit_down_enabled:
        speed_limit_down_gauge.clear()
        speed_limit_down_gauge.labels(enabled="1").set(session.speed_limit_down*1000)
    else:
        speed_limit_down_gauge.clear()
        speed_limit_down_gauge.labels(enabled="0").set(session.speed_limit_down*1000)

    if session.speed_limit_up_enabled:
        speed_limit_up_gauge.clear()
        speed_limit_up_gauge.labels(enabled="1").set(session.speed_limit_up*1000)
    else:
        speed_limit_up_gauge.clear()
        speed_limit_up_gauge.labels(enabled="0").set(session.speed_limit_up*1000)

    if session.alt_speed_time_enabled:
        alt_speed_limit_down_gauge.clear()
        alt_speed_limit_up_gauge.clear()
        alt_speed_limit_down_gauge.labels(enabled="1").set(session.alt_speed_down*1000)
        alt_speed_limit_up_gauge.labels(enabled="1").set(session.alt_speed_up*1000)
    else:
        alt_speed_limit_down_gauge.clear()
        alt_speed_limit_up_gauge.clear()
        alt_speed_limit_down_gauge.labels(enabled="0").set(session.alt_speed_down*1000)
        alt_speed_limit_up_gauge.labels(enabled="0").set(session.alt_speed_up*1000)

    if session.seed_ratio_limited:
        seed_ratio_limit_gauge.clear()
        seed_ratio_limit_gauge.labels(enabled="1").set(session.seed_ratio_limit)
    else:
        seed_ratio_limit_gauge.clear()
        seed_ratio_limit_gauge.labels(enabled="0").set(session.seed_ratio_limit)

    if session.download_queue_enabled:
        down_queue_size_gauge.clear()
        down_queue_size_gauge.labels(enabled="1").set(session.download_queue_size)
    else:
        down_queue_size_gauge.clear()
        down_queue_size_gauge.labels(enabled="0").set(session.download_queue_size)

    if session.seed_queue_enabled:
        up_queue_size_gauge.clear()
        up_queue_size_gauge.labels(enabled="1").set(session.seed_queue_size)
    else:
        up_queue_size_gauge.clear()
        up_queue_size_gauge.labels(enabled="0").set(session.seed_queue_size)

# Connect
client = transmission_connect()

# Loop forever
while True:
    refresh_metrics(client)
    # Wait before next metrics collection
    time.sleep(COLLECT_INTERVAL)
