import random
import discord
import requests
from discord.ext.commands import bot

from Roxbot import checks
from Roxbot.settings import guild_settings
from Roxbot.logging import log


class Fun:
	def __init__(self, bot_client):
		self.bot = bot_client

	@bot.command()
	async def roll(self, ctx, die):
		"""
		Rolls a die using ndx format.
		Usage:
			{command_prefix}roll ndx
		Example:
			.roll 2d20 # Rolls two D20s
		"""
		dice = 0
		if die[0].isdigit():
			if die[1].isdigit() or die[0] == 0:
				return await ctx.send("I only support multipliers from 1-9")
			multiplier = int(die[0])
		else:
			multiplier = 1
		if die[1].lower() != "d" and die[0].lower() != "d":
			return await ctx.send("Use the format 'ndx'.")
		options = (4, 6, 8, 10, 12, 20, 100)
		for option in options:
			if die.endswith(str(option)):
				dice = option
		if dice == 0:
			return await ctx.send("You didn't give a die to use.")

		rolls = []
		if dice == 100:
			step = 10
		else:
			step = 1

		total = 0
		if multiplier > 1:
			for x in range(multiplier):
				rolls.append(random.randrange(step, dice+1, step))
			for r in rolls:
				total += r
			return await ctx.send("{} rolled **{}**. Totaling **{}**".format(ctx.message.author.mention, rolls, total))
		else:
			roll = random.randrange(step, dice + 1, step)
			return await ctx.send("{} rolled a **{}**".format(ctx.message.author.mention, roll))

	@checks.isnt_anal()
	@bot.command()
	async def spank(self, ctx, *, user: discord.User = None):
		"""
		Spanks the mentioned user ;)
		Usage:
			{command_prefix}spank @Roxbot_client#4170
			{command_prefix}spank Roxbot_client
		"""
		if not user:
			return await ctx.send("You didn't mention someone for me to spank")
		return await ctx.send(":peach: :wave: *{} spanks {}*".format(self.bot.user.name, user.name))

	@checks.isnt_anal()
	@bot.command(aliases=["succ"])
	async def suck(self, ctx, *, user: discord.User = None):
		"""
		Sucks the mentioned user ;)
		Usage:
			{command_prefix}suck @Roxbot_client#4170
			{command_prefix}suck Roxbot_client
		"""
		if not user:
			return await ctx.send("You didn't mention someone for me to suck")
		return await ctx.send(":eggplant: :sweat_drops: :tongue: *{} sucks {}*".format(self.bot.user.name, user.name))

	@bot.command()
	async def hug(self, ctx, *, user: discord.User = None):
		"""
		Hugs the mentioned user :3
		Usage:
			{command_prefix}hug @Roxbot_client#4170
			{command_prefix}hug Roxbot_client
		"""
		if not user:
			return await ctx.send("You didn't mention someone for me to hug")
		return await ctx.send(":blush: *{} hugs {}*".format(self.bot.user.name, user.name))

	@bot.command(aliases=["wf"])
	async def waifurate(self, ctx):
		"""
		Rates the mentioned waifu(s)
		Usage:
			{command_prefix}waifurate @user#9999
		"""
		mentions = ctx.message.mentions
		if not mentions:
			return await ctx.send("You didn't mention anyone for me to rate.", delete_after=10)

		rating = random.randrange(1, 11)
		if rating <= 2:
			emoji = ":sob:"
		elif rating <= 4:
			emoji = ":disappointed:"
		elif rating <= 6:
			emoji = ":thinking:"
		elif rating <= 8:
			emoji = ":blush:"
		elif rating == 9:
			emoji = ":kissing_heart:"
		else:
			emoji = ":heart_eyes:"

		if len(mentions) > 1:
			return await ctx.send("Oh poly waifu rating? :smirk: Your combined waifu rating is {}/10. {}".format(rating, emoji))
		else:
			return await ctx.send("Oh that's your waifu? I rate them a {}/10. {}".format(rating, emoji))

	@bot.command(aliases=["cf"])
	async def coinflip(self, ctx):
		"""Flip a coin"""
		return await ctx.send("The coin landed on {}!".format(random.choice(["heads", "tails"])))

	@bot.command()
	async def aesthetics(self, ctx, *, convert):
		"""Converts text to be more  a e s t h e t i c s"""
		WIDE_MAP = dict((i, i + 0xFEE0) for i in range(0x21, 0x7F))
		WIDE_MAP[0x20] = 0x3000
		converted = str(convert).translate(WIDE_MAP)
		await ctx.send(converted)

		logging = guild_settings.get(ctx.guild).logging
		log_channel = self.bot.get_channel(logging["channel"])
		await log(ctx.guild, log_channel, "aesthetics", User=ctx.author, Argument_Given=convert, Channel=ctx.channel, Channel_Mention=ctx.channel.mention)

	@bot.command(aliases=["ft", "frog"])
	async def frogtips(self, ctx):
		"""RETURNS FROG TIPS FOR HOW TO OPERATE YOUR FROG"""
		endpoint = "https://frog.tips/api/1/tips/"
		croak = requests.get(endpoint)
		tip = random.choice(croak.json()["tips"])
		embed = discord.Embed(title="Frog Tip #{}".format(tip["number"]), description=tip["tip"], colour=discord.Colour(0x4C943D))
		embed.set_author(name="HOW TO OPERATE YOUR FROG")
		embed.set_footer(text="https://frog.tips")
		return await ctx.send(embed=embed)


def setup(bot_client):
	bot_client.add_cog(Fun(bot_client))
