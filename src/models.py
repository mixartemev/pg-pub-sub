from tortoise import Model, fields


class User(Model):
    email: str = fields.CharField(127, unique=True)
    first_name: str = fields.CharField(127)
    last_name: str | None = fields.CharField(127, null=True)
