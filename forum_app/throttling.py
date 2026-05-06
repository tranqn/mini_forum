from rest_framework.throttling import ScopedRateThrottle


class PostThrottle(ScopedRateThrottle):
    scope = 'posts'
