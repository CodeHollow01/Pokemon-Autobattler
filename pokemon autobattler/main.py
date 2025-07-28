import pygame
import sys
import random
import os
import math
import pandas as pd
from openpyxl import load_workbook

pygame.init()

# Configuração da Janela
WIDTH = 1280 # Largura
HEIGHT = 720 # Altura
screen = pygame.display.set_mode((WIDTH, HEIGHT)) # Cria uma janela para o jogo e retorna uma Surface que será atribuída a "screen"
pygame.display.set_caption("Pokémon Battles") # Cria o título da janela

font = pygame.font.Font(None, 36) # Cria um objeto Fonte(fonte, tamanho) || None retorna a fonte padrão
clock = pygame.time.Clock() # Cria um objeto Clock() para o jogo para determinar o fps
speed_list = [-4, -3.5, -3, -2.5, -2, 2, 2.5, 3, 3.5, 4] # Variações de velocidade após uma colisão
variation = [0.85, 0.9, 0.92, 0.94, 1, 1.06, 1.08, 1.1, 1.15] # Variações de ângulos de ataque na mira
sprite_size = (90, 90) # Tamanho fixo dos sprites dos pokémon

# Extrai a imagem "arena.png" da pasta "images"
bg_folder = os.path.dirname(__file__) 
bg_path = os.path.join(bg_folder, "images", "arena.png")
bg_original = pygame.image.load(bg_path).convert_alpha()
bg_image = pygame.transform.scale(bg_original, (WIDTH, HEIGHT))


# Pokémon disponíveis
pokemon_list = [ #Nome // Move Timer Max // Move Timer // HPMAX // HP // ATK // SPA
    ["charmander", 295, 295,     100, 100,      12, 2, "flametrower"],
    ["squirtle",   300, 300,     105, 105,      10, 30, "whirlpool"],
    ["bulbasaur",  250, 250,     90, 90,        8, 25, "energy_ball"]
    
]
results = [] # Guarda todos os resultados das partidas
rounds = 100 # Número de rounds da simulação
effects = [] # Lista de efeitos a serem renderizados
bg_effects = [] # Lista de efeitos de background a serem renderizados
pokemons = [] # Lista dos pokémon em campo(max: 2)
mons_draw = [] # Lista que guarda os nomes dos pokémon para importá-los para o Excel
floating_texts = [] # Lista de textos a serem renderizados
timer = 0 # Tempo decorrido das partidas em ticks || 1 tick = 1/60s a 60 fps
timerReload = 0 # Tempo em ticks de espera após o término de uma partida para iniciar a próxima
endround = False # Variável que define se o round já acabou ou não


# Reseta a posição inicial da batalha
def reset_game():
    global pokemons, effects, bg_effects, floating_texts, timer, timerReload, endround, pokemon_list, mons_draw

    pokemon_list = ([  # Reinserir os pokémon disponíveis
        ["charmander", 295, 295,     100, 100,      12, 2, "flametrower"],
        ["squirtle",   300, 300,     105, 105,      10, 30, "whirlpool"],
        ["bulbasaur",  250, 250,     90, 90,        8, 25, "energy_ball"]
    ])
    
    pokemons = []
    mons_draw = []
    effects = []
    bg_effects = []
    floating_texts = []
    timer = 0
    timerReload = 0
    endround = False
    

    for x in [100, 1180]:
        pokemon_info = random.choice(pokemon_list)
        pokemon_list.remove(pokemon_info)
        
        name = pokemon_info[0]
        movetimermax = pokemon_info[1]
        movetimer = pokemon_info[2]
        hpmax = pokemon_info[3]
        hp = pokemon_info[4]
        atk = pokemon_info[5]
        spa = pokemon_info[6]
        move = pokemon_info[7]

        pokemons.append(
            Pokemon(
                x=x,
                y=HEIGHT // 2,
                vel_x=random.choice(speed_list),
                vel_y=random.choice(speed_list),
                name=name,
                movetimermax=movetimermax,
                movetimer=movetimer,
                hpmax=hpmax,
                hp=hp,
                atk=atk,
                spa=spa,
                move=move
            )
        )
        mons_draw.append(name)

# Define os comportamentos dos objetos "Pokemon"
class Pokemon:
    def __init__(self, x, y, vel_x, vel_y, name, movetimermax, movetimer, hpmax, hp, atk, spa, move):
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.name = name
        self.movetimermax = movetimermax
        self.movetimer = movetimer
        self.hpmax = hpmax
        self.hp = hp
        self.atk = atk
        self.spa = spa
        self.move = move
        self.oponent = None

        self.flamethrower_active = False
        self.flamethrower_ticks = 0
        self.flamethrower_amount = 0

        self.taken_whirlpool = False
        self.invframe_whirlpool = 0

        base_path = os.path.dirname(__file__)
        image_path = os.path.join(base_path, "images", f"{name}.png")

        original_image = pygame.image.load(image_path).convert_alpha()
        redimensioned_image = pygame.transform.smoothscale(original_image, sprite_size)

        self.normal_sprite = redimensioned_image
        self.mirrored_sprite = pygame.transform.flip(redimensioned_image, True, False)

        self.sprite = self.normal_sprite
        self.rect = self.sprite.get_rect(center=(x, y))

    #Listagem de golpes possíveis
    def flametrower(self):
        if len(pokemons) > 1 and not self.flamethrower_active:
            self.flamethrower_active = True
            self.flamethrower_ticks = 0
            self.flamethrower_amount = 15

    def energy_ball(self):
        if len(pokemons) > 1:
            result = find_enemy(self)
            dir_x = result[0]
            dir_y = result[1]

            effects.append(Energy_Ball(screen, (0,255,0), 200, dir_x, dir_y, 20, (self.rect.centerx, self.rect.centery), self, self.spa))
        
    def whirlpool(self):
        bg_effects.append(Whirlpool(screen, (0, 255, 255), (self.rect.centerx, self.rect.centery), 60, 20, self, self.spa))


    def psybeam(self):
        pass
    def thunderbolt(self):
        pass
    def mach_punch(self):
        pass
    def metal_sound(self):
        pass
    def brutal_swing(self):
        pass
    def draco_meteor(self):
        pass
    def cut(self):
        pass

    functions = {
        "flametrower": flametrower, # charmander
        "energy_ball": energy_ball, # bulbasaur
        "whirlpool": whirlpool, # squirtle
        "psybeam": psybeam, # gothita
        "thunderbolt": thunderbolt, # mareep
        "mach_punch": mach_punch, # timburr
        "metal_sound": metal_sound, # magnemite
        "brutal_swing": brutal_swing, # sandile
        "draco_meteor": draco_meteor, # gible
        "cut": cut # porygon
    } 

    #Função de update
    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # Rebater nas bordas
        if self.rect.left < 0:
            self.rect.left = 0
            self.vel_x *= -1
            self.vel_y = random.choice(speed_list)
        elif self.rect.right > WIDTH:
            self.rect.right = WIDTH
            self.vel_x *= -1
            self.vel_y = random.choice(speed_list)

        if self.rect.top < 0:
            self.rect.top = 0
            self.vel_y *= -1
            self.vel_x = random.choice(speed_list)
        elif self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT
            self.vel_y *= -1
            self.vel_x = random.choice(speed_list)
        
        if self.flamethrower_active:
            self.flamethrower_ticks += 1

            # Solta um projétil a cada 3 ticks
            if self.flamethrower_ticks % 3 == 0 and self.flamethrower_amount > 0:
                result = find_enemy(self)
                if result:
                    dir_x, dir_y = result

                    effects.append(Flametrower(
                        screen,
                        (255, 165 - random.randint(1, 30), 0),
                        80,
                        dir_x,
                        dir_y,
                        (self.rect.centerx, self.rect.centery),
                        self,
                        self.spa,
                        255,
                        32
                    ))

                    self.flamethrower_amount -= 1

                    if self.flamethrower_amount == 0:
                        self.flamethrower_active = False

        if self.oponent == None:
            for p in pokemons:
                if p != self:
                    self.oponent = p.name
            

        if self.taken_whirlpool == True:
            self.invframe_whirlpool -= 1
            if self.invframe_whirlpool <= 0:
                self.taken_whirlpool = False



        self.movetimer -= 1
        if (self.movetimer <= 0):
            self.movetimer = self.movetimermax
            self.functions[self.move](self)

    def draw(self, surface):
        surface.blit(self.sprite, self.rect)

        x = self.rect.centerx - self.rect.width // 2
        y = self.rect.top - 15
        w = self.rect.width
        h = 10  
        

        proportionhp = self.hp / self.hpmax
        bar = int(w * proportionhp)

        
        pygame.draw.rect(surface, (255, 0, 0), (x, y, w, h))
        pygame.draw.rect(surface, (0, 255, 0), (x, y, bar, h))

    #Função de espelhar imagem
    def turn(self):
        if self.vel_x > 0:
            self.sprite = self.mirrored_sprite
        else:
            self.sprite = self.normal_sprite

# Define os comportamentos dos textos flutuantes com base no ID recebido || id: 0 -> flutua pra cima, id: 1 -> estático
class FloatingText: 
    def __init__(self, text, pos, cor=(255, 0, 0), time=60, size=32, id=0):
        self.text = text
        self.pos = list(pos)  # [x, y]
        self.cor = cor
        self.time = time  # frames de duração
        self.size = size
        self.alpha = 255
        self.id = id

        self.font = pygame.font.SysFont(None, self.size)
        self.surface = self.font.render(self.text, True, self.cor)
        self.surface.set_alpha(self.alpha)

    def update(self):
        if self.id == 0:
            self.pos[1] -= 1  # sobe
            self.alpha = max(0, self.alpha - (255 / self.time))
            self.time -= 1
            self.surface.set_alpha(self.alpha)
        elif self.id == 2:
            self.time -= 1



    def draw(self, surface):
        surface.blit(self.surface, self.pos)


    def end(self):
        return self.time <= 0

# Define os comportamentos de "Bola e energia" para os pokémon de grama
class Energy_Ball: 
    def __init__(self, surface, color, lifetime, dir_x, dir_y, radius, pos, owner, damage):
        self.surface = surface
        self.color = color
        self.lifetime = lifetime
        self.lifetime_max = lifetime
        self.dir_x = dir_x
        self.dir_y = dir_y
        self.radius = radius
        self.pos = list(pos)
        self.owner = owner
        self.damage = damage

    def update(self):
        self.lifetime -= 1

        denominator = math.sqrt((self.dir_x ** 2) + (self.dir_y ** 2))
        magnitude = 7.3

        self.speed_x = self.dir_x / denominator
        self.speed_y = self.dir_y / denominator

        self.pos[0] += self.speed_x * magnitude
        self.pos[1] += self.speed_y * magnitude

    def colides_with_pokemon(self, pokemon):
        # Distância entre o centro da bola e o centro do Pokémon
        dx = self.pos[0] - pokemon.rect.centerx
        dy = self.pos[1] - pokemon.rect.centery
        distance = math.hypot(dx, dy)

        return distance < self.radius + max(pokemon.rect.width, pokemon.rect.height) / 2

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius)

    def end(self):
        return self.lifetime <= 0

# Define os comportamentos de "Lança chamas" para os pokémon de fogo
class Flametrower:
    def __init__(self, surface, color, lifetime, dir_x, dir_y, pos, owner, damage, alpha, size):
        self.surface = surface
        self.color = color
        self.lifetime = lifetime
        self.dir_x = dir_x
        self.dir_y = dir_y

        self.pos = list(pos)
        self.owner = owner
        self.damage = damage
        self.alpha = alpha
        self.size = size

    def update(self):

        self.alpha = max(0, self.alpha - (230 / self.lifetime))
        self.lifetime -= 1

        denominator = math.sqrt((self.dir_x ** 2) + (self.dir_y ** 2))
        magnitude = 7.5

        self.speed_x = self.dir_x / denominator
        self.speed_y = self.dir_y / denominator

        self.pos[0] += self.speed_x * magnitude
        self.pos[1] += self.speed_y * magnitude

    def colides_with_pokemon(self, pokemon):
        # Distância entre o centro da bola e o centro do Pokémon
        dx = self.pos[0] - pokemon.rect.centerx
        dy = self.pos[1] - pokemon.rect.centery
        distance = math.hypot(dx, dy)

        return distance < (self.size / 2) + max(pokemon.rect.width, pokemon.rect.height) / 2

    def draw(self, screen):
        temp_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        temp_surface.set_alpha(int(self.alpha))

        pygame.draw.rect(temp_surface, self.color, (0, 0, self.size, self.size))

        x = self.pos[0] - self.size / 2
        y = self.pos[1] - self.size / 2
        self.surface.blit(temp_surface, (x, y))

    def end(self):
        return self.alpha <= 0 

# Define os comportamentos de "ondas" para os pokémon de água 
class Whirlpool:
    def __init__(self, surface, color, pos, lifetime, radius, owner, damage):
        self.surface = surface
        self.color = color
        self.pos = list(pos)
        self.lifetime = lifetime
        self.radius = radius
        self.owner = owner
        self.damage = damage

    def update(self):
        if self.owner not in pokemons:
            bg_effects.remove(self)
            return

        self.radius += 3.5
        self.lifetime -= 1

        for p in pokemons:
            if p == self.owner:
                self.pos[0] = p.rect.centerx
                self.pos[1] = p.rect.centery

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius, 3)
        pygame.draw.circle(surface, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius / 1.3, 3)
        pygame.draw.circle(surface, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius / 2, 3)

    def colides_with_pokemon(self, pokemon):
        dx = self.pos[0] - pokemon.rect.centerx
        dy = self.pos[1] - pokemon.rect.centery
        distance = math.hypot(dx, dy)

        return distance < self.radius + max(pokemon.rect.width, pokemon.rect.height) / 2


    def end(self):
        return self.lifetime <= 0

# Adiciona o resultado "new_data" para uma nova linha na planilha "results.xlxs"
def add_excel_result(new_data, file_name="results.xlsx"):
    folder_dir = os.path.dirname(os.path.abspath(__file__))
    file_access = os.path.join(folder_dir, "data", file_name)

    new_df = pd.DataFrame([new_data])

    if os.path.exists(file_access):
        existing_df = pd.read_excel(file_access)  # Lê o conteúdo real
        startrow = len(existing_df) + 1  # Começa a escrever na próxima linha
        with pd.ExcelWriter(file_access, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            new_df.to_excel(writer, index=False, header=False, startrow=startrow)
    else:
        # Cria novo arquivo com cabeçalho
        new_df.to_excel(file_access, index=False, engine='openpyxl')

# Encontra a posição(x,y) do pokémon adversário
def find_enemy(self):
    if len(pokemons) > 1:
        for p in pokemons:
            if p != self:
                enemy = p
        alvo_x = enemy.rect.centerx
        alvo_y = enemy.rect.centery
        
        dir_x = (alvo_x - self.rect.centerx) * random.choice(variation)
        dir_y = (alvo_y - self.rect.centery) * random.choice(variation)

        return dir_x, dir_y
    else:
        return False

# Reconstrói a sala inicial e sai do jogo caso os rounds acabem
def rebuild_game():
    global rounds, results
    rounds -= 1
    if rounds > 0:
        main()
    else:
        if len(results) > 0:
            for i in range(len(results)):
                add_excel_result(results[i])
            pygame.quit()
            sys.exit()

# Função Principal
def main():
    running = True # Variável de loop
    global timer, timerReload, endround, pokemons, effects, bg_effects, floating_texts, results, rounds, bg_image # Importa as variáveis de fora da função
    reset_game() # Reinicia o campo de batalha

    text = f"Remaining Rounds: {rounds}"
    text_width, _ = font.size(text)
    floating_texts.append(FloatingText(text, (WIDTH - text_width, 20), (255, 255, 255), 60, 32, 1))

    while running: # Loop Principal
        clock.tick(60) # Fps nativo do programa
        if endround == False:
            timer += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Adiciona o fundo importado
        screen.blit(bg_image, (0, 0))

        segundos = timer // 60
        minutos = segundos // 60
        segundos_restantes = segundos % 60
        text = f"Time: {minutos} m {segundos_restantes} s"
        text_width, _ = font.size(text)
        has_time = False
        for text_unit in floating_texts:
            if text_unit.id == 2:
                has_time = True
        if has_time == False:
            floating_texts.append(FloatingText(text, (20, 20), (255, 255, 255), 1, 32, 2))


        # Verificar colisões entre pokémon e pokémon
        for i in range(len(pokemons)):
            for j in range(i + 1, len(pokemons)):
                p1 = pokemons[i]
                p2 = pokemons[j]

                if p1.rect.colliderect(p2.rect):
                    # Calcula a sobreposição em X e Y
                    dx = (p1.rect.centerx - p2.rect.centerx)
                    dy = (p1.rect.centery - p2.rect.centery)

                    # Decide se a colisão é mais horizontal ou vertical
                    if abs(dx) > abs(dy):
                        # Colisão horizontal → inverter vel_x
                        p1.vel_x *= -1
                        p2.vel_x *= -1

                        p1.hp -= p2.atk
                        p2.hp -= p1.atk

                        floating_texts.append(FloatingText(f"- {p2.atk}", (p1.rect.centerx, p1.rect.top),(255,0,0),60,32,0))
                        floating_texts.append(FloatingText(f"- {p1.atk}", (p2.rect.centerx, p2.rect.top),(255,0,0),60,32,0))

                        # Corrige a sobreposição (ajuste simples)
                        if dx > 0:
                            p1.rect.left = p2.rect.right
                            p2.rect.right = p1.rect.left
                        else:
                            p1.rect.right = p2.rect.left
                            p2.rect.left = p1.rect.right
                    else:
                        # Colisão vertical → inverter vel_y
                        p1.vel_y *= -1
                        p2.vel_y *= -1

                        p1.hp -= p2.atk
                        p2.hp -= p1.atk

                        floating_texts.append(FloatingText(f"- {p2.atk}", (p1.rect.centerx, p1.rect.top),(255,0,0),60,32,0))
                        floating_texts.append(FloatingText(f"- {p1.atk}", (p2.rect.centerx, p2.rect.top),(255,0,0),60,32,0))

                        # Corrige a sobreposição (ajuste simples)
                        if dy > 0:
                            p1.rect.top = p2.rect.bottom
                            p2.rect.bottom = p1.rect.top
                        else:
                            p1.rect.bottom = p2.rect.top
                            p2.rect.top = p1.rect.bottom

        # Verifica a colisão entre os efeitos de background e os pokémon
        for effect in bg_effects[:]:
            effect.update()
            effect.draw(screen)
            for p in pokemons:
                if effect.colides_with_pokemon(p) and p != effect.owner:
                    if p.taken_whirlpool == False:
                        floating_texts.append(FloatingText(f"- {effect.damage}", (p.rect.centerx, p.rect.top),(255,0,0),60,32,0))

                    if not isinstance(effect, Whirlpool):
                        p.hp -= effect.damage  
                    else:
                        if p.taken_whirlpool == False:
                            p.hp -= effect.damage
                            p.invframe_whirlpool = effect.lifetime + (effect.lifetime / 2) # margem de erro
                            p.taken_whirlpool = True
                            
                    bg_effects.remove(effect)
                    break  # já removido, não precisa testar mais pokémon

            if effect.end() and effect in bg_effects:
                bg_effects.remove(effect)

        # Atualiza os pokémon
        for p in pokemons[:]:  # <- cópia da lista
            p.update()
            p.turn()
            p.draw(screen)

            if p.hp <= 0:
                pokemons.remove(p)

        # Verifica a colisão entre os efeitos de foreground e os pokémon
        for effect in effects[:]:
            effect.update()
            effect.draw(screen)

            for p in pokemons:
                if effect.colides_with_pokemon(p) and p != effect.owner:
                    if not isinstance(effect, Whirlpool):
                        p.hp -= effect.damage  
                    else:
                        if p.taken_whirlpool == False:
                            p.hp -= effect.damage
                            p.invframe_whirlpool = effect.lifetime
                            p.taken_whirlpool = True
                            
                            
                    floating_texts.append(FloatingText(f"- {effect.damage}", (p.rect.centerx, p.rect.top),(255,0,0),60,32,0))
                    if not isinstance(effect, Whirlpool):
                        effects.remove(effect)
                        break  # já removido, não precisa testar mais pokémon

            if effect.end() and effect in effects:
                effects.remove(effect)

        # Atualiza os textos
        for text in floating_texts[:]:
            text.update()
            text.draw(screen)
            if text.end():
                floating_texts.remove(text)
        
        # Caso a partida tenha sido encerrada(com vencedor e perdedor)
        if len(pokemons) == 1:
            if endround == False:
                result = {
                    "pokemon_1": pokemons[0].name,
                    "pokemon_2": pokemons[0].oponent,
                    "Winner": pokemons[0].name,
                    "Loser": pokemons[0].oponent,
                    "Tick Time": timer
                }
                results.append(result)
            text = font.render(f"{pokemons[0].name} wins!", True, (255,255,255))
            screen.blit(text, (100, 100))
            endround = True
            timerReload += 1
            if timerReload >= 180:
                rebuild_game()

        # Caso a partida tenha sido encerrada(empate)
        elif len(pokemons) == 0:
            if endround == False:
                result = {
                    "pokemon_1": mons_draw[0],
                    "pokemon_2": mons_draw[1],
                    "Winner": "None",
                    "Lost": "None",
                    "Tick time": timer
                }
                results.append(result)
            text = font.render("Draw", True, (255,255,255))
            screen.blit(text, (100, 100))
            endround = True
            timerReload += 1
            if timerReload >= 180:
                rebuild_game()
                
        pygame.display.flip()

    # Adiciona todos os resultados das partidas para o Excel
    if len(results) > 0:
        for i in range(len(results)):
            add_excel_result(results[i])


    pygame.quit()
    sys.exit()

# Verifica se está executando o arquivo "main"
if __name__ == "__main__":
    main()