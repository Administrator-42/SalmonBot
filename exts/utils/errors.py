from discord.ext import commands

class NotRegistered(commands.CheckFailure):
    pass

class GlobaldataAlreadyAdded(Exception):
    pass