class ArizonaException(Exception):
    pass


class IncorrectLoginData(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

    def __str__(self) -> str:
        return "Вы ввели неверные cookie!"


class ThisIsYouError(ArizonaException):
    def __init__(self, user_id):
        self.user_id = user_id

    def __str__(self) -> str:
        return f"Вы не можете совершить данное действие самому себе\nID пользователя: {self.user_id}"


class IncorrectProxyData(ArizonaException):
    def __init__(self, proxy: str, reason: str = "") -> None:
        self.proxy = proxy
        self.reason = reason

    def __str__(self) -> str:
        base = f"Не удалось создать прокси из строки: {self.proxy}"
        if self.reason:
            base += f"\nПричина: {self.reason}"
        return base