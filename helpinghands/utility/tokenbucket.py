import time


class TokenBucket:
    def __init__(self, tokens, fill_rate, activated=True):
        """tokens is the total amount of tokens in the bucket. fill_rate is the
        rate in tokens/second that the bucket will be refilled."""
        self.capacity = float(tokens)
        self._tokens = float(tokens)
        self.fill_rate = float(fill_rate)
        self.timestamp = time.monotonic()
        self.activated = activated

    def consume(self, tokens):
        """Consume tokens from the bucket. Returns 0 if there were sufficient
        tokens, otherwise the expected time until enough tokens become available."""
        if not self.activated:
            return 0
        if tokens <= self._tokens:
            self._tokens -= tokens
            return 0
        else:
            deficit = tokens - self._tokens
            wait = deficit / self.fill_rate
            return wait

    def refill(self):
        """Refill tokens in the bucket based on fill_rate. Called automatically during consume."""
        now = time.monotonic()
        delta = now - self.timestamp
        self._tokens = min(self.capacity, self._tokens + self.fill_rate * delta)
        self.timestamp = now


def api_rate_limit_wait(bucket):
    wait_time = bucket.consume(1)  # Consume 1 token for API REQUEST
    if wait_time > 0:
        return wait_time
    else:
        return 0
