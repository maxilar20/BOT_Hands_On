# -*- coding: utf-8 -*-
import os
import random
import discord
import csv
import json
import pandas as pd
from dotenv import load_dotenv
from tabulate import tabulate
from discord.ext import tasks, commands
import asyncio

load_dotenv("TOKEN.env")
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

async def update_player(member, player):
    try:
        # Changing nickname
        nick = player["nombre"] if len(player["nombre"]) < 30 else player["nombre"][0:30]
        await member.edit(nick=nick)

        # Assigning rols
        rol_level = discord.utils.get(member.guild.roles, name=player["rango"])
        if player["coh"] == '1':
            rol_coh = discord.utils.get(member.guild.roles, name="COH")
            await member.edit(roles=[rol_level, rol_coh])
        else:
            rol_casa = discord.utils.get(member.guild.roles, name=player["casa"])
            await member.edit(roles=[rol_casa, rol_level])
    except:
        print(f"An exception ocurred with {member}, {player['nombre']}")

async def message_status(member, player, teams):
    team_m = teams.loc[player["id_equipo_monster"]] if player["id_equipo_monster"] != 0 else "N/A"
    team_s = teams.loc[player["id_equipo_sumo"]] if player["id_equipo_sumo"] != 0 else "N/A"
    team_r = teams.loc[player["id_equipo_rover"]] if player["id_equipo_rover"] != 0 else "N/A"
    status_m = (int(team_m["DD"]), int(team_m["DF"]), int(team_m["CL"]), int(team_m["CG"]), int(team_m["lugar"])) if isinstance(team_m, pd.Series) else (" "," "," "," "," ")
    status_s = (int(team_s["DD"]), int(team_s["DF"]), int(team_s["CL"]), int(team_s["CG"]), int(team_s["lugar"])) if isinstance(team_s, pd.Series) else (" "," "," "," "," ")
    status_r = (int(team_r["DD"]), int(team_r["DF"]), int(team_r["CL"]), int(team_r["CG"]), int(team_r["lugar"])) if isinstance(team_r, pd.Series) else (" "," "," "," "," ")

    logo = discord.File("logo_coh.png")
    status_embed = discord.Embed(title=f"__**{player['nombre']}:**__ {rango_dict[player['rango']]}",
                                description=f"Puntos Acumulados: **{player['puntos']}**, Rango: **{player['rango']}**\
                                            \nEquipo actual: **{player['equipo_actual']}**, casa: **{player['casa']}**", color=0x00ff00)
    status_embed.add_field(name=":horse_racing:  __**Monster**__",
                            value=f"Equipo: **{player['equipo_monster']}** \nPuntos: **{player['puntos_monster']}** \
                            \n {tabulate([['DD','DF','CL','CG','Lugar'], [status_dict[status_m[0]], status_dict[status_m[1]], status_dict[status_m[2]], status_dict[status_m[3]], places_dict.get(status_m[4], ':zero:')]], tablefmt='plain')}",
                            inline=True)
    status_embed.add_field(name=":martial_arts_uniform:  __**Sumo**__",
                            value=f"Equipo: **{player['equipo_sumo']}** \nPuntos: **{player['puntos_sumo']}** \
                            \n {tabulate([['DD','DF','CL','CG','Lugar'], [status_dict[status_s[0]], status_dict[status_s[1]], status_dict[status_s[2]], status_dict[status_s[3]], places_dict.get(status_s[4], ':zero:')]], tablefmt='plain')}",
                            inline=True)
    status_embed.add_field(name=":robot:  __**Rover**__",
                            value=f"Equipo: **{player['equipo_rover']}** \nPuntos: **{player['puntos_rover']}** \
                            \n {tabulate([['DD','DF','CL','CG','Lugar'], [status_dict[status_r[0]], status_dict[status_r[1]], status_dict[status_r[2]], status_dict[status_r[3]], places_dict.get(status_r[4], ':zero:')]], tablefmt='plain')}",
                            inline=True)
    status_embed.set_thumbnail(url="attachment://logo_coh.png")
    await member.send(file = logo, embed = status_embed)


@tasks.loop(seconds=1)
async def update_status_torneo():
    await client.wait_until_ready()
    try:
        with open('DataBase.xlsx', 'rb') as file :
            torneos = pd.read_excel(file, sheet_name='torneos', index_col=0, header=0)
            teams   = pd.read_excel(file, sheet_name='equipos', index_col=0, header=0).fillna(0)
        with open('message_ids.csv', 'rb') as file :
            message_ids = pd.DataFrame(pd.read_csv(file, index_col = 0, header = 0, squeeze = True))
    except:
        print("failed to open")
        return


    channel = discord.utils.get(client.get_all_channels(), guild__name='Hands-On RD', name='📃status-torneos')
    for torneo, info_torneo in torneos.loc[torneos["activo"]==1].iterrows():
        try:
            message_edit = await channel.fetch_message(message_ids.loc[torneo, "message_id"])
        except:
            message_edit = await channel.send(embed = discord.Embed(title=f"__**Torneo {info_torneo.loc['nombre']}:**__",description=""))
            message_ids.loc[torneo, "message_id"] = str(message_edit.id)

        torneo_status_embed = discord.Embed(title=f"__**Torneo {info_torneo.loc['nombre']}:**__",
                                    description="", color=0x00ff00)
        for casa in casas:
            torneo_status_embed.add_field(name=f"{casa[1]}  __**{casa[0]}**__: {places_dict.get(info_torneo[casa[4]], ':zero:')}", value=f"Puntos: {str(int(info_torneo[casa[2]]))}, participantes: {str(int(info_torneo[casa[3]]))}", inline=False)
            for idx, categoria in enumerate(categorias):
                list = ""
                for team, team_info in teams.loc[(teams["torneo"] == torneo) & (teams["categoria"] == categoria) & (teams["casa"] == casa[0])].iterrows():
                    list += f"{status_dict_2[team_info['DD']]} {status_dict_2[team_info['DF']]} {status_dict_2[team_info['CL']]} {places_dict.get(team_info['lugar'], ':black_large_square:')} {team_info.loc['nombre'].title() if len(team_info.loc['nombre']) < 12 else team_info.loc['nombre'][:10].title()}\n"
                if list == "":
                    list = "."
                torneo_status_embed.add_field(name=f"__**{categoria}:**__ \n", value=list, inline=True)

        await message_edit.edit(embed = torneo_status_embed)

    message_ids.to_csv("message_ids.csv", index = True)
    #print("torneos post done")


@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})\n'
    )
    print('Guild Members:')
    for member in guild.members:
        print(member.name.encode('utf-8'))


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    mensaje = message.content
    #print("\n\n", message.channel, "-", message.author, ":", mensaje)


    if str(message.channel) == "📖activacion":
        await message.delete()
        id = int(message.content)

        with open('DataBase.xlsx', 'rb') as file :
            players = pd.read_excel(file, sheet_name='players', index_col=0, header=0).fillna(0)
            teams   = pd.read_excel(file, sheet_name='equipos', index_col=0, header=0).fillna(0)

        if id in players.index:
            player = players.loc[id]

            await message_status(message.author, player, teams)
            print("status sent")

            member = message.author
            await update_player(member, player)

            discord_id_df = pd.DataFrame(pd.read_csv("discord_ids.csv", index_col = 0, header = 0, squeeze = True))
            discord_id_df.loc[id] = member.id
            discord_id_df.to_csv("discord_ids.csv", index = True)

        else:
            # No id found
            await message.channel.send("El id " + str(id) + " no existe", delete_after=5)
            print("El id " + str(id) + " no existe")

    if str(message.channel) == "chat-coh" and message.content == '!update':
        with open('DataBase.xlsx', 'rb') as file :
            players = pd.read_excel(file, sheet_name='players', index_col=0, header=0)
        discord_ids = pd.DataFrame(pd.read_csv("discord_ids.csv", index_col = 0, header = 0, squeeze = True))

        await message.channel.send("Procesando...")
        for id, discord_id in discord_ids.iterrows():
            print(id)
            player = players.loc[id]
            member = message.guild.get_member(int(discord_id[0]))
            await update_player(member,player)
        await message.channel.send("Terminado")

    if mensaje == '!status':
        if not isinstance(message.channel, discord.channel.DMChannel):
            await message.delete()

        with open('DataBase.xlsx', 'rb') as file :
            players = pd.read_excel(file, sheet_name='players', index_col=0, header=0).fillna(0)
            teams = pd.read_excel(file, sheet_name='equipos', index_col=0, header=0).fillna(0)
        discord_ids = pd.DataFrame(pd.read_csv("discord_ids.csv", index_col = 1, header = 0, squeeze = True))

        id = discord_ids.loc[message.author.id, "id"]
        player = players.loc[id]

        await message_status(message.author, player, teams)
        print("status sent")

    if message.content == "!test":
        await message.delete()


casas = [   ("Red Team",":red_circle:", "norm_red", "part_red", "rank_red"),
            ("Blue Team", ":blue_circle:", "norm_blue", "part_blue", "rank_blue"),
            ("Yellow Team", ":yellow_circle:", "norm_yellow", "part_yellow", "rank_yellow"),
            ("Mendigo", ":white_circle:", "norm_mendigo", "part_mendigo", "rank_mendigo")]
categorias = ["Monster", "Sumo", "Rover"]
status_dict = {1: ":green_square:", 0: ":red_square:", -1: ":red_square:", " ": ":red_square:"}
status_dict_2 = {1: ":green_square:", 0: ":black_large_square:", -1: ":black_large_square:", " ": ":black_large_square:"}
places_dict = {1: ":first_place:", 2: ":second_place:", 3: ":third_place:"}
rango_dict = {"Blanco": ":white_large_square:", "Verde": ":green_square:", "Morado": ":purple_square:", "Rojo": ":red_square:", "Negro": ":white_square_button:"}

update_status_torneo.start()
client.run(TOKEN)
