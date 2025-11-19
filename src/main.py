import pygame
import sys
import random
from config import *
from player import Player, SWORDSMAN_DASH_END, AUGMENT_READY
from enemy import Enemy
from weapon import Weapon
from skill_effects import Projectile, AreaAttackEffect
from boss import Boss, STAGE_CLEAR
from utils import load_image

# --- 초기화 ---
pygame.init()
try:
    font_path = "src/assets/fonts/Pretendard-Light.otf"
    TITLE_FONT = pygame.font.Font(font_path, 74)
    DESC_FONT = pygame.font.Font(font_path, 36)
    STATS_FONT = pygame.font.Font(font_path, 28)
except FileNotFoundError:
    print(f"'{font_path}' 폰트를 찾을 수 없습니다. 기본 폰트로 대체합니다.")
    TITLE_FONT = pygame.font.Font(None, 80)
    DESC_FONT = pygame.font.Font(None, 40)
    STATS_FONT = pygame.font.Font(None, 32)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("김준우 게임")

# --- UI 및 그리기 함수 ---

class Button:
    def __init__(self, text, x, y, width, height, color, hover_color, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.action = action
        self.is_hovered = False

    def draw(self, surface, font=DESC_FONT):
        draw_color = self.hover_color if self.is_hovered else self.color
        text_surf = font.render(self.text, True, BLACK)
        
        # 텍스트 크기에 맞춰 버튼 크기 동적 조절
        self.rect.width = max(self.rect.width, text_surf.get_width() + 40)
        self.rect.height = max(self.rect.height, text_surf.get_height() + 20)

        pygame.draw.rect(surface, draw_color, self.rect, border_radius=10)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            if self.action:
                return self.action
        return None

def draw_text(text, font, color, surface, x, y, center=False):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)

def draw_hud(surface, player, current_stage_index, kill_count, is_boss_spawned, enemies):
    stage_name = STAGES[current_stage_index]['name']
    if is_boss_spawned:
        stage_text = f"Stage: {stage_name} - BOSS"
    else:
        stage_text = f"Stage: {stage_name} ({kill_count} / 100)"
    draw_text(stage_text, DESC_FONT, WHITE, surface, SCREEN_WIDTH / 2, 30, center=True)

    # 보스 체력 바 그리기
    if is_boss_spawned:
        boss = next((enemy for enemy in enemies if isinstance(enemy, Boss)), None)
        if boss:
            boss_bar_width = SCREEN_WIDTH * 0.6
            boss_bar_height = 20
            boss_bar_x = (SCREEN_WIDTH - boss_bar_width) / 2
            boss_bar_y = 60 # 스테이지 텍스트 아래

            boss_health_ratio = boss.hp / boss.max_hp
            
            # 배경
            bg_rect = pygame.Rect(boss_bar_x, boss_bar_y, boss_bar_width, boss_bar_height)
            pygame.draw.rect(surface, GRAY, bg_rect)
            
            # 체력
            fill_rect = pygame.Rect(boss_bar_x, boss_bar_y, boss_bar_width * boss_health_ratio, boss_bar_height)
            pygame.draw.rect(surface, PURPLE, fill_rect)
            
            # 테두리
            pygame.draw.rect(surface, WHITE, bg_rect, 2)
            
            # 보스 이름
            boss_name_text = f"{boss.stats['name']}"
            draw_text(boss_name_text, STATS_FONT, WHITE, surface, SCREEN_WIDTH / 2, boss_bar_y + boss_bar_height + 15, center=True)

    bar_length, bar_height = 400, 30
    hp_x, hp_y = 10, 10
    current_hp = max(0, player.hp)
    fill_ratio = current_hp / player.max_hp
    bg_rect = pygame.Rect(hp_x, hp_y, bar_length, bar_height)
    fill_rect = pygame.Rect(hp_x, hp_y, bar_length * fill_ratio, bar_height)
    pygame.draw.rect(surface, GRAY, bg_rect)
    pygame.draw.rect(surface, GREEN, fill_rect)
    pygame.draw.rect(surface, WHITE, bg_rect, 2)
    hp_text = f"HP: {int(current_hp)} / {int(player.max_hp)}"
    draw_text(hp_text, STATS_FONT, WHITE, surface, hp_x + bar_length + 10, hp_y)

    exp_y = hp_y + bar_height + 5
    exp_bar_height = bar_height - 10
    exp_ratio = player.exp / player.exp_to_next_level
    exp_bg_rect = pygame.Rect(hp_x, exp_y, bar_length, exp_bar_height)
    exp_fill_rect = pygame.Rect(hp_x, exp_y, bar_length * exp_ratio, exp_bar_height)
    pygame.draw.rect(surface, GRAY, exp_bg_rect)
    pygame.draw.rect(surface, BLUE, exp_fill_rect)
    pygame.draw.rect(surface, WHITE, exp_bg_rect, 2)
    exp_text = f"EXP: {int(player.exp)} / {int(player.exp_to_next_level)}"
    draw_text(exp_text, STATS_FONT, WHITE, surface, hp_x + bar_length + 10, exp_y)

    level_text = f"Level: {player.level}"
    draw_text(level_text, DESC_FONT, WHITE, surface, hp_x, exp_y + exp_bar_height + 5)

    # --- 조준 및 발사 모드 표시 (레벨 아래 중앙) ---
    if player.aim_mode == 'auto_target':
        mode_text = "Aim: Auto Target"
    else: # manual_aim
        manual_mode_text = player.manual_fire_mode.replace('_', ' ').replace('fire', '').capitalize()
        mode_text = f"Aim: Manual ({manual_mode_text.strip()})"
    draw_text(mode_text, STATS_FONT, WHITE, surface, SCREEN_WIDTH / 2, exp_y + exp_bar_height + 15, center=True)
    
    # 대쉬 HUD
    if player.dash_charges > 0:
        dash_text = f"Dashes: {player.dash_charges}"
        dash_color = WHITE
    else: # 대쉬 0개일 때 쿨다운 표시
        now = pygame.time.get_ticks()
        time_since_recharge_start = now - player.last_dash_recharge_start_time
        remaining_cd = (player.dash_charge_time - time_since_recharge_start) / 1000
        remaining_cd = max(0, remaining_cd)
        dash_text = f"Dash CD: {remaining_cd:.1f}s"
        dash_color = GRAY
    draw_text(dash_text, DESC_FONT, dash_color, surface, SCREEN_WIDTH - 200, 10)
    
    # 스킬 HUD
    now = pygame.time.get_ticks()
    time_since_skill = now - player.last_skill_time
    if player.is_skill_active:
        remaining_cd = (player.skill_cooldown - time_since_skill) / 1000
        skill_text = f"Skill: {remaining_cd:.1f}s"
        skill_color = GREEN
    elif time_since_skill < player.skill_cooldown:
        remaining_cd = (player.skill_cooldown - time_since_skill) / 1000
        skill_text = f"Skill: {remaining_cd:.1f}s"
        skill_color = GRAY
    else:
        skill_text = "Skill: Ready"
        skill_color = GREEN
    draw_text(skill_text, DESC_FONT, skill_color, surface, SCREEN_WIDTH - 200, 50)


# --- 게임 상태 관리 ---

def character_selection_screen():
    buttons = [Button(CHARACTERS[key]["name"], 150, 200 + i * 80, 250, 60, LIGHT_GRAY, WHITE, key) for i, key in enumerate(CHARACTERS.keys())]
    hovered_character_key = None
    while True:
        mouse_pos = pygame.mouse.get_pos()
        hovered_character_key = next((btn.action for btn in buttons if btn.rect.collidepoint(mouse_pos)), None)

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                return None
            for btn in buttons:
                result = btn.handle_event(event)
                if result: return result

        screen.fill(BLACK)
        draw_text("캐릭터 선택", TITLE_FONT, WHITE, screen, SCREEN_WIDTH / 2, 100, center=True)
        for btn in buttons:
            btn.is_hovered = btn.rect.collidepoint(mouse_pos)
            btn.draw(screen)
        if hovered_character_key:
            char_info = CHARACTERS[hovered_character_key]
            info_x, info_y = 500, 250
            draw_text(f"이름: {char_info['name']}", DESC_FONT, WHITE, screen, info_x, info_y)
            draw_text(f"체력: {char_info['hp']}", STATS_FONT, WHITE, screen, info_x, info_y + 60)
            draw_text(f"공격력: {char_info['attack_power']}", STATS_FONT, WHITE, screen, info_x, info_y + 100)
            draw_text(f"공격 속도: {char_info['attack_speed']}초", STATS_FONT, WHITE, screen, info_x, info_y + 140)
            draw_text(f"이동 속도: {char_info['move_speed']}", STATS_FONT, WHITE, screen, info_x, info_y + 180)
            draw_text(f"특징: {char_info['description']}", STATS_FONT, WHITE, screen, info_x, info_y + 240)
            draw_text(char_info['skill_text'], STATS_FONT, GREEN, screen, info_x, info_y + 280)
        pygame.display.flip()
        pygame.time.Clock().tick(FPS)

def augment_selection_screen(player):
    available_augments = list(AUGMENTS.keys())
    chosen_augment_keys = random.sample(available_augments, 3)

    augment_buttons = []
    button_width, button_height = 400, 150
    start_x = (SCREEN_WIDTH - button_width) / 2
    start_y = (SCREEN_HEIGHT - (button_height * 3 + 20 * 2)) / 2

    for i, key in enumerate(chosen_augment_keys):
        augment = AUGMENTS[key]
        button_text = f"{augment['name']}: {augment['description']}"
        button = Button(button_text, start_x, start_y + i * (button_height + 20), button_width, button_height, LIGHT_GRAY, WHITE, key)
        augment_buttons.append(button)

    selecting = True
    while selecting:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            for btn in augment_buttons:
                result = btn.handle_event(event)
                if result:
                    player.apply_augment(result)
                    selecting = False
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        draw_text("증강 선택", TITLE_FONT, WHITE, screen, SCREEN_WIDTH / 2, 150, center=True)
        for btn in augment_buttons:
            btn.is_hovered = btn.rect.collidepoint(mouse_pos)
            btn.draw(screen)
        pygame.display.flip()
        pygame.time.Clock().tick(FPS)

def view_augments_screen(player):
    back_button = Button("돌아가기", SCREEN_WIDTH / 2 - 100, SCREEN_HEIGHT - 100, 200, 50, LIGHT_GRAY, WHITE, "back")
    
    viewing = True
    while viewing:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit_game"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                viewing = False
            if back_button.handle_event(event):
                viewing = False

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))

        draw_text("획득한 증강", TITLE_FONT, WHITE, screen, SCREEN_WIDTH / 2, 100, center=True)
        
        if not player.chosen_augments:
            draw_text("아직 획득한 증강이 없습니다.", DESC_FONT, WHITE, screen, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, center=True)
        else:
            for i, augment_key in enumerate(player.chosen_augments):
                augment = AUGMENTS[augment_key]
                augment_text = f"- {augment['name']}: {augment['description']}"
                draw_text(augment_text, STATS_FONT, WHITE, screen, 300, 200 + i * 50)

        back_button.is_hovered = back_button.rect.collidepoint(mouse_pos)
        back_button.draw(screen)
        pygame.display.flip()
        pygame.time.Clock().tick(FPS)
    return "pause"

def confirmation_dialog(message):
    dialog_width, dialog_height = 700, 300
    dialog_x = (SCREEN_WIDTH - dialog_width) / 2
    dialog_y = (SCREEN_HEIGHT - dialog_height) / 2
    dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)

    yes_button = Button("예", dialog_x + 150, dialog_y + 180, 150, 60, LIGHT_GRAY, WHITE, "yes")
    no_button = Button("아니오", dialog_x + 400, dialog_y + 180, 150, 60, LIGHT_GRAY, WHITE, "no")
    buttons = [yes_button, no_button]

    confirming = True
    while confirming:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False # Escape는 취소

            for btn in buttons:
                result = btn.handle_event(event)
                if result == "yes":
                    return True
                elif result == "no":
                    return False

        # 뒷 배경을 어둡게 처리
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))
        
        # 다이얼로그 박스 그리기
        pygame.draw.rect(screen, BLACK, dialog_rect, border_radius=15)
        pygame.draw.rect(screen, WHITE, dialog_rect, 3, border_radius=15)

        # 메시지를 줄바꿈하여 표시
        lines = message.split('\n')
        for i, line in enumerate(lines):
            draw_text(line, DESC_FONT, WHITE, screen, SCREEN_WIDTH / 2, dialog_y + 80 + i * 45, center=True)

        for btn in buttons:
            btn.is_hovered = btn.rect.collidepoint(mouse_pos)
            btn.draw(screen)

        pygame.display.flip()
        pygame.time.Clock().tick(FPS)

def pause_menu(player):
    paused = True
    menu_options = {
        "continue": "계속하기",
        "view_augments": "증강 보기",
        "change_character": "캐릭터 바꾸기",
        "exit_game": "게임 종료하기"
    }
    
    buttons = []
    button_y = 300
    for action, text in menu_options.items():
        button = Button(text, SCREEN_WIDTH / 2 - 150, button_y, 300, 60, LIGHT_GRAY, WHITE, action)
        buttons.append(button)
        button_y += 80

    while paused:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit_game"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "continue"
            
            for btn in buttons:
                result = btn.handle_event(event)
                if result == "continue":
                    return "continue"
                elif result == "exit_game":
                    return "exit_game"
                elif result == "change_character":
                    warning_message = "캐릭터를 바꾸면 처음부터 시작해야 합니다.\n정말 진행하시겠습니까?"
                    if confirmation_dialog(warning_message):
                        return "change_character"
                elif result == "view_augments":
                    # 증강 보기 화면에서 "exit_game"이 반환될 수 있음
                    if view_augments_screen(player) == "exit_game":
                        return "exit_game"

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        draw_text("일시정지", TITLE_FONT, WHITE, screen, SCREEN_WIDTH / 2, 150, center=True)
        for btn in buttons:
            btn.is_hovered = btn.rect.collidepoint(mouse_pos)
            btn.draw(screen)
        pygame.display.flip()
        pygame.time.Clock().tick(FPS)

from items import Coin
from coin_system import handle_enemy_death_drops, update_coin_collection, draw_coin_hud

# ... (기존 코드) ...

def shop_screen(player):
    """보스 클리어 후 아이템을 구매할 수 있는 상점 화면"""
    shopping = True
    
    # --- 상점 아이템 생성 ---
    shop_item_keys = random.sample(list(SHOP_ITEMS.keys()), 3)
    shop_items = []
    for key in shop_item_keys:
        item_info = SHOP_ITEMS[key]
        value = random.randint(*item_info["value_range"])
        price = int(value * item_info["price_multiplier"])
        
        item = {
            "key": key,
            "name": item_info["name"],
            "type": item_info["type"],
            "stat": item_info["stat"],
            "icon": item_info["icon"],
            "value": value,
            "price": price,
            "description": ""
        }

        if item["type"] == "consumable":
            item["description"] = f"{item['stat']} {item['value']} 즉시 회복"
        elif item["type"] == "temporary_stat_boost":
            duration = item_info["duration"]
            item["description"] = f"{item['stat']} +{item['value']} ({duration}레벨 동안)"
            item["duration"] = duration

        shop_items.append(item)

    # --- UI 버튼 생성 ---
    exit_button = Button("나가기", SCREEN_WIDTH / 2 - 100, SCREEN_HEIGHT - 120, 200, 60, LIGHT_GRAY, WHITE, "exit")
    item_buttons = []
    button_x = 250
    for i, item in enumerate(shop_items):
        button = Button(f"구매 ({item['price']} C)", button_x + i * 500, 650, 250, 60, GREEN, WHITE, item["key"])
        item_buttons.append(button)

    while shopping:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "exit_game"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: shopping = False
            if exit_button.handle_event(event) == "exit": shopping = False

            for i, btn in enumerate(item_buttons):
                if btn.handle_event(event):
                    item_to_buy = shop_items[i]
                    if player.coins >= item_to_buy["price"]:
                        player.coins -= item_to_buy["price"]
                        print(f"{item_to_buy['name']}을(를) 구매했습니다!")

                        # 아이템 효과 적용
                        if item_to_buy["type"] == "consumable":
                            if item_to_buy["stat"] == "hp":
                                player.hp = min(player.max_hp, player.hp + item_to_buy["value"])
                            elif item_to_buy["stat"] == "exp":
                                player.gain_exp(item_to_buy["value"])
                        
                        elif item_to_buy["type"] == "temporary_stat_boost":
                            stat = item_to_buy["stat"]
                            amount = item_to_buy["value"]
                            duration = item_to_buy["duration"]
                            
                            # 기존 버프가 있으면 중첩 (만료 레벨은 새로 갱신)
                            if stat in player.temporary_boosts:
                                # 기존 버프 제거
                                old_amount = player.temporary_boosts[stat]["amount"]
                                setattr(player, stat, getattr(player, stat) - old_amount)
                                
                            # 새 버프 적용
                            setattr(player, stat, getattr(player, stat) + amount)
                            player.temporary_boosts[stat] = {
                                "amount": amount,
                                "expire_level": player.level + duration
                            }

                        # 구매 후 버튼 비활성화 또는 제거
                        shop_items.pop(i)
                        item_buttons.pop(i)
                        break # 버튼 리스트가 변경되었으므로 루프 탈출
                    else:
                        print("코인이 부족합니다!")


        # --- 화면 그리기 ---
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))

        draw_text("상점", TITLE_FONT, WHITE, screen, SCREEN_WIDTH / 2, 100, center=True)
        
        merchant_icon = load_image("src/assets/images/merchant.png", scale=(150, 150))
        screen.blit(merchant_icon, (SCREEN_WIDTH / 2 - 75, 180))

        # 아이템 정보 표시
        item_x = 380
        for item in shop_items:
            icon_path = f"src/assets/images/{item['icon']}"
            icon = load_image(icon_path, scale=(80, 80))
            screen.blit(icon, (item_x - 40, 420))
            
            draw_text(item["name"], DESC_FONT, WHITE, screen, item_x, 520, center=True)
            draw_text(item["description"], STATS_FONT, GREEN, screen, item_x, 570, center=True)
            item_x += 500

        # 버튼 그리기
        exit_button.is_hovered = exit_button.rect.collidepoint(mouse_pos)
        exit_button.draw(screen)
        for btn in item_buttons:
            btn.is_hovered = btn.rect.collidepoint(mouse_pos)
            btn.draw(screen)
        
        draw_coin_hud(screen, player)
        pygame.display.flip()
        pygame.time.Clock().tick(FPS)
    
    return "continue"


def game_over_screen(player, final_kill_count, final_level):
    game_over = True
    
    retry_button = Button("다시 시작", SCREEN_WIDTH / 2 - 150, SCREEN_HEIGHT / 2 + 50, 300, 60, LIGHT_GRAY, WHITE, "retry")
    quit_button = Button("게임 종료", SCREEN_WIDTH / 2 - 150, SCREEN_HEIGHT / 2 + 130, 300, 60, LIGHT_GRAY, WHITE, "exit_game")
    buttons = [retry_button, quit_button]

    while game_over:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit_game"
            
            for btn in buttons:
                result = btn.handle_event(event)
                if result:
                    return result

        screen.fill(BLACK)
        draw_text("GAME OVER", TITLE_FONT, RED, screen, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100, center=True)
        draw_text(f"최종 레벨: {final_level}", DESC_FONT, WHITE, screen, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20, center=True)
        draw_text(f"처치 수: {final_kill_count}", DESC_FONT, WHITE, screen, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 20, center=True)

        for btn in buttons:
            btn.is_hovered = btn.rect.collidepoint(mouse_pos)
            btn.draw(screen)

        pygame.display.flip()
        pygame.time.Clock().tick(FPS)


def game_play_loop(selected_character_key):
    all_sprites, enemies, weapons = pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group()
    all_coins = pygame.sprite.Group()
    player = Player(selected_character_key)
    all_sprites.add(player)
    all_projectiles = pygame.sprite.Group()
    all_skill_effects = pygame.sprite.Group()

    current_stage_index = 0
    stage_level = 1
    kill_count = 0
    is_boss_spawned = False
    spawn_interval = 1000

    ADD_ENEMY = pygame.USEREVENT + 1
    pygame.time.set_timer(ADD_ENEMY, spawn_interval)

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return "exit_game"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    action = pause_menu(player)
                    if action == "exit_game": return "exit_game"
                    if action == "change_character": return "change_character"
                if event.key == pygame.K_SPACE: player.dash(mouse_pos=mouse_pos)
                if event.key == pygame.K_q:
                    new_projectiles, new_skill_effects = player.activate_skill(enemies=enemies, mouse_pos=mouse_pos)
                    all_projectiles.add(new_projectiles)
                    all_sprites.add(new_projectiles, new_skill_effects)
                if event.key == pygame.K_TAB: player.switch_aim_mode()
                if event.key == pygame.K_f and player.aim_mode == 'manual_aim': player.switch_manual_fire_mode()
            
            if event.type == ADD_ENEMY and not is_boss_spawned:
                enemy_key = random.choice(STAGES[current_stage_index]["enemies"])
                new_enemy = Enemy(enemy_key, player, stage_level)
                enemies.add(new_enemy)
                all_sprites.add(new_enemy)
            
            if event.type == SWORDSMAN_DASH_END:
                area_effect = AreaAttackEffect(event.dict['pos'].x, event.dict['pos'].y, 100, event.dict['skill_damage'], 200)
                all_skill_effects.add(area_effect)
                all_sprites.add(area_effect)
            
            if event.type == AUGMENT_READY:
                augment_selection_screen(event.player)
            
            if event.type == STAGE_CLEAR:
                handle_enemy_death_drops(event.dict['boss'], all_sprites, all_coins)
                
                # 상점 화면 호출
                shop_action = shop_screen(player)
                if shop_action == "exit_game":
                    return "exit_game"

                player.level_up()
                current_stage_index = (current_stage_index + 1) % len(STAGES)
                stage_level += 1
                kill_count = 0
                is_boss_spawned = False
                for enemy in enemies: enemy.kill()
                spawn_interval = max(200, 1000 - (stage_level - 1) * 100)
                pygame.time.set_timer(ADD_ENEMY, 0)
                pygame.time.set_timer(ADD_ENEMY, int(spawn_interval))

        # --- 공격 로직 ---
        now = pygame.time.get_ticks()
        can_attack = now - player.last_attack_time > player.attack_speed * 1000
        fire_request, target_pos, use_nearest_enemy = False, None, False

        if player.aim_mode == 'auto_target':
            fire_request, use_nearest_enemy = True, True
        elif player.aim_mode == 'manual_aim' and (player.manual_fire_mode == 'cursor_auto_fire' or pygame.mouse.get_pressed()[0]):
            fire_request, target_pos = True, mouse_pos

        if fire_request and can_attack:
            player.last_attack_time = now
            target = enemies if use_nearest_enemy else target_pos
            if target:
                new_weapon = Weapon(player, target_pos=target_pos, enemies=enemies if use_nearest_enemy else None)
                weapons.add(new_weapon)
                all_sprites.add(new_weapon)

        # --- 업데이트 ---
        all_sprites.update()
        all_coins.update()

        # --- 충돌 처리 ---
        # 무기-적 충돌
        hits = pygame.sprite.groupcollide(weapons, enemies, True, False)
        for weapon, hit_enemies_list in hits.items():
            primary_target = hit_enemies_list[0]
            enemies_to_damage = [primary_target]
            if player.splash_radius > 0:
                splash_rect = pygame.Rect(0, 0, player.splash_radius * 2, player.splash_radius * 2)
                splash_rect.center = primary_target.rect.center
                enemies_to_damage = [enemy for enemy in enemies if splash_rect.colliderect(enemy.rect)]
            
            for enemy in enemies_to_damage:
                exp_gain = enemy.take_damage(player.attack_power)
                if exp_gain > 0:
                    player.gain_exp(exp_gain)
                    kill_count += 1
                    handle_enemy_death_drops(enemy, all_sprites, all_coins) # 코인 드랍

        # 투사체-적 충돌
        projectile_hits = pygame.sprite.groupcollide(all_projectiles, enemies, True, False)
        for projectile, hit_enemies_list in projectile_hits.items():
            for enemy in hit_enemies_list:
                exp_gain = enemy.take_damage(projectile.damage)
                if exp_gain > 0:
                    player.gain_exp(exp_gain)
                    kill_count += 1
                    handle_enemy_death_drops(enemy, all_sprites, all_coins) # 코인 드랍
        
        # 스킬-적 충돌
        skill_effect_hits = pygame.sprite.groupcollide(all_skill_effects, enemies, False, False)
        for skill_effect, hit_enemies_list in skill_effect_hits.items():
            if isinstance(skill_effect, AreaAttackEffect) and not skill_effect.has_damaged:
                for enemy in hit_enemies_list:
                    exp_gain = enemy.take_damage(skill_effect.damage)
                    if exp_gain > 0:
                        player.gain_exp(exp_gain)
                        kill_count += 1
                        handle_enemy_death_drops(enemy, all_sprites, all_coins) # 코인 드랍
                skill_effect.has_damaged = True

        # 플레이어-코인 충돌
        update_coin_collection(player, all_coins)

        # 플레이어-적 충돌
        if not player.is_invincible:
            # 1. 일반 적과의 충돌 처리
            normal_enemies_group = pygame.sprite.Group([e for e in enemies if not isinstance(e, Boss)])
            if pygame.sprite.spritecollide(player, normal_enemies_group, False):
                collided_enemy = pygame.sprite.spritecollide(player, normal_enemies_group, False)[0]
                player.take_damage(collided_enemy.attack_power)
                collided_enemy.kill()

            # 2. 보스와의 충돌 처리
            boss_group = pygame.sprite.Group([e for e in enemies if isinstance(e, Boss)])
            if pygame.sprite.spritecollide(player, boss_group, False):
                boss = boss_group.sprites()[0]
                player.take_damage(boss.attack_power)
                boss.take_damage(10) # 보스 반사 데미지
                direction = (player.pos - boss.pos).normalize() if (player.pos - boss.pos).length() > 0 else pygame.math.Vector2(0, -1)
                player.pos += direction * 150
                player.rect.center = player.pos
                player.is_invincible = True
                player.dash_start_time = pygame.time.get_ticks()

        if player.hp <= 0: return game_over_screen(player, kill_count, player.level)

        if kill_count >= 100 and not is_boss_spawned:
            is_boss_spawned = True
            boss = Boss(STAGES[current_stage_index]["boss"], player, stage_level)
            enemies.add(boss)
            all_sprites.add(boss)

        # --- 그리기 ---
        screen.fill(BLACK)
        all_sprites.draw(screen)
        for enemy in enemies:
            if not isinstance(enemy, Boss): enemy.draw_health_bar(screen)
        draw_hud(screen, player, current_stage_index, kill_count, is_boss_spawned, enemies)
        draw_coin_hud(screen, player)
        pygame.display.flip()
        pygame.time.Clock().tick(FPS)
    
    return "continue"


def main():
    while True:
        selected_character = character_selection_screen()
        if not selected_character:
            break # 게임 완전 종료
        
        action = game_play_loop(selected_character)
        if action == "exit_game":
            break # 게임 완전 종료
        elif action == "retry":
            # game_play_loop will be called again with the same selected_character
            continue 
        elif action == "change_character":
            # character_selection_screen will be called again
            continue

if __name__ == '__main__':
    main()
    pygame.quit()
    sys.exit()