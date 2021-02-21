from django.db import models


class TestKid(models.Model):
    """
    Model class Kid of family app
    """
    happy = models.BooleanField()
    name = models.CharField(max_length=30)
    age = models.IntegerField()
    bio = models.TextField()
    wanted_games_qtd = models.BigIntegerField()
    birthday = models.DateField(null=True)
    appointment = models.DateTimeField(null=True)
