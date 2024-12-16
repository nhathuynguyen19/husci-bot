import discord, aiohttp, os, json, datetime, html, asyncio, base64
from discord.ext import tasks, commands
from bs4 import BeautifulSoup
from config import fixed_key, id_admin
from modules import UserManager, BotConfig, AuthManager, HUSCNotifications
from cryptography.fernet import Fernet
from dotenv import load_dotenv