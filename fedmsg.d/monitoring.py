# Enable the MonitoringProducer.
# Without this, consumers will leak memory.

config = {
    'moksha.monitoring.socket': 'ipc:///var/tmp/moksha-monitor',
    'moksha.monitoring.socket.mode': '777',
}
