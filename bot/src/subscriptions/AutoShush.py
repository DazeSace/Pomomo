from discord.ext.commands import Context
from session import session_manager
from bot.configs import config, bot_enum
from Subscriptions import Subscriptions


ALL = "all"


class AutoShush(Subscriptions):

    def __init__(self):
        super().__init__()
        self.all = False

    async def shush(self, ctx: Context, who=None):
        vc_members = session_manager.get_nonbot_members_in_voice_channel(ctx)
        if who == ALL:
            for member in vc_members:
                await member.edit(deafen=True, mute=True)
        elif who:
            await who.edit(deafen=True, mute=True)
        elif self.all:
            for member in vc_members:
                await member.edit(deafen=True, mute=True)
        else:
            for member in vc_members:
                if member in self.subs:
                    await member.edit(deafen=True, mute=True)

    async def unshush(self, ctx: Context, who=None):
        vc_members = session_manager.get_nonbot_members_in_voice_channel(ctx)
        if who == ALL:
            for member in vc_members:
                await member.edit(deafen=False, mute=False)
        elif who:
            await who.edit(deafen=False, mute=False)
        elif self.all:
            for member in vc_members:
                await member.edit(deafen=False, mute=False)
        else:
            for member in vc_members:
                if member in self.subs:
                    await member.edit(deafen=False, mute=False)

    async def handle_all(self, ctx: Context):
        permissions = ctx.author.permissions_in(ctx.channel)
        vc_name = session_manager.get_voice_channel(ctx).name
        if not ((permissions.deafen_members and permissions.mute_members) or permissions.administrator):
            await ctx.send('You do not have permission to mute and deafen other members.')
            return
        if self.all:
            self.all = False
            await ctx.send(f'Auto-shush has been turned off for the {vc_name} channel.')
            await self.unshush(ctx, ALL)
        else:
            self.all = True
            await ctx.send(f'Auto-shush has been turned on for the {vc_name} channel.')
            await self.shush(ctx, ALL)

    async def remove_sub(self, ctx: Context):
        vc_members = session_manager.get_nonbot_members_in_voice_channel(ctx)
        vc_name = session_manager.get_voice_channel(ctx).name
        if self.all:
            await ctx.send(f'Auto-shush is already turned on for all members in the {vc_name} channel.')
            return
        self.subs.remove(ctx.author)
        await ctx.author.send('You will no longer be automatically deafened and muted'
                              f' during pomodoro intervals in {ctx.guild.name}\'s {vc_name} channel.\n')
        if ctx.author in vc_members:
            await self.unshush(ctx, ctx.author)

    async def add_sub(self, state: bot_enum.State, ctx: Context):
        vc_members = session_manager.get_nonbot_members_in_voice_channel(ctx)
        vc_name = session_manager.get_voice_channel(ctx).name
        if self.all:
            await ctx.send(f'Auto-shush is already turned on for all members in the {vc_name} channel.')
            return
        self.subs.add(ctx.author)
        await ctx.author.send(f'Hey {ctx.author.display_name}! You will now be automatically deafened and muted '
                              f'during pomodoro intervals in {ctx.guild.name}\'s {vc_name} channel.\n'
                              f'Use command \'{config.CMD_PREFIX}auto_shush\' in one of the server\'s '
                              'text channels to turn off auto-shush.')
        if state in [bot_enum.State.POMODORO, bot_enum.State.COUNTDOWN] and ctx.author in vc_members:
            await self.shush(ctx, ctx.author)
