import discord
from discord.ext import commands
import requests
import random

intents = discord.Intents.default()
intents.message_content = True  # Pour le contenu des messages
intents.members = True  # Pour les informations sur les membres du serveur

bot = commands.Bot(command_prefix='!', intents=intents)

# Fonction pour rechercher des informations sur une carte MTG via l'API Scryfall
def fetch_card_info(card_name):

    while True:
        url = f"https://api.scryfall.com/cards/search?q={card_name}"
        response = requests.get(url)
        if response.status_code == 200:
            json_data = response.json()
            if 'data' in json_data:
                first_card = json_data['data'][0]
                card_info = {
                    'name': first_card.get('name', 'Inconnu'),
                    'set': first_card.get('set_name', 'Inconnu'),
                    'type': first_card.get('type_line', 'Inconnu'),
                    'oracle_text': first_card.get('oracle_text', 'Inconnu'),
                    'image_url': first_card.get('image_uris', {}).get('small', 'Pas d\'image disponible')
                }
                return card_info
    return None

# Fonction pour obtenir une carte MTG aléatoire via l'API Scryfall
def fetch_random_card():
    url = "https://api.scryfall.com/cards/search?q=rarity:rare+OR+rarity:mythic"
    response = requests.get(url)
    if response.status_code == 200:
        json_data = response.json()
        total_cards = json_data.get('total_cards', 0)
        if total_cards > 0:
            random_index = random.randint(0, total_cards - 1)
            page = random_index // 175 + 1  # Scryfall renvoie jusqu'à 175 cartes par page
            position_on_page = random_index % 175

            url = f"https://api.scryfall.com/cards/search?q=rarity:rare+OR+rarity:mythic&page={page}"
            response = requests.get(url)
            if response.status_code == 200:
                json_data = response.json()
                if 'data' in json_data:
                    card = json_data['data'][position_on_page]
                    card_info = {
                        'name': card.get('name', 'Inconnu'),
                        'type_line': card.get('type_line', 'Inconnu'),
                        'mana_cost': card.get('mana_cost', 'Inconnu'),
                        'oracle_text': card.get('oracle_text', 'Inconnu'),
                        'colors': card.get('colors', []),
                        'cmc': card.get('cmc', 0),
                        'rarity': card.get('rarity', 'Inconnu'),
                        'image_url': card.get('image_uris', {}).get('art_crop', 'Pas d\'image disponible')
                    }
                    return card_info
    return None




# Convertit les abréviations de couleur en noms complets
def full_color_name(abbr):
    color_dict = {'W': 'Blanc', 'U': 'Bleu', 'B': 'Noir', 'R': 'Rouge', 'G': 'Vert'}
    return [color_dict.get(c, c) for c in abbr]

# Récupère les informations d'une carte par son nom
def fetch_card_by_name(card_name):
    url = f"https://api.scryfall.com/cards/search?q={card_name}"
    response = requests.get(url)
    if response.status_code == 200:
        json_data = response.json()
        if 'data' in json_data:
            card = json_data['data'][0]
            card_info = {
                'name': card.get('name', 'Inconnu'),
                'type_line': card.get('type_line', 'Inconnu'),
                'colors': card.get('colors', []),
                'cmc': card.get('cmc', 0),
                'rarity': card.get('rarity', 'Inconnu')
            }
            return card_info
    return None



# Événement pour indiquer que le bot est prêt
@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user.name} ({bot.user.id})')

# Commande pour afficher des informations sur une carte MTG
@bot.command()
async def card(ctx, *, card_name):
    card_info = fetch_card_info(card_name)
    if card_info:
        embed = discord.Embed(title=card_info['name'], description=f"Set: {card_info['set']}\nType: {card_info['type']}")
        embed.add_field(name="Oracle Text", value=card_info['oracle_text'], inline=False)
        embed.set_thumbnail(url=card_info['image_url'])
        await ctx.send(embed=embed)
    else:
        await ctx.send(f'Désolé, je n\'ai pas pu trouver d\'informations sur la carte "{card_name}".')


# Commande pour démarrer un jeu de devinette de carte
@bot.command()
async def guess(ctx):
    card_info = fetch_random_card()
    if card_info:
        await ctx.send("Devinez le nom de cette carte:")
        await ctx.send(
            f"Type: {card_info.get('type_line', 'Inconnu')}\nCoût de mana: {card_info.get('mana_cost', 'Inconnu')}\nTexte Oracle: {card_info.get('oracle_text', 'Inconnu')}")

        def check(m):
            return m.channel == ctx.channel and m.content.lower() == card_info['name'].lower()

        try:
            guess = await bot.wait_for('message', timeout=30.0, check=check)
        except TimeoutError:
            await ctx.send(f'Temps écoulé! La bonne réponse était {card_info["name"]}.')
        else:
            await ctx.send(f'Bien joué {guess.author.mention}! La bonne réponse était {card_info["name"]}.')
    else:
        await ctx.send("Je n'ai pas pu trouver une carte aléatoire. Essayez encore.")

@bot.command()
async def guess_creature(ctx):
    target_card = fetch_random_card()  # Supposons que cette fonction existe déjà
    if target_card and 'Creature' in target_card['type_line']:
        await ctx.send("Envoyez le nom d'une créature, et je vous dirai comment elle se compare à la créature cible.")

        def check(m):
            return m.channel == ctx.channel

        while True:
            try:
                guess = await bot.wait_for('message', timeout=60.0, check=check)
                guessed_card = fetch_card_by_name(guess.content)

                if guessed_card:
                    if guessed_card['colors'] == target_card['colors']:
                        color_hint = "La couleur est correcte."
                    else:
                        color_hint = f"La couleur n'est pas bonne"

                    if guessed_card['cmc'] == target_card['cmc']:
                        cmc_hint = "Le coût en mana est correct."
                    elif guessed_card['cmc'] < target_card['cmc']:
                        cmc_hint = "Le coût en mana est trop bas."
                    else:
                        cmc_hint = "Le coût en mana est trop élevé."

                    if guessed_card['rarity'] == target_card['rarity']:
                        rarity_hint = "La rareté est correcte."
                    else:
                        rarity_hint = f"La rareté devrait être {target_card['rarity']}."

                    await ctx.send(f"{color_hint}\n{cmc_hint}\n{rarity_hint}")

                else:
                    await ctx.send("Je n'ai pas pu trouver cette carte. Essayez un autre nom.")

            except TimeoutError:
                await ctx.send(f'Temps écoulé! La bonne réponse était {target_card["name"]}.')
                break

    else:
        await ctx.send("Je n'ai pas pu trouver une créature aléatoire. Essayez encore.")


@bot.command()
async def multiple_choice(ctx):
    target_card = fetch_random_card()  # Supposons que cette fonction existe déjà
    if target_card and 'Creature' in target_card['type_line']:
        # Obtenir trois autres cartes aléatoires pour les choix
        other_choices = [fetch_random_card()['name'] for _ in range(3)]
        choices = other_choices + [target_card['name']]
        random.shuffle(choices)

        choice_text = "\n".join([f"{idx + 1}. {choice}" for idx, choice in enumerate(choices)])

        await ctx.send("Devinez le nom de cette créature:")
        image_url = target_card.get('image_url', 'URL d\'image non disponible')
        image_msg = await ctx.send(image_url)
        choices_msg = await ctx.send(f"Choix :\n{choice_text}")

        for emoji in ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]:
            await choices_msg.add_reaction(emoji)

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]

        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
            user_choice = choices[int(reaction.emoji[0]) - 1]

            if user_choice == target_card['name']:
                await ctx.send(f'Bien joué {ctx.author.mention}! La bonne réponse était {target_card["name"]}.')
            else:
                await ctx.send(f'Dommage! La bonne réponse était {target_card["name"]}.')

        except TimeoutError:
            await ctx.send(f'Temps écoulé! La bonne réponse était {target_card["name"]}.')
    else:
        await ctx.send("Je n'ai pas pu trouver une créature aléatoire. Essayez encore.")


# @bot.command()
# async def help(ctx):
#     embed = discord.Embed(title="Aide du Bot MTG", description="Liste des commandes disponibles :", color=0x00ff00)
#
#     embed.add_field(name="!card [nom de la carte]", value="Affiche des informations sur une carte MTG spécifique.", inline=False)
#     embed.add_field(name="!guess", value="Démarre un jeu de devinette où vous devez deviner le nom d'une carte MTG.", inline=False)
#     embed.add_field(name="!guess_creature", value="Démarre un jeu où vous devez deviner une créature en comparant ses attributs.", inline=False)
#     embed.add_field(name="!multiple_choice", value="Démarre un jeu à choix multiples où vous devez deviner le nom d'une créature.", inline=False)
#
#     await ctx.send(embed=embed)


# Remplacez 'YOUR_BOT_TOKEN' par le token de votre bot
bot.run('TOKENHERE')
