from rest_framework.throttling import ScopedRateThrottle


class PostThrottle(ScopedRateThrottle):
    scope = 'posts'

    def allow_request(self, request, view):
        if request.method != 'POST':
            return True
        return super().allow_request(request, view)
