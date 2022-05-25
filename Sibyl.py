import typing
import html
from pyrogram import Client, filters
from pyrogram.types import Message
from SibylSystem import PsychoPass
from SibylSystem.types import MultiScanInfo
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified
from shadowhawk import config, ee
from shadowhawk.utils import get_entity, self_destruct, build_name_flags
from shadowhawk.utils.Command import parse_command
from shadowhawk.utils.Logging import log_errors, public_log_errors, log_chat
from shadowhawk.plugins.moderation import ResolveChatUser

__help_section__ = "Sibyl"

sibyl_client: typing.Union[PsychoPass, None]

# Use OnDatabaseStart since it's fairly easy
# and we'll likely depend on database stuff anyway
@ee.on('OnDatabaseStart')
async def OnStart():
	global sibyl_client
	try:
		sibyl_client = PsychoPass(config['config']['sibyl_api'], show_license=False)
	except Exception:
		sibyl_client = None

@Client.on_message( ~filters.sticker & ~filters.via_bot & ~filters.edited & filters.me & filters.command(['asb', 'associationban', 'assban'], prefixes=config['config'][ 'prefixes']))
@log_errors
@public_log_errors
async def ass_ban(client: Client, message: Message) -> typing.Optional[None]:
	"""{prefix}associationban [-c=&ltchat&gt|as reply] -r="Reason text" - Request ban a group of users by association
Aliases: {prefix}assban, {prefix}asb
	"""
	global sibyl_client
	if not sibyl_client:
		await self_destruct(message, "This feature won't work due to lack of Sibyl API connection")
		return

	owo = parse_command(message.text)
	_, chat = await ResolveChatUser(owo, client, message)

	# TODO: ResolveChatUser will assume that the current chat is what should be eliminated
	# there needs to be a flag added to prevent this!

	reason = next((val for key, val in owo.items() if key in ["r", "reason"]), None)

	if not chat:
		await self_destruct(message, "<code>Cannot find the target chat</code>")
		return

	if not reason:
		await self_destruct(message, "<code>You must specify a reason</code>")
		return

	try:
		d = []
		chattext = await build_name_flags(client, chat)
		for mem in await client.get_chat_members(chat.id, filter="administrators"):
			if not mem.user.is_bot:
				# owo = MultiBanInfo(user_id=mem.user.id, is_bot=False, reason=reason, source=message.link, source_group=chat.id)
				owo = MultiScanInfo(user_id=mem.user.id, reason=reason, message=message.reply_to_message.text or "")
				d.append(owo)
				# sibyl_client.add_ban(user_id=mem.user.id, reason=reason, source=message.link)
				text = "<b>Sibyl Association Ban Request</b> [#SIBYLBAN]"
				text += f"\n- <b>Chat:</b> {chattext}"
				text += "\n- <b>Banned:</b> " + await build_name_flags(client, mem.user)
				text += f"\n- <b>Reason:</b> <code>{html.escape(reason)}</code>"
				await log_chat(text)
		response = sibyl_client.multi_scan(source=message.link, group_link="https://t.me/{}".format(chat.username or chat.id), info=d)
		await self_destruct(message, f"Banned {len(d)} people for reason <code>{reason}</code>\nSibyl: <code>{response}</code>")
	except BaseException as e:
		await self_destruct(message, f"Failed due to <code>{e}</code>")


@Client.on_message( ~filters.sticker & ~filters.via_bot & ~filters.edited & filters.me & filters.command(['elm', 'eliminate'], prefixes=config['config'][ 'prefixes']))
@log_errors
@public_log_errors
async def req_ban_user(client: Client, message: Message) -> typing.Optional[None]:
	"""{prefix}eliminate [-u=&ltuser&gt|as reply|as mention] -r="Reason text" - Request the use of the Lethal Eliminator mode of your Dominator
Aliases: {prefix}elm
	"""
	global sibyl_client
	if not sibyl_client:
		await self_destruct(message, "This feature won't work due to lack of Sibyl API connection")
		return

	owo = parse_command(message.text)
	user, _ = await ResolveChatUser(owo, client, message)
	msg = message.reply_to_message.text if message.reply_to_message else ""
	reason = next((val for key, val in owo.items() if key in ["r", "reason"]), None)

	if not user:
		await self_destruct(message, "<code>Cannot find the target user</code>")
		return

	if not reason:
		await self_destruct(message, "<code>You must specify a reason</code>")
		return

	try:
		a = sibyl_client.report_user(user.id, reason=reason, message=msg, source_url=message.link)
		print(a)
		nametext = await build_name_flags(client, user)
		text = "<b>Sibyl Ban Request</b> [#SIBYLBAN]"
		text += "\n- <b>Banned:</b> " + nametext
		text += f"\n- <b>Reason:</b> <code>{html.escape(reason)}</code>"
		await log_chat(text)
		await self_destruct(message, f"{nametext} was eliminated with reason <code>{reason}</code>")
	except BaseException as e:
		await self_destruct(message, f"Failed due to <code>{e}</code>")


@Client.on_message( ~filters.sticker & ~filters.via_bot & ~filters.edited & filters.me & filters.command(['cymatic', 'cyscan', 'cc'], prefixes=config['config'][ 'prefixes']))
@log_errors
@public_log_errors
async def lookup_user(client: Client, message: Message) -> typing.Optional[None]:
	"""{prefix}cymatic [-u=&ltuser&gt|as reply|as mention] - Query information on a user
Aliases: {prefix}cyscan, {prefix}cc
	"""
	global sibyl_client
	if not sibyl_client:
		await self_destruct(message, "This feature won't work due to lack of Sibyl API connection")
		return

	owo = parse_command(message.text)
	user, _ = await ResolveChatUser(owo, client, message)

	info = sibyl_client.get_info(user.id)
	officer_info = None

	# Determine if we need to make a stupid "get more info" call
	if info.crime_coefficient <= 10 or (info.crime_coefficient > 100 and info.crime_coefficient <= 150):
		officer_info = sibyl_client.get_general_info(user.id)
		if officer_info and officer_info.result:
			officer_info = officer_info.result

	# Try and get the enforcer
	officer = None
	try:
		officer = await get_entity(client, info.banned_by)
	except ValueError:
		pass

	reply = None
	for ping in range(0, 2):
		text = "<b>Cymatic Scan Results</b>\n"
		text += await build_name_flags(client, user, ping=bool(ping))
		text += "" if not info.crime_coefficient else f"\n- <b>Crime Coefficient:</b> <code>{info.crime_coefficient}</code>"
		text += "" if not info.hue_color else f"\n- <b>Hue:</b> <code>{info.hue_color}</code>"
		# text += "" if not info.date else f"\n- <b>Record Date:</b> <code>{info.date}</code>"
		text += "" if not info.is_bot else "\n- <b>Bot:</b> <code>Yes</code>"
		text += "" if not info.banned else "\n- <b>Banned:</b> <code>Yes</code>"
		text += "" if not info.reason else f"\n- <b>Ban Reason:</b> <code>{info.reason}</code>"
		text += "" if not info.banned_by else f"\n- <b>Ban Enforcer:</b> {await build_name_flags(client, officer[0], ping=bool(ping))}"
		text += "" if not info.ban_source_url else f"\n- <b>Ban Source:</b> <code>{info.ban_source_url}</code>"
		text += "" if not info.ban_flags else f"\n- <b>Ban Flags:</b> <code>{' '.join(info.ban_flags)}</code>"
		text += "" if not info.source_group else f"\n- <b>Source Group:</b> <code>{info.source_group}</code>"
		
		if officer_info:
			text += "" if not officer_info.division else f"\n- <b>Divison:</b> <code>{officer_info.division}</code>"
			text += "" if not officer_info.assigned_by else f"\n- <b>Assigned By:</b> {await build_name_flags(client, officer, ping=bool(ping))}"
			text += "" if not officer_info.assigned_reason else f"\n- <b>Reason for Assignment:</b> <code>{officer_info.assigned_reason}</code>"
			text += "" if not officer_info.assigned_at else f"\n- <b>Assignment Date:</b> <code>{officer_info.assigned_at}</code>"
			text += "" if not officer_info.permission else f"\n- <b>Position:</b> <code>{officer_info.permission.name.title()}</code>"
		
		if bool(ping):
			try:
				await reply.edit(text, disable_web_page_preview=True)
			except MessageNotModified:
				pass
		else:
			reply = await message.reply(text, disable_web_page_preview=True)



__signature__ = "SHSIG-INFh7PUISMcLCJgr5ogpY1Fn+/Kb+CxF3b1KU7srQJjTAAAAILtuMCcjZiHUG7kAaeTrOZghWRwEt/MV07mVK8kVsnK7AAAA"
