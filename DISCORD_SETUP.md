# Discord Integration Setup Guide for Chaptrix

This guide explains how to set up Discord integration for Chaptrix automation, allowing you to receive notifications with chapter updates and download links.

**Note: Discord integration is completely optional.** Chaptrix will work without Discord credentials, but you won't receive notifications about new chapters.

## Webhook Method vs. Bot Method

Chaptrix supports two methods for Discord integration:

1. **Webhook Method** (Simpler):
   - Easier to set up
   - No bot hosting required
   - Limited to text and file attachments
   - 8MB file size limit (25MB for premium servers)
   - Cannot use rich embeds with buttons

2. **Bot Method** (More features):
   - Requires creating and configuring a Discord bot
   - Supports rich embeds with buttons
   - Higher file size limits
   - Can interact with users
   - More customization options

## Setting Up Discord Webhook (Recommended for Beginners)

### 1. Create a Webhook in Discord

1. Open Discord and go to the server where you want to receive notifications
2. Right-click on the channel and select "Edit Channel"
3. Click on "Integrations"
4. Click on "Webhooks"
5. Click "New Webhook"
6. (Optional) Customize the webhook name and avatar
7. Click "Copy Webhook URL"

### 2. Configure Chaptrix to Use the Webhook

For GitHub Actions automation:

1. Go to your GitHub repository
2. Go to "Settings" > "Secrets and variables" > "Actions"
3. Create a new repository secret named `DISCORD_WEBHOOK_URL`
4. Paste the webhook URL as the value
5. Click "Add secret"

## Setting Up Discord Bot (Advanced)

### 1. Create a Discord Application and Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Enter a name for your application (e.g., "Chaptrix Bot")
4. Click "Create"
5. In the left sidebar, click on "Bot"
6. Click "Add Bot"
7. Confirm by clicking "Yes, do it!"

### 2. Configure Bot Settings

1. (Optional) Customize your bot's username and avatar
2. Under "Privileged Gateway Intents", enable:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
3. Click "Save Changes"
4. Under the "TOKEN" section, click "Reset Token" and then "Yes, do it!"
5. Copy the token (you'll only see it once!)

### 3. Add Bot to Your Server

1. In the left sidebar, click on "OAuth2" > "URL Generator"
2. Under "Scopes", select "bot"
3. Under "Bot Permissions", select:
   - Send Messages
   - Embed Links
   - Attach Files
   - Read Message History
   - Use External Emojis
4. Copy the generated URL at the bottom
5. Open the URL in a new browser tab
6. Select your server and click "Continue"
7. Verify the permissions and click "Authorize"
8. Complete the CAPTCHA if prompted

### 4. Get Channel ID

1. Open Discord
2. Go to User Settings > Advanced
3. Enable "Developer Mode"
4. Right-click on the channel where you want to receive notifications
5. Click "Copy ID"

### 5. Configure Chaptrix to Use the Bot

For GitHub Actions automation:

1. Go to your GitHub repository
2. Go to "Settings" > "Secrets and variables" > "Actions"
3. Create these repository secrets:
   - `DISCORD_BOT_TOKEN`: Your bot token
   - `DISCORD_CHANNEL_ID`: The channel ID
4. Click "Add secret" for each

## Testing Discord Integration

### Testing Webhook

You can test your webhook with this curl command (replace with your actual webhook URL):

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"content":"Testing Chaptrix webhook integration"}' \
  YOUR_WEBHOOK_URL
```

### Testing Bot

To test your bot integration, you can create a simple Python script:

```python
import discord
import asyncio

async def test_bot():
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f'Logged in as {client.user}')
        channel = client.get_channel(YOUR_CHANNEL_ID)  # Replace with your channel ID
        await channel.send('Testing Chaptrix bot integration')
        await client.close()
    
    await client.start('YOUR_BOT_TOKEN')  # Replace with your bot token

asyncio.run(test_bot())
```

## Customizing Discord Notifications

You can customize how notifications appear in Discord by modifying the relevant functions in `main.py`:

- For webhook notifications: `send_discord_notification_webhook`
- For bot notifications: `send_discord_notification_bot`

Consider customizing:

- Message content
- Embed colors and fields
- Thumbnail and image attachments
- Button labels and URLs

## Disabling Discord Notifications

If you want to disable Discord notifications entirely:

1. Open `settings.json`
2. Set `"upload_to_discord": false`

This will prevent Chaptrix from attempting to send Discord notifications even if credentials are configured.

## Troubleshooting

### Common Webhook Issues

1. **Invalid Webhook URL**: Ensure the webhook URL is correct and hasn't been deleted
2. **Rate Limiting**: Discord limits webhooks to 5 requests per second
3. **File Size**: Webhooks have an 8MB file size limit (25MB for premium servers)

### Common Bot Issues

1. **Invalid Token**: Ensure the bot token is correct and hasn't been reset
2. **Missing Permissions**: Check that the bot has the necessary permissions in the channel
3. **Intents**: Verify that the required intents are enabled in the Discord Developer Portal
4. **Channel ID**: Confirm the channel ID is correct

### Getting Help

If you're still experiencing issues:

1. Check the Discord API documentation: https://discord.com/developers/docs
2. Review the Discord.py documentation: https://discordpy.readthedocs.io/
3. Include detailed error messages when seeking help