from fastapi import HTTPException, status

class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class AuthError(HTTPException):
    def __init__(self, detail: str = "Authentication error"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class PermissionDeniedError(HTTPException):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class BadRequestError(HTTPException):
    def __init__(self, detail: str = "Invalid request"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class ConflictError(HTTPException):
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


# Bot Management Specific Exceptions
class BotNotFoundError(NotFoundError):
    def __init__(self, bot_id: str = None):
        detail = f"Bot {bot_id} not found" if bot_id else "Bot not found"
        super().__init__(detail=detail)


class BotScenarioNotFoundError(NotFoundError):
    def __init__(self, scenario_id: str = None):
        detail = f"Bot scenario {scenario_id} not found" if scenario_id else "Bot scenario not found"
        super().__init__(detail=detail)


class DialogStateNotFoundError(NotFoundError):
    def __init__(self, dialog_id: str = None):
        detail = f"Dialog state {dialog_id} not found" if dialog_id else "Dialog state not found"
        super().__init__(detail=detail)


class BotCredentialError(BadRequestError):
    def __init__(self, platform: str = None, detail: str = None):
        if not detail:
            detail = f"Invalid credentials for platform {platform}" if platform else "Invalid bot credentials"
        super().__init__(detail=detail)


class BotOperationError(HTTPException):
    def __init__(self, detail: str = "Bot operation failed", status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)


class WebhookConfigurationError(BadRequestError):
    def __init__(self, detail: str = "Webhook configuration error"):
        super().__init__(detail=detail)