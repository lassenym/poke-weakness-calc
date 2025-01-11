import sqlite3, os

RESET = "\033[0m"
ORANGE = "\033[38;5;214m"
RED = "\033[91m"
GREEN = "\033[92m"
BLUE = "\033[34m"

def db_connect():
    conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), "poke.db"))
    return conn, conn.cursor()

def levenshtein_distance(s1, s2):
    dp = [[0 for _ in range(len(s2) + 1)] for _ in range(len(s1) + 1)]

    for i in range(len(s1) + 1):
        dp[i][0] = i
    for j in range(len(s2) + 1):
        dp[0][j] = j

    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],
                    dp[i][j - 1],
                    dp[i - 1][j - 1]
                )

    return dp[-1][-1]

def get_typechart():
    conn, cursor =  db_connect()

    cursor.execute('''
    SELECT atk.name AS attacker, def.name AS defender, e.multiplier
    FROM effectiveness e
    JOIN types atk ON e.attacker_type_id = atk.id
    JOIN types def ON e.defender_type_id = def.id
    ''')
    
    rows = cursor.fetchall()
    type_chart = {}

    for attacker, defender, multiplier in rows:
        if attacker not in type_chart:
            type_chart[attacker] = {}
        type_chart[attacker][defender] = multiplier
    
    conn.commit()
    conn.close()    
    return type_chart

def get_all_types():
    conn, cursor =  db_connect()

    types = [row[0] for row in cursor.execute("SELECT name FROM types").fetchall()]

    conn.commit()
    conn.close()
    return types

def get_all_pokemon():
    conn, cursor =  db_connect()

    pokemon = [row[0] for row in cursor.execute("SELECT name FROM pokemon").fetchall()]

    conn.commit()
    conn.close()
    return pokemon

def get_poketype(pokename):
    
    conn, cursor =  db_connect()
    
    if not cursor.execute("SELECT type1, type2 FROM pokemon WHERE name = ?", (pokename,)).fetchall():
        return None

    types = cursor.execute("SELECT type1, type2 FROM pokemon WHERE name = ?", (pokename,)).fetchall()[0]
    
    conn.commit()
    conn.close()
    return types

def get_multiplier(types):

    type_chart = get_typechart()
    new_chart = {}

    if types[1]:
        for type in get_all_types():

            if type in type_chart[types[0]] and type in type_chart[types[1]]:
                new_chart[type] = type_chart[types[0]][type] * type_chart[types[1]][type]
            elif type in type_chart[types[0]]:
                new_chart[type] = type_chart[types[0]][type]
            elif type in type_chart[types[1]]:
                new_chart[type] = type_chart[types[1]][type]
            else:
                new_chart[type] = 1.0
    else:

        for type in get_all_types():

            if type in type_chart[types[0]]:
                new_chart[type] = type_chart[types[0]][type]
            else:
                new_chart[type] = 1.0
    
    return new_chart

def print_types(type_chart):
    sorted_dict = dict(sorted(type_chart.items(), key=lambda item: item[1]))
    for type in sorted_dict:
        if sorted_dict[type] < 1.0:
            print(f"{BLUE}x{sorted_dict[type]}{RESET} {RED}{type}{RESET}")
        elif sorted_dict[type] == 1.0:
            print(f"{BLUE}x{sorted_dict[type]}{RESET} {ORANGE}{type}{RESET}")
        else:
            print(f"{BLUE}x{sorted_dict[type]}{RESET} {GREEN}{type}{RESET}")

def suggest_pokemon_name(mistyped_name):

    closest_match = None
    min_distance = float('inf')

    for pokemon in get_all_pokemon():
        distance = levenshtein_distance(mistyped_name, pokemon)
        if distance < min_distance:
            min_distance = distance
            closest_match = pokemon

    return closest_match

if __name__ == "__main__":

    print(f"{BLUE}WELCOME TO THE POKE-WEAKNESS CALC!{RESET}")
    print("Enter the name of a Pokemon you are fighting against to see what type of attack you should use!")
    print(f"(Enter {BLUE}quit{RESET} or {BLUE}exit{RESET} to leave the application.)\n")

    while True:

        pokemon = input().lower()
        if pokemon == "exit" or pokemon == "quit":
            exit()
        elif pokemon not in get_all_pokemon():
            print(f"{RED}Pokemon unknown.{RESET} Did you mean {BLUE}{suggest_pokemon_name(pokemon)}{RESET}?")
        else:
            print(f"\n======{pokemon.upper()}======\n")
            print_types(get_multiplier(get_poketype(pokemon)))
            print(f"\n{"="*len(pokemon)}===========\n")