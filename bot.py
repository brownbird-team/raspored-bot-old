import discord
import pyautogui
from discord.ext.commands import cooldown, BucketType
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from PIL import Image
import glob, os
from discord.ext import commands
client = commands.Bot(command_prefix=".", intents = discord.Intents.default())
@client.event
async def on_ready():
    print("Ready")

@client.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandOnCooldown):
		msg = "Cekaj delam vec"
		print("Request denied, already processing another request")
		await ctx.send(msg)

@client.command()
@commands.cooldown(1,25,commands.BucketType.guild)
async def raspored(ctx):
	await ctx.send("Delam")
	print("Sending")
	chrome_options= Options()
	driver=webdriver.Chrome(executable_path=r"/home/roko/Raspored/chromedriver",options=chrome_options)
	driver.get("https://www.tsrb.hr/b-smjena")
	driver.find_element_by_xpath("/html/body/div[6]/div[1]/div/div/div/article/div/section/div/div/div/div/section[2]/div/div/div/div/div/div[1]/div/div/div[1]/ul/li[3]/span").click()
	for x in range(1, 11):
		pyautogui.press("down")
	myScreenshot = pyautogui.screenshot()
	myScreenshot.save(r'/home/roko/Raspored/screenshot.png')
	im = Image.open(r'/home/roko/Raspored/screenshot.png').convert('L')
	im = im.crop((91, 429, 659, 628))
	im.save('0.png')
	await ctx.send(file=discord.File(r'/home/roko/Raspored/0.png'))
	pyautogui.hotkey('ctrl', 'f')
	pyautogui.typewrite('1.G\n', 1)
	pyautogui.press("enter")
	pyautogui.press("escape")
	myScreenshot = pyautogui.screenshot()
	myScreenshot.save(r'/home/roko/Raspored/screenshot.png')
	im = Image.open(r'/home/roko/Raspored/screenshot.png').convert('L')
	im = im.crop((84, 573, 667, 760))
	im.save('1.png')
	await ctx.send(file=discord.File(r'/home/roko/Raspored/1.png'))
	driver.close()
	await ctx.send("Gotov")
client.run("ODM5MDk0OTU3MjA1MzU2NTQ0.YJEqEw.vGuTA8Aqob77RAkdcPp1b_koKZs")
