from tortoise import Model, fields


class User(Model):
    id: str = fields.IntField(primary_key=True)
    name: str = fields.CharField(127)
