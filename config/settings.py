import os
import sys
import aiohttp
import asyncio

import checks
import load_config
from config.server_config import ServerConfig

import discord
from discord.ext.commands import bot, group, is_owner


class Settings:
	"""
	Settings is a mix of settings and admin stuff for the bot. OWNER OR ADMIN ONLY.
	"""
	def __init__(self, bot_client):
		self.bot = bot_client
		self.con = ServerConfig()
		self.serverconfig = self.con.servers

	def get_channel(self, ctx, channel):
		if ctx.message.channel_mentions:
			return ctx.message.channel_mentions[0]
		else:
			return self.bot.get_channel(channel)

	@bot.command(pass_context=True)
	@checks.is_owner_or_admin()
	async def blacklist(self, ctx, option):
		"""
		OWNER OR ADMIN ONLY: Add or remove users to the blacklist.
		Blacklisted users are forbidden from using bot commands.
		"""
		blacklist_amount = 0
		mentions = ctx.message.mentions

		if not mentions:
			return await ctx.send("You didn't mention anyone")

		if option not in ['+', '-', 'add', 'remove']:
			return await ctx.send('Invalid option "%s" specified, use +, -, add, or remove' % option, expire_in=20)

		for user in mentions:
			if user.id == load_config.owner:
				print("[Commands:Blacklist] The owner cannot be blacklisted.")
				await ctx.send("The owner cannot be blacklisted.")
				mentions.remove(user)

		if option in ['+', 'add']:
			with open("config/blacklist.txt", "r") as fp:
				for user in mentions:
					for line in fp.readlines():
						if user.id + "\n" in line:
							mentions.remove(user)

			with open("config/blacklist.txt", "a+") as fp:
				lines = fp.readlines()
				for user in mentions:
					if user.id not in lines:
						fp.write("{}\n".format(user.id))
						blacklist_amount += 1
			return await ctx.send('{} user(s) have been added to the blacklist'.format(blacklist_amount))

		elif option in ['-', 'remove']:
			with open("config/blacklist.txt", "r") as fp:
				lines = fp.readlines()
			with open("config/blacklist.txt", "w") as fp:
				for user in mentions:
					for line in lines:
						if user.id + "\n" != line:
							fp.write(line)
						else:
							fp.write("")
							blacklist_amount += 1
				return await ctx.send('{} user(s) have been removed from the blacklist'.format(blacklist_amount))

	@bot.command(pass_context=True, hidden=True, aliases=["setava", "setavatar"])
	@is_owner()
	async def changeavatar(self, ctx, url=None):
		# TODO: Organise the non-settings group commands to be better and support gifs and shit. Also not hidden and the better check.
		"""
		Usage:
			{command_prefix}setavatar [url]
		Changes the bot's avatar.
		Attaching a file and leaving the url parameter blank also works.
		"""
		if ctx.message.attachments:
			thing = ctx.message.attachments[0]['url']
		else:
			thing = url.strip('<>')

		avaimg = 'avaimg'
		async with aiohttp.ClientSession() as session:
			async with session.get(thing) as img:
				with open(avaimg, 'wb') as f:
					f.write(await img.read())
		with open(avaimg, 'rb') as f:
			await self.bot.user.edit(avatar=f.read())
		os.remove(avaimg)
		asyncio.sleep(2)
		return await ctx.send(":ok_hand:")

	@bot.command(pass_context=True, hidden=True, aliases=["nick"])
	@is_owner()
	async def changenickname(self, ctx, *nick):
		if ctx.message.channel.permissions_for(ctx.message.server.me).change_nickname:
			await self.bot.change_nickname(ctx.message.server.me, ' '.join(nick))
			return await ctx.send(":thumbsup:")
		else:
			return await ctx.send("I don't have permission to do that :sob:", delete_after=self.con.delete_after)

	@bot.command(pass_context=True, hidden=True, aliases=["setgame", "game"])
	@is_owner()
	async def changegame(self, ctx, *, game: str):
		# TODO: Update for new presence changes
		if game.lower() == "none":
			game_name = None
		else:
			game_name = discord.Game(name=game, type=0)
		await self.bot.change_presence(game=game_name, afk=False)
		return await ctx.send(":ok_hand: Game set to {}".format(str(game_name)))

	@bot.command(pass_context=True, hidden=True, aliases=["status"])
	@is_owner()
	async def changestatus(self, ctx, status: str):
		status = status.lower()
		if status == 'offline' or status == 'invisible':
			discordStatus = discord.Status.invisible
		elif status == 'idle':
			discordStatus = discord.Status.idle
		elif status == 'dnd':
			discordStatus = discord.Status.dnd
		else:
			discordStatus = discord.Status.online
		await self.bot.change_presence(status=discordStatus)
		await ctx.send("**:ok:** Status set to {}".format(discordStatus))

	@bot.command(hidden=True)
	@is_owner()
	async def restart(self):
		await self.bot.logout()
		return os.execl(sys.executable, sys.executable, *sys.argv)

	@bot.command(hidden=True)
	@is_owner()
	async def shutdown(self):
		await self.bot.logout()
		return exit(0)

	@bot.command(pass_context=True)
	@checks.is_owner_or_admin()
	async def printsettings(self, ctx):
		"OWNER OR ADMIN ONLY: Prints the servers config file."
		self.serverconfig = self.con.load_config()
		config = self.serverconfig[str(ctx.message.guild.id)]
		em = discord.Embed(colour=0xDEADBF)
		em.set_author(name="{} settings for {}.".format(self.bot.user.name, ctx.message.guild.name), icon_url=self.bot.user.avatar_url)
		for settings in config:
			if settings != "custom_commands" and settings != "warnings":
				settingcontent = ""
				for x in config[settings].items():
					settingcontent += str(x).strip("()") + "\n"
				em.add_field(name=settings, value=settingcontent, inline=False)
			elif settings == "custom_commands":
				em.add_field(name="custom_commands", value="For Custom Commands, use the custom list command.", inline=False)
		return await ctx.send(embed=em)

	@group(pass_context=True)
	@checks.is_admin_or_mod()
	async def settings(self, ctx):
		if ctx.invoked_subcommand is None:
			return await ctx.send('Missing Argument')
		self.serverconfig = self.con.load_config()
		self.guild_id = str(ctx.message.guild.id)

	@settings.command(pass_context=True, aliases=["sa"])
	async def selfassign(self, ctx, selection, *, changes = None):
		"""
		Adds a role to the list of roles that can be self assigned for that server.
		Removes a role from the list of self assignable roles for that server.
		"""
		selection = selection.lower()
		role = discord.utils.find(lambda u: u.name == changes, ctx.message.guild.roles)
		if selection == "enable":
			self.serverconfig[self.guild_id]["self_assign"]["enabled"] = 1
			await ctx.send("'self_assign' was enabled!")
		elif selection == "disable":
			self.serverconfig[self.guild_id]["self_assign"]["enabled"] = 0
			await ctx.send("'self_assign' was disabled :cry:")
		elif selection == "addrole":
			if role.id in self.serverconfig[ctx.message.guild.id]["self_assign"]["roles"]:
				return await ctx.send("{} is already a self-assignable role.".format(role.name),
										  delete_after=self.con.delete_after)

			self.serverconfig[ctx.message.guild.id]["self_assign"]["roles"].append(role.id)
			await ctx.send('Role "{}" added'.format(str(role)))
		elif selection == "removerole":
			if role.id in self.serverconfig[ctx.message.guild.id]["self_assign"]["roles"]:
				self.serverconfig[ctx.message.guild.id]["self_assign"]["roles"].remove(role.id)
				self.con.update_config(self.serverconfig)
				await ctx.send('"{}" has been removed from the self-assignable roles.'.format(str(role)))
			else:
				return await ctx.send("That role was not in the list.")
		else:
			return await ctx.send("No valid option given.")
		return self.con.update_config(self.serverconfig)

	@settings.command(pass_context=True, aliases=["jl"])
	async def joinleave(self, ctx, selection, *, changes = None):
		selection = selection.lower()
		if selection == "enable":
			if changes == "greets":
				self.serverconfig[self.guild_id]["greets"]["enabled"] = 1
				await ctx.send("'greets' was enabled!")
			elif changes == "goodbyes":
				self.serverconfig[self.guild_id]["goodbyes"]["enabled"] = 1
				await ctx.send("'goodbyes' was enabled!")
		elif selection == "disable":
			if changes == "greets":
				self.serverconfig[self.guild_id]["greets"]["enabled"] = 0
				await ctx.send("'greets' was disabled :cry:")
			elif changes == "goodbyes":
				self.serverconfig[self.guild_id]["goodbyes"]["enabled"] = 0
				await ctx.send("'goodbyes' was disabled :cry:")
		elif selection == "welcomechannel":
			channel = self.get_channel(ctx, changes)
			self.serverconfig[ctx.message.guild.id]["greets"]["welcome-channel"] = channel.id
			await ctx.send("{} has been set as the welcome channel!".format(channel.mention))
		elif selection == "goodbyeschanel":
			channel = self.get_channel(ctx, changes)
			self.serverconfig[ctx.message.guild.id]["goodbyes"]["goodbye-channel"] = channel.id
			await ctx.send("{} has been set as the goodbye channel!".format(channel.mention))
		elif selection == "custommessage":
			self.serverconfig[ctx.message.guild.id]["greets"]["custom-message"] = changes
			await ctx.send("Custom message set to '{}'".format(changes))
		else:
			return await ctx.send("No valid option given.")
		return self.con.update_config(self.serverconfig)

	@settings.command(pass_context=True)
	async def twitch(self, ctx, selection, *, changes = None):
		selection = selection.lower()
		if selection == "enable":
			self.serverconfig[self.guild_id]["twitch"]["enabled"] = 1
			await ctx.send("'twitch' was enabled!")
		elif selection == "disable":
			self.serverconfig[self.guild_id]["twitch"]["enabled"] = 0
			await ctx.send("'twitch' was disabled :cry:")
		elif selection == "channel":
			channel = self.get_channel(ctx, changes)
			self.serverconfig[ctx.message.guild.id]["twitch"]["twitch-channel"] = channel.id
			await ctx.send("{} has been set as the twitch shilling channel!".format(channel.mention))
		else:
			return await ctx.send("No valid option given.")
		return self.con.update_config(self.serverconfig)

	@settings.command(pass_context=True, aliases=["perms"])
	async def permrole(self, ctx, selection, *, changes = None):
		"""
		Adds a role to the list of roles that can be self assigned for that server.
		Removes a role from the list of self assignable roles for that server.
		"""
		selection = selection.lower()
		role = discord.utils.find(lambda u: u.name == changes, ctx.message.guild.roles)
		if selection == "addadmin":
			if role.id not in self.serverconfig[ctx.message.guild.id]["perm_roles"]["admin"]:
				self.serverconfig[ctx.message.guild.id]["perm_roles"]["admin"].append(role.id)
				await ctx.send("'{}' has been added to the Admin role list.".format(role.name))
			else:
				return await ctx.send("'{}' is already in the list.".format(role.name))
		elif selection == "addmod":
			if role.id not in self.serverconfig[ctx.message.guild.id]["perm_roles"]["mod"]:
				self.serverconfig[ctx.message.guild.id]["perm_roles"]["mod"].append(role.id)
				await ctx.send("'{}' has been added to the Mod role list.".format(role.name))
			else:
				return await ctx.send("'{}' is already in the list.".format(role.name))
		elif selection == "removeadmin":
			try:
				self.serverconfig[ctx.message.guild.id]["perm_roles"]["admin"].remove(role.id)
				await ctx.send("'{}' has been removed from the Admin role list.".format(role.name))
			except ValueError:
				return await ctx.send("That role was not in the list.")
		elif selection == "removemod":
			try:
				self.serverconfig[ctx.message.guild.id]["perm_roles"]["mod"].remove(role.id)
				await ctx.send("'{}' has been removed from the Mod role list.".format(role.name))
			except ValueError:
				return await ctx.send("That role was not in the list.")

		else:
			return await ctx.send("No valid option given.")
		return self.con.update_config(self.serverconfig)

	@settings.command(pass_context=True)
	async def gss(self, ctx, selection, *, changes = None):
		selection = selection.lower()
		if selection == "loggingchannel":
			channel = self.get_channel(ctx, changes)
			self.serverconfig[ctx.message.guild.id]["gss"]["log_channel"] = channel.id
			await ctx.send("Logging Channel set to '{}'".format(channel.name))
		elif selection == "requireddays":
			self.serverconfig[ctx.message.guild.id]["gss"]["required_days"] = int(changes)
			await ctx.send("Required days set to '{}'".format(str(changes)))
		elif selection == "requiredscore":
			self.serverconfig[ctx.message.guild.id]["gss"]["required_score"] = int(changes)
			await ctx.send("Required score set to '{}'".format(str(changes)))
		else:
			return await ctx.send("No valid option given.")
		return self.con.update_config(self.serverconfig)


	@settings.command(pass_context=True)
	async def nsfw(self, ctx, selection, *, changes = None):
		selection = selection.lower()
		if selection == "enable":
			self.serverconfig[self.guild_id]["nsfw"]["enabled"] = 1
			await ctx.send("'nsfw' was enabled!")
		elif selection == "disable":
			self.serverconfig[self.guild_id]["nsfw"]["enabled"] = 0
			await ctx.send("'nsfw' was disabled :cry:")
		elif selection == "addchannel":
			channel = self.get_channel(ctx, changes)
			if channel.id not in self.serverconfig[ctx.message.guild.id]["nsfw"]["channels"]:
				self.serverconfig[ctx.message.guild.id]["nsfw"]["channels"].append(channel.id)
				await ctx.send("'{}' has been added to the nsfw channel list.".format(channel.name))
			else:
				return await ctx.send("'{}' is already in the list.".format(channel.name))
		elif selection == "removechannel":
			channel = self.get_channel(ctx, changes)
			try:
				self.serverconfig[ctx.message.guild.id]["nsfw"]["channels"].remove(channel.id)
				await ctx.send("'{}' has been removed from the nsfw channel list.".format(channel.name))
			except ValueError:
				return await ctx.send("That role was not in the list.")
		else:
			return await ctx.send("No valid option given.")
		return self.con.update_config(self.serverconfig)

	@checks.is_admin_or_mod()
	@bot.command(pass_context=True)
	async def serverisanal(self, ctx):
		self.serverconfig = self.con.load_config()
		is_anal = self.serverconfig[ctx.message.guild.id]["is_anal"]["y/n"]
		if is_anal == 0:
			self.serverconfig[ctx.message.guild.id]["is_anal"]["y/n"] = 1
			self.con.update_config(self.serverconfig)
			return await ctx.send("I now know this server is anal")
		else:
			self.serverconfig[ctx.message.guild.id]["is_anal"]["y/n"] = 0
			self.con.update_config(self.serverconfig)
			return await ctx.send("I now know this server is NOT anal")


def setup(Bot):
	Bot.add_cog(Settings(Bot))