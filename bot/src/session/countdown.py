from session.Session import Session
import time as t
from asyncio import sleep
from session import session_manager, session_controller
from utils import player
from discord.ext.commands import Context
from discord import Colour


async def handle_connection(ctx: Context, audio_alert: bool):
    if audio_alert:
        if not session_manager.connected_to_vc(ctx):
            await ctx.author.voice.channel.connect()
            await ctx.guild.get_member(ctx.bot.user.id).edit(deafen=True)
    else:
        if session_manager.connected_to_vc(ctx):
            await ctx.guild.voice_client.disconnect()


async def cleanup_pins(ctx: Context):
    for pinned_msg in await ctx.channel.pins():
        if pinned_msg.author == ctx.bot.user:
            embed = pinned_msg.embeds[0]
            embed.colour = Colour.red()
            await pinned_msg.unpin()
            await pinned_msg.edit(embed=embed)


async def update_msg(session: Session):
    timer = session.timer
    timer.remaining = timer.end - t.time()
    if not session.countdown_msg:
        return
    countdown_msg = session.countdown_msg
    embed = countdown_msg.embeds[0]
    if timer.remaining < 0:
        embed.colour = Colour.red()
        embed.description = 'DONE!'
        await countdown_msg.edit(embed=embed)
        for sub in session.subscriptions.dm_subs:
            await sub.send(embed=embed)
        await player.alert(session)
        await session_controller.end(session)
        return
    embed.description = f'{timer.time_remaining_to_str(include_seconds=True)} left!'
    await countdown_msg.edit(embed=embed)


async def start(session: Session):
    session.timer.running = True
    await cleanup_pins(session.ctx)
    while True:
        time_remaining = session.timer.remaining
        await sleep(1)
        session = session_manager.active_sessions.get(session.ctx.guild.id)
        if not (session and
                session.timer.running and
                time_remaining == session.timer.remaining):
            break
        await update_msg(session)