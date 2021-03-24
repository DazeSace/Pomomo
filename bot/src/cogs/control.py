from discord.ext import commands
import sessions_manager
import session_controller
from Session import Session
from Settings import Settings
from utils import state_handler
from configs import config, bot_enum, user_messages as u_msg
import time as t


class Control(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def start(self, ctx, pomodoro=20, short_break=5, long_break=15, intervals=4):
        if not await Settings.is_valid(ctx, pomodoro, short_break, long_break, intervals):
            return

        if not ctx.author.voice:
            await ctx.send(u_msg.JOIN_CHANNEL)
            return
        if sessions_manager.connected_to_vc(ctx):
            await ctx.send(u_msg.ACTIVE_SESSION)
            return
        await ctx.author.voice.channel.connect()
        session = Session(Settings(pomodoro, short_break, long_break, intervals))
        session.ctx = ctx
        session.timer.running = True
        await session_controller.start(session)

    @start.error
    async def handle_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(u_msg.INV_NUM)
        else:
            raise error

    @commands.command()
    async def stop(self, ctx):
        session = sessions_manager.get_server_session(ctx)
        if not session:
            await ctx.send(u_msg.NO_ACTIVE_SESSION)
            return

        if ctx.voice_client:
            await ctx.guild.voice_client.disconnect()
        if session.pomos_completed > 0:
            await ctx.send(f'Great job! You completed {session.pomos_completed} pomodoros.')
        else:
            await ctx.send(f'See you again soon! 👋')
        sessions_manager.active_sessions.pop(ctx.guild.id)

    @commands.command()
    async def pause(self, ctx):
        session = sessions_manager.get_server_session(ctx)
        if not session:
            await ctx.send(u_msg.NO_ACTIVE_SESSION)
            return
        timer = session.timer
        if not timer.running:
            await ctx.send('Timer is already paused.')
            return

        timer.running = False
        timer.remaining = timer.end - t.time()
        await ctx.send(f'Pausing {session.state}.')
        session.timeout = t.time() + config.PAUSE_TIMEOUT

    @commands.command()
    async def resume(self, ctx):
        session = sessions_manager.get_server_session(ctx)
        if not session:
            await ctx.send(u_msg.NO_ACTIVE_SESSION)
            return
        timer = session.timer
        if session.timer.running:
            await ctx.send('Timer is already running.')
            return

        timer.running = True
        timer.end = t.time() + timer.remaining
        await ctx.send(f'Resuming {session.state}.')
        await session_controller.resume(session)

    @commands.command()
    async def restart(self, ctx):
        session = sessions_manager.get_server_session(ctx)
        if not session:
            await ctx.send(u_msg.NO_ACTIVE_SESSION)
            return
        session.timer.calculate_delay()
        await ctx.send(f'Restarting {session.state}.')
        await session_controller.resume(session)

    @commands.command()
    async def skip(self, ctx):
        session = sessions_manager.get_server_session(ctx)
        if not session:
            await ctx.send(u_msg.NO_ACTIVE_SESSION)
            return
        if session.pomos_completed > 0 and session.state == bot_enum.State.POMODORO:
            session.pomos_completed -= 1

        await ctx.send(f'Skipping {session.state}.')
        await state_handler.transition_session(session)
        await session_controller.resume(ctx)

    @commands.command()
    async def edit(self, ctx, pomodoro: int, short_break: int = None, long_break: int = None, intervals: int = None):
        session = sessions_manager.get_server_session(ctx)
        if not session:
            await ctx.send(u_msg.NO_ACTIVE_SESSION)
            return
        if not await Settings.is_valid(ctx, pomodoro, short_break, long_break, intervals):
            return
        await session_controller.edit(session, Settings(pomodoro, short_break, long_break, intervals))
        session.timer.calculate_delay()
        await session_controller.resume(session)

    @edit.error
    async def handle_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Pass in at least one number.')
        elif isinstance(error, commands.BadArgument):
            await ctx.send(u_msg.INV_NUM)
        else:
            raise error


def setup(client):
    client.add_cog(Control(client))
