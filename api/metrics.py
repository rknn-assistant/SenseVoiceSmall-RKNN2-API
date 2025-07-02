from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter('sensevoice_requests_total', 'Total requests', ['endpoint', 'method'])
REQUEST_LATENCY = Histogram('sensevoice_request_duration_seconds', 'Request latency', ['endpoint'])
TRANSCRIPTION_DURATION = Histogram('sensevoice_transcription_duration_seconds', 'Transcription processing time')
AUDIO_DURATION = Histogram('sensevoice_audio_duration_seconds', 'Audio duration processed')
ACTIVE_REQUESTS = Gauge('sensevoice_active_requests', 'Number of active requests')
MODEL_LOAD_TIME = Histogram('sensevoice_model_load_time_seconds', 'Model loading time') 