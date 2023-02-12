from http import HTTPStatus
from quart import Blueprint, current_app
from quart_schema import validate_request, validate_response
from .login_request import LoginRequest
from .register_user_request import RegisterUserRequest
from .user_response import UserResponse, UserResponseUser
from ..auth import create_access_token, jwt_required, get_jwt_identity
from ..exceptions import UnauthorizedException, NotFoundException

users_blueprint = Blueprint("users", __name__)


@users_blueprint.post(rule="/users")
@validate_request(model_class=RegisterUserRequest)
@validate_response(model_class=UserResponse, status_code=HTTPStatus.CREATED)
async def register_user(data: RegisterUserRequest) -> (UserResponse, int):
    current_app.logger.info(
        f"received register user request {data.user.username} {data.user.email}"
    )

    user = await current_app.users_service.register_user(
        username=data.user.username,
        email=data.user.email,
        password=data.user.password,
    )

    current_app.logger.info(f"user registered! {user}")

    token = create_access_token(user=user)

    return (
        UserResponse(
            UserResponseUser(
                email=user.email,
                token=token,
                username=user.username,
                bio=user.bio,
                image=user.image,
            )
        ),
        HTTPStatus.CREATED,
    )


@users_blueprint.post(rule="/users/login")
@validate_request(model_class=LoginRequest)
@validate_response(model_class=UserResponse)
async def login(data: LoginRequest) -> (UserResponse, int):
    current_app.logger.info(f"received login request {data.user.email}")

    is_correct_password = await current_app.users_service.verify_password_by_email(
        email=data.user.email,
        password=data.user.password,
    )

    if not is_correct_password:
        raise UnauthorizedException(f"incorrect password for email {data.user.email}")

    user = await current_app.users_service.get_user_by_email(email=data.user.email)

    current_app.logger.info(f"login successful! {user}")

    token = create_access_token(user=user)

    return (
        UserResponse(
            UserResponseUser(
                email=user.email,
                token=token,
                username=user.username,
                bio=user.bio,
                image=user.image,
            )
        ),
    )


@users_blueprint.get(rule="/user")
@jwt_required
@validate_response(model_class=UserResponse)
async def get_current_user() -> (UserResponse, int):
    user_id = get_jwt_identity()

    user = await current_app.users_service.get_user_by_id(user_id=user_id)

    if not user:
        raise NotFoundException(f"user_id {user_id} not found")

    token = create_access_token(user=user)

    return (
        UserResponse(
            UserResponseUser(
                email=user.email,
                token=token,
                username=user.username,
                bio=user.bio,
                image=user.image,
            )
        ),
    )
