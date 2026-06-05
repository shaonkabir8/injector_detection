Dashboard should be live ops center. Show:

source health
camera/stream status
detection events
validation state
audit trail
model quality trends
Monitor all:

stream FPS, latency, bitrate
queue depth, retries, failures
model confidence, false positives, false negatives
infra GPU/CPU/RAM/disk
Audit:

log every detection event
log every validation request/response
store input/prediction/correction/outcome
make audit data queryable
Train:

auto dataset builder from validated events
nightly fine-tune jobs
versioned model updates
keep metadata for source, label, confidence
Test realtime:

run live frame sample through full pipeline
compare result vs expected
alert drift when metrics fall
surface realtime test status on dashboard