from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        print(f"[DEBUG] JWT header: {header}")
        if header is None:
            print("[DEBUG] No Authorization header found.")
            return None
        raw_token = self.get_raw_token(header)
        print(f"[DEBUG] Raw token: {raw_token}")
        if raw_token is None:
            print("[DEBUG] No raw token found in header.")
            return None
        try:
            validated_token = self.get_validated_token(raw_token)
            print(f"[DEBUG] Validated token: {validated_token}")
        except Exception as e:
            print(f"[DEBUG] Token validation error: {e}")
            raise
        # Check if token is a refresh token (by inspecting claims)
        if validated_token.get('token_type', None) == 'refresh':
            print("[DEBUG] Refresh token used in Authorization header.")
            raise AuthenticationFailed({
                "detail": "Refresh token used in Authorization header. Use access token instead.",
                "code": "refresh_token_in_auth_header"
            })
        return self.get_user(validated_token), validated_token
